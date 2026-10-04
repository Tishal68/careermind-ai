from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.interview import InterviewSession
from app.repositories.base_repo import BaseRepository


class InterviewRepository(BaseRepository[InterviewSession]):
    def __init__(self):
        super().__init__(InterviewSession)

    def get_by_user(self, db: Session, user_id: int) -> List[InterviewSession]:
        return db.query(InterviewSession).filter(InterviewSession.user_id == user_id).order_by(InterviewSession.created_at.desc()).all()

    def count_total(self, db: Session) -> int:
        return db.query(InterviewSession).count()


interview_repo = InterviewRepository()
