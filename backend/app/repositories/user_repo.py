from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.user import User
from app.repositories.base_repo import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self):
        super().__init__(User)

    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()

    def get_superusers(self, db: Session) -> List[User]:
        return db.query(User).filter(User.is_superuser == True).all()

    def count_total(self, db: Session) -> int:
        return db.query(User).count()


user_repo = UserRepository()
