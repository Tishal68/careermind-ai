"""Database-backed queue for the supported single-instance deployment."""
import logging
import secrets
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException
from sqlalchemy import update, delete
from sqlalchemy.exc import IntegrityError
from app.core.database import SessionLocal
from app.models.research import ResearchJob, ResearchSlot, ResearchLease, ResearchSubmission
from app.models.report import CareerReport
from app.models.session import ResumeSession
from app.models.user import User
from app.schemas import ResearchRequest
from app.services.job_research import research

logger = logging.getLogger(__name__)
_capacity = threading.BoundedSemaphore(2)

def now():
    return datetime.now(timezone.utc).replace(tzinfo=None)

def expired(job):
    return (now() - job.created_at.replace(tzinfo=None)).total_seconds() > 600

def release_slot(db, job):
    db.execute(update(ResearchSlot).where(ResearchSlot.user_id == job.user_id, ResearchSlot.job_id == job.id).values(job_id=None))

def maintain_queue(db):
    for job in db.query(ResearchJob).filter(ResearchJob.status.in_(["pending", "running"])).all():
        base = update(ResearchJob).where(ResearchJob.id == job.id, ResearchJob.status == job.status)
        if expired(job):
            changed = db.execute(base.values(status="failed", error="Research timed out. Please retry.", request_data={})).rowcount
            if changed: release_slot(db, job)
        elif job.status == "running":
            lease = db.get(ResearchLease, job.id)
            if lease:
                # Lock/revoke only an expired lease before changing job state.
                changed = db.execute(update(ResearchLease).where(ResearchLease.job_id == job.id, ResearchLease.expires_at < now()).values(token="expired")).rowcount
                if not changed: continue
            if lease and lease.attempts >= 2:
                changed = db.execute(base.values(status="failed", error="Research was interrupted twice. Please retry.", request_data={})).rowcount
                if changed: release_slot(db, job)
            else:
                db.execute(base.values(status="pending"))
    # Retain completed report data, but discard old execution metadata.
    old = [row.id for row in db.query(ResearchJob.id).filter(ResearchJob.status.in_(["completed", "failed"]), ResearchJob.created_at < now() - timedelta(days=30)).limit(500)]
    if old:
        db.execute(delete(ResearchSubmission).where(ResearchSubmission.job_id.in_(old)))
        db.execute(delete(ResearchLease).where(ResearchLease.job_id.in_(old)))
        db.execute(delete(ResearchJob).where(ResearchJob.id.in_(old)))
    db.commit()

def claim(db, job_id, token):
    job = db.get(ResearchJob, job_id)
    if not job or job.status != "pending" or expired(job):
        return False
    lease = db.get(ResearchLease, job_id)
    try:
        if lease:
            changed = db.execute(update(ResearchLease).where(ResearchLease.job_id == job_id, ResearchLease.expires_at < now(), ResearchLease.attempts < 2).values(token=token, expires_at=now()+timedelta(seconds=90), attempts=ResearchLease.attempts+1)).rowcount
            if not changed:
                db.rollback(); return False
        else:
            db.add(ResearchLease(job_id=job_id, token=token, expires_at=now()+timedelta(seconds=90), attempts=1))
            db.flush()
        changed = db.execute(update(ResearchJob).where(ResearchJob.id == job_id, ResearchJob.status == "pending").values(status="running")).rowcount
        if not changed:
            db.rollback(); return False
        db.commit(); return True
    except IntegrityError:
        db.rollback(); return False

def heartbeat(job_id, token, stop):
    while not stop.wait(25):
        try:
            with SessionLocal() as db:
                changed = db.execute(update(ResearchLease).where(ResearchLease.job_id == job_id, ResearchLease.token == token).values(expires_at=now()+timedelta(seconds=90))).rowcount
                db.commit()
                if not changed: return
        except Exception:
            logger.warning("Research heartbeat unavailable for job %s", job_id)

def run_research(job_id: int):
    if not _capacity.acquire(blocking=False):
        return  # Leave queued; the dispatcher will try later.
    token = secrets.token_hex(16)
    stop = threading.Event()
    try:
        with SessionLocal() as db:
            if not claim(db, job_id, token): return
            threading.Thread(target=heartbeat, args=(job_id, token, stop), daemon=True).start()
            job = db.get(ResearchJob, job_id)
            req = ResearchRequest.model_validate(job.request_data)
            resume = db.query(ResumeSession).filter(ResumeSession.id == req.resume_id, ResumeSession.user_id == job.user_id).first()
            if not resume: raise HTTPException(404, "Resume not found. Upload it again.")
            analysis, gap = research(req, resume.raw_text or "")
            # Fence commits from stale/recovered workers. This update holds the
            # lease row until report creation and job completion commit together.
            owned = db.execute(update(ResearchLease).where(ResearchLease.job_id == job_id, ResearchLease.token == token, ResearchLease.expires_at > now()).values(expires_at=now()+timedelta(seconds=90))).rowcount
            db.refresh(job)
            if not owned or job.status != "running" or expired(job):
                db.rollback(); return
            report = CareerReport(user_id=job.user_id, resume_session_id=resume.id, field="Career research", job_role=req.job_role, experience_level=req.experience_level,
                nex_score=analysis.get("match_percent"), resume_score=None, ats_score=None, readiness_score=None,
                analysis_data=analysis, gap_analysis=gap, roadmap_data={"milestones": []}, project_recommendations=[])
            db.add(report); db.flush()
            user = db.get(User, job.user_id)
            if user: user.target_job_role = req.job_role
            job.report_id, job.status = report.id, "completed"
            job.request_data = {"resume_id": req.resume_id, "job_role": req.job_role}
            release_slot(db, job)
            db.commit()
    except Exception as exc:
        with SessionLocal() as db:
            job, lease = db.get(ResearchJob, job_id), db.get(ResearchLease, job_id)
            if job and lease and lease.token == token and job.status == "running":
                job.status = "failed"
                job.error = str(exc.detail)[:500] if isinstance(exc, HTTPException) else "Research could not finish. Please retry."
                job.request_data = {}
                release_slot(db, job); db.commit()
        if not isinstance(exc, HTTPException): logger.error("Research job %s failed (%s)", job_id, type(exc).__name__)
    finally:
        stop.set(); _capacity.release()

def start_dispatcher():
    stop = threading.Event()
    def loop():
        pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="research")
        futures = {}
        try:
            while not stop.is_set():
                try:
                    futures = {key: future for key, future in futures.items() if not future.done()}
                    with SessionLocal() as db:
                        maintain_queue(db)
                        queued = db.query(ResearchJob.id).filter(ResearchJob.status == "pending").order_by(ResearchJob.created_at, ResearchJob.id).limit(2).all()
                    for (job_id,) in queued:
                        if len(futures) >= 2: break
                        if job_id not in futures: futures[job_id] = pool.submit(run_research, job_id)
                except Exception:
                    logger.warning("Research queue temporarily unavailable")
                stop.wait(2)
        finally:
            pool.shutdown(wait=False, cancel_futures=True)
    thread = threading.Thread(target=loop, daemon=True, name="research-dispatcher")
    thread.start()
    return stop
