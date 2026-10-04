from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.session import ResumeSession
from app.models.chat import ChatSession, ChatMessage
from app.schemas import ChatMessageRequest, ChatMessageResponse, ChatHistoryResponse
from app.services import CoachService

router = APIRouter(prefix="/chat", tags=["Chat & AI Coach"])


@router.post("/message", response_model=ChatMessageResponse)
def send_chat(req: ChatMessageRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    latest_resume = db.query(ResumeSession).filter(ResumeSession.user_id == current_user.id).order_by(ResumeSession.created_at.desc()).first()
    
    # Get or auto-create daily chat session
    daily_session = CoachService.get_or_create_daily_session(db, current_user.id, latest_resume.id if latest_resume else None)

    # Save User Message
    user_msg = ChatMessage(chat_session_id=daily_session.id, role="user", content=req.content)
    db.add(user_msg)
    db.commit()

    # Generate Coach Response using persistent memory + LLM provider
    reply_content = CoachService.generate_coach_response(db, current_user.id, req.content, daily_session.id, latest_resume)

    # Save Assistant Message
    assistant_msg = ChatMessage(chat_session_id=daily_session.id, role="assistant", content=reply_content)
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)

    return assistant_msg


@router.get("/history", response_model=ChatHistoryResponse)
def chat_history(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    latest_resume = db.query(ResumeSession).filter(ResumeSession.user_id == current_user.id).order_by(ResumeSession.created_at.desc()).first()
    daily_session = CoachService.get_or_create_daily_session(db, current_user.id, latest_resume.id if latest_resume else None)
    
    msgs = db.query(ChatMessage).filter(ChatMessage.chat_session_id == daily_session.id).order_by(ChatMessage.created_at.asc()).all()
    return ChatHistoryResponse(messages=msgs)


@router.delete("/clear", status_code=204)
def clear_chat(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    latest_resume = db.query(ResumeSession).filter(ResumeSession.user_id == current_user.id).order_by(ResumeSession.created_at.desc()).first()
    if latest_resume:
        db.query(ChatSession).filter(ChatSession.resume_session_id == latest_resume.id).delete()
        db.commit()
    return None
