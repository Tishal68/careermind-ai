from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.session import ResumeSession
from app.models.report import CareerReport
from app.models.research import ResearchJob
from app.schemas import ResearchRequest
from app.services.job_research import public_url
from app.services.research_worker import run_research, expired
from app.schemas import (
    AnalysisRequest, CareerReportResponse, DashboardOverviewResponse,
    RecentReportSummary, RoadmapResponse, ProjectRecommendation
)
from app.intelligence.career_engine import career_engine
from app.intelligence.career_graph import career_graph
from app.intelligence.learning_engine import learning_engine
from app.intelligence.recommendation_engine import recommendation_engine

router = APIRouter(tags=["Reports & Analytics"])


@router.post("/analysis/research", status_code=202)
def start_research(req: ResearchRequest, background: BackgroundTasks,
                   db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    resume = db.query(ResumeSession).filter(ResumeSession.id == req.resume_id,
                                          ResumeSession.user_id == current_user.id).first()
    if not resume:
        raise HTTPException(404, "Resume not found")
    if req.job_url:
        public_url(req.job_url)
    active = db.query(ResearchJob).filter(ResearchJob.user_id == current_user.id,
                                        ResearchJob.status.in_(["pending", "running"])).all()
    for job in active:
        if not expired(job):
            raise HTTPException(409, "Research is already running. Wait for it to finish.")
        job.status, job.error, job.request_data = "failed", "Research interrupted or timed out. Please retry.", {}
    job = ResearchJob(user_id=current_user.id, request_data=req.model_dump())
    db.add(job)
    db.commit()
    db.refresh(job)
    background.add_task(run_research, job.id)
    return {"id": job.id, "status": "pending"}


@router.get("/analysis/research/{job_id}")
def research_status(job_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    job = db.query(ResearchJob).filter(ResearchJob.id == job_id, ResearchJob.user_id == current_user.id).first()
    if not job:
        raise HTTPException(404, "Research not found")
    if job.status in ("pending", "running") and expired(job):
        job.status, job.error, job.request_data = "failed", "Research interrupted or timed out. Please retry.", {}
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
    if req.job_role.lower() not in career_graph.roles:
        raise HTTPException(status_code=400, detail="Select a supported job role")

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
def get_all_reports(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(CareerReport).filter(CareerReport.user_id == current_user.id).order_by(CareerReport.created_at.desc()).all()


@router.post("/roadmap/generate/{report_id}", response_model=RoadmapResponse)
def generate_roadmap(report_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    report = db.query(CareerReport).filter(CareerReport.id == report_id, CareerReport.user_id == current_user.id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    missing_skills = (report.gap_analysis or {}).get("missing_skills", [])
    milestones = learning_engine.build_learning_path(report.job_role, missing_skills)
    report.roadmap_data = {"milestones": milestones}
    db.commit()
    return RoadmapResponse(report_id=report.id, job_role=report.job_role, total_weeks=len(milestones), milestones=milestones)


@router.get("/projects/recommendations", response_model=List[ProjectRecommendation])
def get_projects(job_role: str = "AI Engineer", experience_level: str = "Mid-Level", current_user: User = Depends(get_current_user)):
    return recommendation_engine.recommend_projects(job_role, experience_level)


@router.get("/dashboard/overview", response_model=DashboardOverviewResponse)
def get_dashboard(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    resumes_count = db.query(ResumeSession).filter(ResumeSession.user_id == current_user.id).count()
    reports_count = db.query(CareerReport).filter(CareerReport.user_id == current_user.id).count()
    latest_report = db.query(CareerReport).filter(CareerReport.user_id == current_user.id).order_by(CareerReport.created_at.desc()).first()
    recent = db.query(CareerReport).filter(CareerReport.user_id == current_user.id).order_by(CareerReport.created_at.desc()).limit(5).all()
    
    return DashboardOverviewResponse(
        ats_score=latest_report.ats_score if latest_report else 82.0,
        resume_score=latest_report.resume_score if latest_report else 80.0,
        readiness_score=latest_report.readiness_score if latest_report else 75.0,
        interview_score=84.5,
        learning_progress_percent=65.0,
        completed_projects_count=2,
        resumes_count=resumes_count,
        reports_count=reports_count,
        recent_reports=[
            RecentReportSummary(
                id=r.id,
                job_role=r.job_role,
                experience_level=r.experience_level,
                ats_score=r.ats_score,
                created_at=r.created_at
            ) for r in recent
        ]
    )
