from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Header, Query
import hashlib
import json
import uuid
from datetime import timedelta
from sqlalchemy import update, text
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.session import ResumeSession
from app.models.report import CareerReport
from app.models.research import ResearchJob, ResearchSlot, ResearchSubmission
from app.schemas import ResearchRequest
from app.services.job_research import public_url
from app.services import action_plans
from app.schemas import ActionTaskUpdate
from app.services.research_worker import expired, release_slot, now
from app.schemas import (
    AnalysisRequest, CareerReportResponse, DashboardOverviewResponse,
    RecentReportSummary, RoadmapResponse, ProjectRecommendation
)
from app.intelligence.career_engine import career_engine
from app.intelligence.career_graph import career_graph

router = APIRouter(tags=["Reports & Analytics"])


@router.post("/analysis/research", status_code=202)
def start_research(req: ResearchRequest, idempotency_key: str = Header(default="", max_length=64),
                   db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    key = idempotency_key or uuid.uuid4().hex
    fingerprint = hashlib.sha256(json.dumps(req.model_dump(), sort_keys=True).encode()).hexdigest()
    try:
        # Lock one account for the whole admission transaction (also serializes
        # SQLite writes). No in-memory lock is needed for duplicate admission.
        if db.get_bind().dialect.name == "postgresql":
            db.execute(text("SELECT pg_advisory_xact_lock(731439)"))
        db.execute(update(User).where(User.id == current_user.id).values(updated_at=User.updated_at))
        previous = db.get(ResearchSubmission, (current_user.id, key))
        if previous:
            if previous.fingerprint != fingerprint: raise HTTPException(409, "This request key was already used with different inputs.")
            job = db.get(ResearchJob, previous.job_id)
            db.commit()
            return {"id": job.id, "status": job.status}
        resume = db.query(ResumeSession).filter(ResumeSession.id == req.resume_id, ResumeSession.user_id == current_user.id).first()
        if not resume: raise HTTPException(404, "Resume not found")
        if req.job_url: public_url(req.job_url)
        active = db.query(ResearchJob).filter(ResearchJob.user_id == current_user.id, ResearchJob.status.in_(["pending", "running"])).all()
        for job in active:
            if not expired(job): raise HTTPException(409, "Research is already running. Wait for it to finish.")
            job.status, job.error, job.request_data = "failed", "Research timed out. Please retry.", {}
            release_slot(db, job)
        recent = db.query(ResearchJob).filter(ResearchJob.user_id == current_user.id, ResearchJob.created_at > now()-timedelta(hours=1)).count()
        if recent >= 12: raise HTTPException(429, "Hourly research limit reached. Try again later.", headers={"Retry-After": "3600"})
        if db.query(ResearchJob).filter(ResearchJob.status.in_(["pending", "running"])).count() >= 100:
            raise HTTPException(503, "Research queue is full. Please retry shortly.", headers={"Retry-After": "60"})
        slot = db.get(ResearchSlot, current_user.id)
        if slot is None:
            slot = ResearchSlot(user_id=current_user.id)
            db.add(slot); db.flush()
        job = ResearchJob(user_id=current_user.id, request_data=req.model_dump())
        db.add(job); db.flush()
        if not db.execute(update(ResearchSlot).where(ResearchSlot.user_id == current_user.id, ResearchSlot.job_id.is_(None)).values(job_id=job.id)).rowcount:
            raise HTTPException(409, "Research is already running. Wait for it to finish.")
        db.add(ResearchSubmission(user_id=current_user.id, request_key=key, fingerprint=fingerprint, job_id=job.id))
        db.commit()
        return {"id": job.id, "status": "pending"}
    except (IntegrityError, OperationalError) as exc:
        db.rollback()
        raise HTTPException(409, "Research admission is busy. Retry the same request shortly.") from exc
    except HTTPException:
        db.rollback(); raise


@router.get("/analysis/research/{job_id}")
def research_status(job_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    job = db.query(ResearchJob).filter(ResearchJob.id == job_id, ResearchJob.user_id == current_user.id).first()
    if not job:
        raise HTTPException(404, "Research not found")
    if job.status in ("pending", "running") and expired(job):
        job.status, job.error, job.request_data = "failed", "Research interrupted or timed out. Please retry.", {}
        release_slot(db, job)
        db.commit()
    report = None
    if job.report_id:
        report = db.query(CareerReport).filter(CareerReport.id == job.report_id,
                                             CareerReport.user_id == current_user.id).first()
    return {"id": job.id, "status": job.status, "error": job.error,
            "report": CareerReportResponse.model_validate(report).model_dump() if report else None}


@router.post("/analysis/analyze", response_model=CareerReportResponse, status_code=201)
def analyze_role(req: AnalysisRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    resume = db.query(ResumeSession).filter(
        ResumeSession.id == req.resume_id, ResumeSession.user_id == current_user.id
    ).first()
    if resume is None:
        raise HTTPException(status_code=404, detail="Resume not found")
    if req.job_role.strip().lower() not in career_graph.roles:
        raise HTTPException(status_code=400, detail="This legacy keyword endpoint only has curated technology profiles. Use /api/v1/analysis/research for any professional role with a job description or market sources.")

    parsed = resume.parsed_data or {}
    skills = list(dict.fromkeys(parsed.get("technical_skills", []) + parsed.get("tools_frameworks", [])))
    evaluation = career_engine.evaluate_candidate(skills, req.job_role, req.experience_level)
    matched = evaluation["matched_skills"]
    missing = evaluation["missing_skills"]
    match_percent = evaluation["match_percent"]
    steps = [
        f"Learn {skill} fundamentals, then build a small project that demonstrates {skill}."
        for skill in missing
    ]
    steps.append(f"Build one portfolio project for {req.job_role} that combines your skills. Document what you built, your decisions, and measurable results.")
    steps.append("Update your resume with evidence from that project, then practice explaining your work in a mock interview.")
    report = CareerReport(
        user_id=current_user.id,
        resume_session_id=resume.id,
        field=req.field,
        job_role=req.job_role,
        experience_level=req.experience_level,
        nex_score=evaluation["nex_score"],
        resume_score=evaluation["resume_score"],
        ats_score=evaluation["ats_score"],
        readiness_score=evaluation["readiness_score"],
        analysis_data={"matched_skills": matched, "match_percent": match_percent,
                       "match_label": "Strong skills match" if match_percent >= 80 else "Partial skills match" if match_percent >= 50 else "Limited skills match"},
        gap_analysis={
            "missing_skills": missing,
            "learning_steps": steps,
            "reasoning": f"Your resume shows {len(matched)} of {len(matched) + len(missing)} core skills for {req.job_role}. This is a skills overlap estimate, not a hiring prediction.",
        },
        roadmap_data={"milestones": []},
        project_recommendations=[],
    )
    current_user.target_job_role = req.job_role
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


@router.get("/analysis/reports", response_model=List[CareerReportResponse])
def get_all_reports(limit: int = Query(20, ge=1, le=50), before: int | None = Query(None, gt=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = db.query(CareerReport).filter(CareerReport.user_id == current_user.id)
    if before: query = query.filter(CareerReport.id < before)
    return query.order_by(CareerReport.id.desc()).limit(limit).all()


@router.get("/analysis/report-summaries")
def report_summaries(limit: int = Query(20, ge=1, le=50), before: int | None = Query(None, gt=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = db.query(CareerReport.id, CareerReport.job_role, CareerReport.experience_level, CareerReport.created_at).filter(CareerReport.user_id == current_user.id)
    if before: query = query.filter(CareerReport.id < before)
    rows = query.order_by(CareerReport.id.desc()).limit(limit+1).all()
    return {"items": [dict(row._mapping) for row in rows[:limit]], "next_before": rows[limit-1].id if len(rows)>limit else None}


@router.get("/analysis/reports/{report_id}", response_model=CareerReportResponse)
def report_detail(report_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    report = db.query(CareerReport).filter(CareerReport.id == report_id, CareerReport.user_id == current_user.id).first()
    if not report: raise HTTPException(404, "Report not found")
    return report


@router.get("/analysis/reports/{report_id}/action-plan")
def read_action_plan(report_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return action_plans.response(action_plans.owned_report(db, current_user.id, report_id))


@router.post("/analysis/reports/{report_id}/action-plan")
def create_action_plan(report_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return action_plans.create_plan(db, current_user.id, report_id)


@router.patch("/analysis/reports/{report_id}/action-plan/tasks/{task_id}")
def update_action_task(report_id: int, task_id: str, change: ActionTaskUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return action_plans.save_task(db, current_user.id, report_id, task_id, change.revision, change.is_completed)


@router.post("/roadmap/generate/{report_id}", response_model=RoadmapResponse)
def generate_roadmap(report_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    plan = action_plans.create_plan(db, current_user.id, report_id)
    return {**plan, "total_weeks": len(plan["milestones"])}


@router.get("/projects/recommendations", response_model=List[ProjectRecommendation])
def get_projects(report_id: int = Query(gt=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    report = action_plans.owned_report(db, current_user.id, report_id)
    return action_plans.build_plan(report)["projects"]


@router.get("/dashboard/overview", response_model=DashboardOverviewResponse)
def get_dashboard(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    resumes_count = db.query(ResumeSession).filter(ResumeSession.user_id == current_user.id).count()
    reports_count = db.query(CareerReport).filter(CareerReport.user_id == current_user.id).count()
    latest_report = db.query(CareerReport).filter(CareerReport.user_id == current_user.id).order_by(CareerReport.created_at.desc()).first()
    recent = db.query(CareerReport).filter(CareerReport.user_id == current_user.id).order_by(CareerReport.created_at.desc()).limit(5).all()
    
    return DashboardOverviewResponse(
        ats_score=None,
        resume_score=None,
        readiness_score=None,
        interview_score=None,
        learning_progress_percent=None,
        completed_projects_count=0,
        resumes_count=resumes_count,
        reports_count=reports_count,
        recent_reports=[
            RecentReportSummary(
                id=r.id,
                job_role=r.job_role,
                experience_level=r.experience_level,
                ats_score=None,
                created_at=r.created_at
            ) for r in recent
        ]
    )
