from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.session import ResumeSession
from app.models.report import CareerReport
from app.schemas import (
    AnalysisRequest, CareerReportResponse, DashboardOverviewResponse,
    RecentReportSummary, RoadmapResponse, ProjectRecommendation
)
from app.intelligence.career_engine import career_engine
from app.intelligence.learning_engine import learning_engine
from app.intelligence.recommendation_engine import recommendation_engine

router = APIRouter(tags=["Reports & Analytics"])


@router.post("/analysis/analyze", response_model=CareerReportResponse, status_code=status.HTTP_201_CREATED)
def run_analysis(req: AnalysisRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = db.query(ResumeSession).filter(ResumeSession.id == req.resume_id, ResumeSession.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Resume session not found")
    
    parsed = session.parsed_data or {}
    skills = parsed.get("technical_skills", [])
    eval_res = career_engine.evaluate_candidate(skills, req.job_role, req.experience_level)

    report = CareerReport(
        user_id=current_user.id,
        resume_session_id=session.id,
        field=req.field,
        job_role=req.job_role,
        experience_level=req.experience_level,
        resume_score=eval_res["resume_score"],
        ats_score=eval_res["ats_score"],
        readiness_score=eval_res["readiness_score"],
        analysis_data={"matched_skills": eval_res["matched_skills"]},
        gap_analysis={"missing_skills": eval_res["missing_skills"]}
    )
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
