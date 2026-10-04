from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.session import ResumeSession
from app.repositories.base_repo import BaseRepository


class ResumeSessionRepository(BaseRepository[ResumeSession]):
    def __init__(self):
        super().__init__(ResumeSession)

    def get_by_user(self, db: Session, user_id: int) -> List[ResumeSession]:
        return db.query(ResumeSession).filter(ResumeSession.user_id == user_id).order_by(ResumeSession.created_at.desc()).all()

    def get_latest_by_user(self, db: Session, user_id: int) -> Optional[ResumeSession]:
        return db.query(ResumeSession).filter(ResumeSession.user_id == user_id).order_by(ResumeSession.created_at.desc()).first()

    def count_total(self, db: Session) -> int:
        return db.query(ResumeSession).count()


session_repo = ResumeSessionRepository()
