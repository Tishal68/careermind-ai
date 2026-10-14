from app.core.request_limits import expensive_request
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.chat import ChatMessage
from app.schemas import ChatMessageRequest, ChatMessageResponse, ChatHistoryResponse
from app.services.coach_service import CoachService

router = APIRouter(prefix="/chat", tags=["Career coach"])


@router.get("/context")
def chat_context(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    report = CoachService.latest_report(db, current_user.id)
    return CoachService.report_context(db, report) if report else None


@router.post("/message", response_model=ChatMessageResponse, dependencies=[Depends(expensive_request)])
def send_chat(req: ChatMessageRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = req.content.strip()
    if not query:
        raise HTTPException(status_code=422, detail="Enter a career question.")
    report = CoachService.latest_report(db, current_user.id)
    if report is None:
        raise HTTPException(status_code=400, detail="Analyze a resume and job role before starting your coaching session.")
    session = CoachService.get_or_create_daily_session(db, current_user.id, report)
    reply = CoachService.generate_coach_response(db, query, session, report)
    db.add(ChatMessage(chat_session_id=session.id, role="user", content=query))
    assistant = ChatMessage(chat_session_id=session.id, role="assistant", content=reply)
    db.add(assistant)
    db.commit()
    db.refresh(assistant)
    return assistant


@router.get("/history", response_model=ChatHistoryResponse)
def chat_history(limit: int = Query(40, ge=1, le=100), before: int | None = Query(None, gt=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    report = CoachService.latest_report(db, current_user.id)
    if report is None:
        return ChatHistoryResponse(messages=[])
    session = CoachService.get_or_create_daily_session(db, current_user.id, report)
    query = db.query(ChatMessage).filter(ChatMessage.chat_session_id == session.id)
    if before: query = query.filter(ChatMessage.id < before)
    rows = query.order_by(ChatMessage.id.desc()).limit(limit+1).all()
    return ChatHistoryResponse(messages=list(reversed(rows[:limit])), next_before=rows[limit-1].id if len(rows)>limit else None)


@router.delete("/clear", status_code=204)
def clear_chat(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    report = CoachService.latest_report(db, current_user.id)
    if report:
        session = CoachService.get_or_create_daily_session(db, current_user.id, report)
        db.query(ChatMessage).filter(ChatMessage.chat_session_id == session.id).delete()
        db.commit()
