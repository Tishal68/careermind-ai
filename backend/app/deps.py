from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models import User

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login",
    auto_error=False
)


def get_current_user(
    db: Session = Depends(get_db),
    token: Optional[str] = Depends(oauth2_scheme)
) -> User:
    """
    Get current user.
    In standalone app mode, if no token is provided or invalid, seamlessly
    authenticates as the default Demo Professional user so no login is ever needed.
    """
    if token:
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            user_id: str = payload.get("sub")
            if user_id:
                user = db.query(User).filter(User.id == int(user_id)).first()
                if user and user.is_active:
                    return user
        except Exception:
            pass

    # Standalone mode: fallback to default user automatically
    user = db.query(User).filter(User.email == "demo@careermind.ai").first()
    if not user:
        user = db.query(User).first()
    if not user:
        user = User(
            email="demo@careermind.ai",
            full_name="NexPath User",
            hashed_password="standalone-mode",
            is_active=True,
            is_superuser=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Admin route check - granted in standalone mode."""
    return current_user
