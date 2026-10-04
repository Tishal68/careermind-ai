from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.chat import ChatSession, ChatMessage, CareerMemory
from app.repositories.base_repo import BaseRepository


class ChatRepository(BaseRepository[ChatSession]):
    def __init__(self):
        super().__init__(ChatSession)

    def get_daily_session(self, db: Session, user_id: int, date_str: str) -> Optional[ChatSession]:
        return db.query(ChatSession).filter(
            ChatSession.user_id == user_id,
            ChatSession.session_date == date_str,
            ChatSession.is_active == True
        ).first()

    def get_messages(self, db: Session, chat_session_id: int) -> List[ChatMessage]:
        return db.query(ChatMessage).filter(ChatMessage.chat_session_id == chat_session_id).order_by(ChatMessage.created_at.asc()).all()

    def add_message(self, db: Session, chat_session_id: int, role: str, content: str) -> ChatMessage:
        msg = ChatMessage(chat_session_id=chat_session_id, role=role, content=content)
        db.add(msg)
        db.commit()
        db.refresh(msg)
        return msg

    def get_career_memory(self, db: Session, user_id: int) -> Optional[CareerMemory]:
        return db.query(CareerMemory).filter(CareerMemory.user_id == user_id).first()

    def create_career_memory(self, db: Session, user_id: int, target_role: str, skills: list) -> CareerMemory:
        memory = CareerMemory(user_id=user_id, target_job_role=target_role, extracted_skills=skills, last_nex_score=89)
        db.add(memory)
        db.commit()
        db.refresh(memory)
        return memory


chat_repo = ChatRepository()
