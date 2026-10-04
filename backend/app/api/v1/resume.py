import os
import uuid
import shutil
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.session import ResumeSession
from app.models.report import CareerReport
from app.schemas import ResumeResponse, CareerReportResponse
from app.services.parser_service import ResumeParserService
from app.intelligence.command_center import command_center

router = APIRouter(prefix="/resume", tags=["Resume"])
UPLOAD_DIR = "./uploads/resumes"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/auto-pipeline", tags=["NexPath Auto Pipeline"])
async def run_auto_pipeline(
    file: UploadFile = File(...),
    target_role: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".pdf", ".docx", ".doc"]:
        raise HTTPException(status_code=400, detail="Invalid format. Allowed: .pdf, .docx")
    
    session_uuid = str(uuid.uuid4())
    user_dir = os.path.join(UPLOAD_DIR, f"user_{current_user.id}", session_uuid)
    os.makedirs(user_dir, exist_ok=True)
    saved_path = os.path.join(user_dir, file.filename)
    with open(saved_path, "wb") as buf:
        shutil.copyfileobj(file.file, buf)

    raw_text = ResumeParserService.extract_raw_text(saved_path, ext)
    parsed = ResumeParserService.parse_resume_content(raw_text)

    # Create ResumeSession Root Entity
    session_record = ResumeSession(
        user_id=current_user.id,
        session_uuid=session_uuid,
        file_name=file.filename,
        file_type=ext,
        file_path=saved_path,
        raw_text=raw_text,
        parsed_data=parsed,
        is_active=True
    )
    db.add(session_record)
    db.commit()
    db.refresh(session_record)

    job_role = target_role or current_user.target_job_role or "AI Engineer"
    current_user.target_job_role = job_role

    # Route through AI Command Center Orchestrator
    user_name = current_user.full_name or "Candidate"
    pipeline_res = command_center.process_auto_pipeline(db, current_user.id, user_name, job_role, parsed)

    career_eval = pipeline_res["career_evaluation"]
    nex_breakdown = pipeline_res["nex_score_breakdown"]
    roadmap_milestones = pipeline_res["roadmap_milestones"]
    projects = pipeline_res["project_recommendations"]

    report_record = CareerReport(
        user_id=current_user.id,
        resume_session_id=session_record.id,
        field="Software Development",
        job_role=job_role,
        experience_level="Mid-Level",
        nex_score=nex_breakdown["nex_score"],
        nex_score_breakdown=nex_breakdown,
        resume_score=career_eval["resume_score"],
        ats_score=career_eval["ats_score"],
        readiness_score=career_eval["readiness_score"],
        analysis_data={"matched_skills": career_eval["matched_skills"], "strengths": ["Solid baseline skills"]},
        gap_analysis={"missing_skills": career_eval["missing_skills"]},
        roadmap_data={"milestones": roadmap_milestones},
        project_recommendations=projects
    )
    db.add(report_record)
    db.commit()
    db.refresh(report_record)

    return {
        "success": True,
        "message": "NexPath Auto-Pipeline Execution Complete",
        "resume": ResumeResponse.model_validate(session_record),
        "report": CareerReportResponse.model_validate(report_record),
        "nex_score": nex_breakdown,
        "roadmap": roadmap_milestones,
        "projects": projects
    }


@router.post("/upload", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".pdf", ".docx", ".doc"]:
        raise HTTPException(status_code=400, detail="Invalid format. Allowed: .pdf, .docx")
    
    session_uuid = str(uuid.uuid4())
    user_dir = os.path.join(UPLOAD_DIR, f"user_{current_user.id}", session_uuid)
    os.makedirs(user_dir, exist_ok=True)
    saved_path = os.path.join(user_dir, file.filename)
    with open(saved_path, "wb") as buf:
        shutil.copyfileobj(file.file, buf)
        
    raw_text = ResumeParserService.extract_raw_text(saved_path, ext)
    parsed = ResumeParserService.parse_resume_content(raw_text)
    record = ResumeSession(user_id=current_user.id, session_uuid=session_uuid, file_name=file.filename, file_type=ext, file_path=saved_path, raw_text=raw_text, parsed_data=parsed)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.delete("/session/{resume_id}", status_code=204)
def delete_resume_session(resume_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session_record = db.query(ResumeSession).filter(ResumeSession.id == resume_id, ResumeSession.user_id == current_user.id).first()
    if not session_record:
        raise HTTPException(status_code=404, detail="Resume session not found")

    session_dir = os.path.dirname(session_record.file_path)
    if os.path.exists(session_dir):
        try:
            shutil.rmtree(session_dir)
        except Exception:
            pass

    db.delete(session_record)
    db.commit()
    return None


@router.get("/my-resumes", response_model=List[ResumeResponse])
def get_resumes(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(ResumeSession).filter(ResumeSession.user_id == current_user.id).order_by(ResumeSession.created_at.desc()).all()
