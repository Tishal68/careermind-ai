import hashlib
import jwt
from datetime import datetime, timezone
from app.models.revoked_token import RevokedToken
from app.deps import oauth2_scheme
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import update
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_password_hash, verify_password, create_access_token
from app.deps import get_current_user
from app.models.user import User
from app.schemas import UserCreate, UserLogin, UserResponse, Token, PasswordChange

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user_in.email).first():
        raise HTTPException(status_code=400, detail="A user with this email ID already exists.")
    user = User(email=user_in.email, full_name=user_in.full_name, hashed_password=get_password_hash(user_in.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="A user with this email ID already exists.")
    db.refresh(user)
    token = create_access_token(user.id, timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES), session_version=user.session_version)
    return Token(access_token=token, user=UserResponse.model_validate(user))


@router.post("/login", response_model=Token)
def login(user_in: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_in.email).first()
    if not user or not user.is_active or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email address or password.")
    token = create_access_token(user.id, timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES), session_version=user.session_version)
    return Token(access_token=token, user=UserResponse.model_validate(user))


@router.get("/me", response_model=UserResponse)
def read_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/logout", status_code=204)
def logout(token: str = Depends(oauth2_scheme), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    db.query(RevokedToken).filter(RevokedToken.expires_at < datetime.now(timezone.utc)).delete()
    db.merge(RevokedToken(token_hash=hashlib.sha256(token.encode()).hexdigest(),
                         expires_at=datetime.fromtimestamp(payload["exp"], timezone.utc)))
    db.commit()


# Single-instance per-account budget; independent of AI research quotas.
from app.core.request_limits import WindowLimiter
_password_attempts = WindowLimiter(limit=5)


@router.post("/change-password", response_model=Token)
def change_password(body: PasswordChange, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not _password_attempts.allow(current_user.id):
        raise HTTPException(429, "Too many password-change attempts. Retry in a minute.", headers={"Retry-After": "60"})
    if not verify_password(body.current_password, current_user.hashed_password):
        raise HTTPException(400, "Your current password is incorrect.")
    if body.current_password == body.new_password:
        raise HTTPException(400, "Choose a different new password.")
    previous_version = current_user.session_version
    # Compare-and-swap prevents concurrent changes authorized by the same old
    # password from overwriting each other on SQLite or PostgreSQL.
    changed = db.execute(update(User).where(
        User.id == current_user.id,
        User.hashed_password == current_user.hashed_password,
        User.session_version == previous_version,
    ).values(hashed_password=get_password_hash(body.new_password),
             session_version=previous_version + 1), execution_options={"synchronize_session": False})
    if changed.rowcount != 1:
        db.rollback()
        raise HTTPException(409, "Your account changed during this request. Sign in again before retrying.")
    db.commit()
    db.refresh(current_user)
    token = create_access_token(current_user.id, session_version=previous_version + 1)
    return Token(access_token=token, user=UserResponse.model_validate(current_user))
