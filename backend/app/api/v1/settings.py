from fastapi import APIRouter, Depends, HTTPException
from app.core.config import settings
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas import UserResponse

router = APIRouter(prefix="/user", tags=["Settings & Preferences"])


@router.get("/settings")
def get_user_settings(current_user: User = Depends(get_current_user)):
    return {
        "target_job_role": current_user.target_job_role or "AI Engineer",
        "preferred_ai_model": settings.OLLAMA_MODEL,
        "coach_provider": settings.DEFAULT_AI_PROVIDER,
        "coach_model": settings.GEMINI_MODEL if settings.DEFAULT_AI_PROVIDER.lower() == "gemini" else settings.OLLAMA_MODEL,
        "fallback_enabled": settings.AI_FALLBACK_ENABLED,
        "email": current_user.email,
        "full_name": current_user.full_name
    }


class SettingsUpdate(BaseModel):
    target_job_role: str = Field(default="AI Engineer", min_length=1, max_length=100)
    preferred_ai_model: str | None = None
    full_name: str = Field(default="", max_length=255)


@router.put("/settings")
def update_user_settings(
    payload: SettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if payload.preferred_ai_model is not None and payload.preferred_ai_model != settings.OLLAMA_MODEL:
        raise HTTPException(422, "The AI model is configured by the service administrator.")
    for key, value in payload.model_dump(exclude_unset=True, exclude={"preferred_ai_model"}).items():
        setattr(current_user, key, value)
    db.commit()
    db.refresh(current_user)
    return {"message": "Settings updated successfully", "user": UserResponse.model_validate(current_user)}
