from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas import UserResponse

router = APIRouter(prefix="/user", tags=["Settings & Preferences"])


@router.get("/settings")
def get_user_settings(current_user: User = Depends(get_current_user)):
    return {
        "target_job_role": current_user.target_job_role or "AI Engineer",
        "preferred_ai_model": current_user.preferred_ai_model or "gemini-2.5-flash",
        "email": current_user.email,
        "full_name": current_user.full_name
    }


@router.put("/settings")
def update_user_settings(
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if "target_job_role" in payload:
        current_user.target_job_role = payload["target_job_role"]
    if "preferred_ai_model" in payload:
        current_user.preferred_ai_model = payload["preferred_ai_model"]
    if "full_name" in payload:
        current_user.full_name = payload["full_name"]
    db.commit()
    db.refresh(current_user)
    return {"message": "Settings updated successfully", "user": UserResponse.model_validate(current_user)}
