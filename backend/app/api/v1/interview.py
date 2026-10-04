from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.session import ResumeSession
from app.models.interview import InterviewSession
from app.schemas import StartInterviewRequest, EvaluateAnswerRequest, AnswerFeedbackResponse, InterviewSessionResponse
from app.services import InterviewService

router = APIRouter(prefix="/interview", tags=["Interview Studio"])


@router.post("/start", response_model=InterviewSessionResponse, status_code=201)
def start_interview(req: StartInterviewRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    latest_resume = db.query(ResumeSession).filter(ResumeSession.user_id == current_user.id).order_by(ResumeSession.created_at.desc()).first()
    q = InterviewService.generate_initial_question(req.interview_type, req.target_role)
    
    session = InterviewSession(
        user_id=current_user.id,
        resume_session_id=latest_resume.id if latest_resume else None,
        interview_type=req.interview_type,
        target_role=req.target_role,
        overall_score=85.0,
        history=[{"question": q, "answer": None, "evaluation": None}]
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.post("/evaluate", response_model=AnswerFeedbackResponse)
def eval_interview(req: EvaluateAnswerRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = db.query(InterviewSession).filter(InterviewSession.id == req.session_id, InterviewSession.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    res = InterviewService.evaluate_response(session.interview_type, session.target_role, req.question, req.user_answer)
    return AnswerFeedbackResponse(
        question=req.question,
        user_answer=req.user_answer,
        score=res.get("score", 85),
        strengths=res.get("strengths", []),
        mistakes=res.get("mistakes", []),
        suggested_answer=res.get("suggested_answer", ""),
        next_question=res.get("next_question")
    )
