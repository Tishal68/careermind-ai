import logging
import threading
from datetime import datetime, timezone
from fastapi import HTTPException
from app.core.database import SessionLocal
from app.models.research import ResearchJob
from app.models.report import CareerReport
from app.models.session import ResumeSession
from app.models.user import User
from app.schemas import ResearchRequest
from app.services.job_research import research

logger = logging.getLogger(__name__)
_capacity = threading.BoundedSemaphore(2)


def expired(job):
    created = job.created_at.replace(tzinfo=timezone.utc) if job.created_at.tzinfo is None else job.created_at
    return (datetime.now(timezone.utc) - created).total_seconds() > 600


def run_research(job_id: int):
    with SessionLocal() as db:
        job = db.get(ResearchJob, job_id)
        if not job or job.status != "pending":
            return
        acquired = _capacity.acquire(blocking=False)
        try:
            if not acquired:
                raise HTTPException(503, "Research is busy. Please retry shortly.")
            job.status = "running"
            db.commit()
            req = ResearchRequest.model_validate(job.request_data)
            resume = db.query(ResumeSession).filter(ResumeSession.id == req.resume_id,
                                                    ResumeSession.user_id == job.user_id).first()
            if not resume:
                raise HTTPException(404, "Resume not found. Upload it again.")
            analysis, gap = research(req, resume.raw_text or "")
            db.refresh(job)
            if expired(job) or job.status != "running":
                raise HTTPException(503, "Research expired. Please retry.")
            coverage = analysis.get("match_percent") or 0
            report = CareerReport(user_id=job.user_id, resume_session_id=resume.id, field="Career research",
                                  job_role=req.job_role, experience_level=req.experience_level,
                                  nex_score=coverage, resume_score=0, ats_score=0, readiness_score=0,
                                  analysis_data=analysis, gap_analysis=gap,
                                  roadmap_data={"milestones": []}, project_recommendations=[])
            db.add(report)
            db.flush()
            user = db.get(User, job.user_id)
            if user:
                user.target_job_role = req.job_role
            job.report_id = report.id
            job.status = "completed"
            # Do not retain a second copy of the user-pasted description.
            job.request_data = {"resume_id": req.resume_id, "job_role": req.job_role}
            db.commit()
        except Exception as exc:
            db.rollback()
            job = db.get(ResearchJob, job_id)
            if job:
                job.status = "failed"
                job.error = str(exc.detail)[:500] if isinstance(exc, HTTPException) else "Research could not finish. Please retry."
                job.request_data = {}
                db.commit()
            if not isinstance(exc, HTTPException):
                # No prompts, resume text, provider bodies, or keys in logs.
                logger.error("Research job %s failed (%s)", job_id, type(exc).__name__)
        finally:
            if acquired:
                _capacity.release()
