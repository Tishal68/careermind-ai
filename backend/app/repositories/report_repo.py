from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.report import CareerReport
from app.repositories.base_repo import BaseRepository


class CareerReportRepository(BaseRepository[CareerReport]):
    def __init__(self):
        super().__init__(CareerReport)

    def get_by_user(self, db: Session, user_id: int) -> List[CareerReport]:
        return db.query(CareerReport).filter(CareerReport.user_id == user_id).order_by(CareerReport.created_at.desc()).all()

    def get_latest_by_user(self, db: Session, user_id: int) -> Optional[CareerReport]:
        return db.query(CareerReport).filter(CareerReport.user_id == user_id).order_by(CareerReport.created_at.desc()).first()

    def count_total(self, db: Session) -> int:
        return db.query(CareerReport).count()


report_repo = CareerReportRepository()
