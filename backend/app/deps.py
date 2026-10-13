import hashlib
from app.models.revoked_token import RevokedToken
from typing import Optional
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
import jwt
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login", auto_error=False)

def get_current_user(db: Session = Depends(get_db), token: Optional[str] = Depends(oauth2_scheme)) -> User:
    unauthorized = HTTPException(status_code=401, detail="Please sign in again.", headers={"WWW-Authenticate": "Bearer"})
    if not token:
        raise unauthorized
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM], options={"require": ["exp", "sub"]})
        user_id = int(payload["sub"])
    except (jwt.InvalidTokenError, ValueError, TypeError, KeyError):
        raise unauthorized
    if db.get(RevokedToken, hashlib.sha256(token.encode()).hexdigest()):
        raise unauthorized
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise unauthorized
    return user

def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Administrator access required.")
    return current_user
