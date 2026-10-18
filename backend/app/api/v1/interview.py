from app.core.request_limits import expensive_request
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import update, or_
from sqlalchemy.exc import IntegrityError, OperationalError
from datetime import datetime, timedelta, timezone
import hashlib, json, secrets

from app.core.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.session import ResumeSession
from app.models.interview import InterviewSession, InterviewEvaluation
from app.schemas import StartInterviewRequest, EvaluateAnswerRequest, AnswerFeedbackResponse, InterviewSessionResponse
from app.services import InterviewService

router = APIRouter(prefix="/interview", tags=["Interview Studio"])


@router.post("/start", response_model=InterviewSessionResponse, status_code=201, dependencies=[Depends(expensive_request)])
def start_interview(req: StartInterviewRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    latest_resume = db.query(ResumeSession).filter(ResumeSession.user_id == current_user.id).order_by(ResumeSession.created_at.desc()).first()
    q = InterviewService.generate_initial_question(req.interview_type, req.target_role)
    
    session = InterviewSession(
        user_id=current_user.id,
        resume_session_id=latest_resume.id if latest_resume else None,
        interview_type=req.interview_type,
        target_role=req.target_role,
        overall_score=0.0,
        history=[{"question": q, "answer": None, "evaluation": None}]
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session



@router.get("/sessions")
def list_interviews(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rows = db.query(InterviewSession).filter(InterviewSession.user_id == current_user.id).order_by(InterviewSession.id.desc()).limit(20).all()
    return [{"id": row.id, "target_role": row.target_role, "created_at": row.created_at,
             "completed": bool(row.history and row.history[-1].get("answer") is not None)} for row in rows]


def owned_interview(session_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = db.query(InterviewSession).filter(InterviewSession.id == session_id, InterviewSession.user_id == current_user.id).first()
    if session is None: raise HTTPException(404, "Interview not found")
    return session


@router.get("/sessions/{session_id}", response_model=InterviewSessionResponse)
def get_interview(session_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    response = InterviewSessionResponse.model_validate(owned_interview(session_id, db, current_user)).model_dump()
    # Older saved model examples are not evidence of the user's personal history.
    for item in response['history']:
        if item.get('answer') is not None and item.get('evaluation'):
            item['evaluation']['suggested_answer'] = InterviewService.answer_template(item['answer'])
    return response


@router.post("/evaluate", response_model=AnswerFeedbackResponse, dependencies=[Depends(expensive_request)])
def eval_interview(req: EvaluateAnswerRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = owned_interview(req.session_id, db, current_user)
    history = list(session.history or [])
    index = req.question_index
    if index is None:  # Compatibility for older clients; new clients send stable question indexes.
        index = next((i for i in reversed(range(len(history))) if history[i]['question'] == req.question), -1)
    if index < 0 or index >= len(history) or history[index]['question'] != req.question:
        raise HTTPException(409, "This question changed. Reload the saved interview.")
    if not req.user_answer.strip(): raise HTTPException(422, "Enter an interview answer.")
    fingerprint = hashlib.sha256(json.dumps([req.question, req.user_answer]).encode()).hexdigest()
    key = (session.id, index)
    attempt = db.get(InterviewEvaluation, key)
    if attempt and attempt.status == 'completed':
        if attempt.fingerprint != fingerprint: raise HTTPException(409, "This question already has a saved answer. Reload the interview.")
        return attempt.response
    if history[index].get('answer') is not None or index != len(history)-1:
        raise HTTPException(409, "This question is no longer active. Reload the saved interview.")
    token = secrets.token_hex(24)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    # A bounded lease spans provider processing without holding a database transaction open.
    try:
        if attempt is None:
            attempt = InterviewEvaluation(session_id=session.id, question_index=index, fingerprint=fingerprint,
                status='processing', lease_token=token, expires_at=now+timedelta(minutes=10))
            db.add(attempt); db.flush()
        else:
            claimed = db.execute(update(InterviewEvaluation).where(
                InterviewEvaluation.session_id == session.id, InterviewEvaluation.question_index == index,
                or_(InterviewEvaluation.status == 'failed', (InterviewEvaluation.status == 'processing') & (InterviewEvaluation.expires_at < now))
            ).values(fingerprint=fingerprint,status='processing',lease_token=token,expires_at=now+timedelta(minutes=10))).rowcount
            if not claimed:
                db.rollback()
                raise HTTPException(409, "An answer is being evaluated. Wait, then retry or reload the saved interview.")
        role, kind = session.target_role, session.interview_type
        db.commit()
    except (IntegrityError, OperationalError) as exc:
        db.rollback()
        raise HTTPException(409, "An answer is being evaluated. Retry shortly or reload the saved interview.") from exc
    try:
        result = InterviewService.evaluate_response(kind, role, req.question, req.user_answer)
        # Fence expired/replaced attempts before updating either saved history or cached response.
        claimed = db.execute(update(InterviewEvaluation).where(
            InterviewEvaluation.session_id == req.session_id, InterviewEvaluation.question_index == index,
            InterviewEvaluation.lease_token == token, InterviewEvaluation.status == 'processing',
            InterviewEvaluation.expires_at > datetime.now(timezone.utc).replace(tzinfo=None)
        ).values(status='completed')).rowcount
        if not claimed: raise HTTPException(409, "This evaluation expired or was replaced. Reload the saved interview.")
        db.expire_all()
        session = owned_interview(req.session_id, db, current_user)
        history = list(session.history or [])
        if len(history)-1 != index or history[index].get('answer') is not None:
            raise HTTPException(409, "This question already changed. Reload the saved interview.")
        next_question = result.get('next_question') if len(history) < 20 else None
        response = dict(question=req.question,user_answer=req.user_answer,score=result['score'],
            strengths=result.get('strengths',[]),mistakes=result.get('mistakes',[]),
            suggested_answer=result.get('suggested_answer',''),next_question=next_question)
        history[index] = {'question': req.question, 'answer': req.user_answer, 'evaluation': response}
        if next_question: history.append({'question':next_question,'answer':None,'evaluation':None})
        session.history = history
        scores = [item['evaluation']['score'] for item in history if item.get('evaluation')]
        session.overall_score = sum(scores)/len(scores)
        db.execute(update(InterviewEvaluation).where(InterviewEvaluation.session_id == req.session_id,
            InterviewEvaluation.question_index == index, InterviewEvaluation.lease_token == token).values(response=response))
        db.commit()
        return response
    except Exception:
        db.rollback()
        db.execute(update(InterviewEvaluation).where(InterviewEvaluation.session_id == req.session_id,
            InterviewEvaluation.question_index == index, InterviewEvaluation.lease_token == token,
            InterviewEvaluation.status == 'processing').values(status='failed'))
        db.commit()
        raise
