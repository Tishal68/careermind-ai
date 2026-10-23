import hashlib
from app.models.revoked_token import RevokedToken
from typing import Optional
from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
import jwt
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login", auto_error=False)

def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    token: Optional[str] = Depends(oauth2_scheme)
) -> User:
    unauthorized = HTTPException(status_code=401, detail="Please sign in again.", headers={"WWW-Authenticate": "Bearer"})
    auth_token = token
    used_cookie = False

    if not auth_token:
        auth_token = request.cookies.get("careermind_session")
        if auth_token:
            used_cookie = True

    if not auth_token:
        raise unauthorized

    if used_cookie and request.method in ("POST", "PUT", "DELETE", "PATCH"):
        csrf_cookie = request.cookies.get("careermind_csrf")
        csrf_header = request.headers.get("x-csrf-token") or request.headers.get("X-CSRF-Token")
        if not csrf_cookie or not csrf_header or csrf_cookie != csrf_header:
            raise HTTPException(status_code=403, detail="CSRF token missing or invalid.")

    try:
        payload = jwt.decode(auth_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM], options={"require": ["exp", "sub"]})
        user_id = int(payload["sub"])
    except (jwt.InvalidTokenError, ValueError, TypeError, KeyError):
        raise unauthorized

    if db.get(RevokedToken, hashlib.sha256(auth_token.encode()).hexdigest()):
        raise unauthorized

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active or type(payload.get("sv", 0)) is not int or payload.get("sv", 0) != user.session_version:
        raise unauthorized

    return user

def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Administrator access required.")
    return current_user
