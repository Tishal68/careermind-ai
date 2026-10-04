from datetime import datetime, timezone
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.models.chat import ChatSession, CareerMemory
from app.models.session import ResumeSession
from app.repositories.chat_repo import chat_repo
from app.ai.agents.coach_agent import coach_agent


class CoachService:
    @staticmethod
    def get_or_create_daily_session(db: Session, user_id: int, resume_session_id: int = None) -> ChatSession:
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        session = chat_repo.get_daily_session(db, user_id, today_str)

        if not session:
            session = ChatSession(
                user_id=user_id,
                resume_session_id=resume_session_id,
                session_date=today_str,
                title=f"Coaching Session ({today_str})",
                is_active=True
            )
            session = chat_repo.create(db, session)

        return session

    @staticmethod
    def get_or_create_career_memory(db: Session, user_id: int, parsed_resume: Dict[str, Any] = None, target_role: str = "AI Engineer") -> CareerMemory:
        memory = chat_repo.get_career_memory(db, user_id)
        if not memory:
            skills = parsed_resume.get("technical_skills", []) if parsed_resume else []
            memory = chat_repo.create_career_memory(db, user_id, target_role, skills)
        elif parsed_resume and parsed_resume.get("technical_skills"):
            memory.extracted_skills = parsed_resume.get("technical_skills", [])
            db.commit()
            db.refresh(memory)

        return memory

    @staticmethod
    def generate_coach_response(
        db: Session,
        user_id: int,
        query: str,
        chat_session_id: int,
        resume_session: ResumeSession = None
    ) -> str:
        memory = CoachService.get_or_create_career_memory(db, user_id, resume_session.parsed_data if resume_session else None)
        
        target_role = memory.target_job_role or "AI Engineer"
        extracted_skills = memory.extracted_skills or []
        nex_score = memory.last_nex_score or 89

        # Delegate execution to CoachAgent & AIProviderRouter
        return coach_agent.execute_coaching(
            query=query,
            target_role=target_role,
            skills=extracted_skills,
            nex_score=nex_score,
            provider_name="gemini"
        )
