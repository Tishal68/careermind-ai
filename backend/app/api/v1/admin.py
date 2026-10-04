from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.deps import get_current_admin_user
from app.models.user import User
from app.models.session import ResumeSession
from app.models.report import CareerReport
from app.models.interview import InterviewSession
from app.schemas import AdminStatsResponse, UserAdminItem

router = APIRouter(prefix="/admin", tags=["Admin Portal"])


@router.get("/stats", response_model=AdminStatsResponse)
def get_admin_stats(db: Session = Depends(get_db), admin_user: User = Depends(get_current_admin_user)):
    return AdminStatsResponse(
        total_users=db.query(User).count(),
        total_resumes=db.query(ResumeSession).count(),
        total_reports=db.query(CareerReport).count(),
        total_interviews=db.query(InterviewSession).count(),
        active_admins=db.query(User).filter(User.is_superuser == True).count()
    )


@router.get("/users", response_model=List[UserAdminItem])
def list_admin_users(db: Session = Depends(get_db), admin_user: User = Depends(get_current_admin_user)):
    return db.query(User).order_by(User.created_at.desc()).all()


@router.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: int, db: Session = Depends(get_db), admin_user: User = Depends(get_current_admin_user)):
    user_to_delete = db.query(User).filter(User.id == user_id).first()
    if not user_to_delete:
        raise HTTPException(status_code=404, detail="User not found.")
    if user_to_delete.id == admin_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own admin account.")
    db.delete(user_to_delete)
    db.commit()
    return None
