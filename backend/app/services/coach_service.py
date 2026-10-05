import json
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.chat import ChatSession, ChatMessage
from app.models.report import CareerReport
from app.models.session import ResumeSession
from app.ai.agents.coach_agent import coach_agent


class CoachService:
    @staticmethod
    def latest_report(db: Session, user_id: int):
        return db.query(CareerReport).filter(CareerReport.user_id == user_id).order_by(CareerReport.id.desc()).first()

    @staticmethod
    def get_or_create_daily_session(db: Session, user_id: int, report: CareerReport) -> ChatSession:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        title = f"Report {report.id}: {report.job_role}"
        session = db.query(ChatSession).filter(
            ChatSession.user_id == user_id,
            ChatSession.session_date == today,
            ChatSession.title == title,
            ChatSession.is_active == True,
        ).first()
        if session is None:
            session = ChatSession(user_id=user_id, resume_session_id=report.resume_session_id,
                                  session_date=today, title=title, is_active=True)
            db.add(session)
            db.commit()
            db.refresh(session)
        return session

    @staticmethod
    def report_context(db: Session, report: CareerReport) -> dict:
        resume = db.query(ResumeSession).filter(
            ResumeSession.id == report.resume_session_id,
            ResumeSession.user_id == report.user_id,
        ).first()
        return {
            "report_id": report.id,
            "job_role": report.job_role,
            "file_name": resume.file_name if resume else "Resume unavailable",
            "match_percent": (report.analysis_data or {}).get("match_percent"),
            "matched_skills": (report.analysis_data or {}).get("matched_skills", []),
            "missing_skills": (report.gap_analysis or {}).get("missing_skills", []),
            "learning_steps": (report.gap_analysis or {}).get("learning_steps", []),
        }

    @staticmethod
    def generate_coach_response(db: Session, query: str, chat_session: ChatSession, report: CareerReport) -> str:
        context = CoachService.report_context(db, report)
        resume = db.query(ResumeSession).filter(
            ResumeSession.id == report.resume_session_id,
            ResumeSession.user_id == report.user_id,
        ).first()
        parsed = (resume.parsed_data or {}) if resume else {}
        context["resume_text"] = resume.raw_text[:10000] if resume and resume.raw_text else "Unavailable"
        recent = db.query(ChatMessage).filter(ChatMessage.chat_session_id == chat_session.id).order_by(ChatMessage.id.desc()).limit(8).all()
        context["conversation"] = [{"role": m.role, "content": m.content[:2000]} for m in reversed(recent)]
        return coach_agent.execute_coaching(
            query=query,
            target_role=report.job_role,
            skills=parsed.get("technical_skills", []),
            nex_score=context["match_percent"],
            context=json.dumps(context, ensure_ascii=False),
        )
