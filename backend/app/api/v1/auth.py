import hashlib
import json
import os
import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional

import jwt
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy import update, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.request_limits import WindowLimiter
from app.deps import get_current_user, oauth2_scheme
from app.models.user import User
from app.models.revoked_token import RevokedToken
from app.models.account_token import AccountToken
from app.models.profile import ResumeVersion
from app.services import email_service
from app.services.upload_safety import remove_owned_directory
from app.schemas import (
    UserCreate,
    UserLogin,
    UserResponse,
    Token,
    PasswordChange,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    VerifyEmailRequest,
    AccountDeleteRequest,
)

router = APIRouter(prefix="/auth", tags=["Auth"])

# Rate limiters for abuse controls
_password_attempts = WindowLimiter(limit=5)
_forgot_attempts = WindowLimiter(limit=3)
_reset_attempts = WindowLimiter(limit=5)
_verification_attempts = WindowLimiter(limit=3)
_verify_token_attempts = WindowLimiter(limit=5)
_delete_attempts = WindowLimiter(limit=5)


def should_set_cookies(request: Request = None) -> bool:
    if request is None:
        return False
    if request.headers.get("x-use-cookie") == "1" or request.headers.get("x-auth-cookie") == "1":
        return True
    if "careermind_session" in request.cookies or "careermind_csrf" in request.cookies:
        return True
    if request.headers.get("sec-fetch-dest") == "document":
        return True
    return False


def set_auth_cookies(response: Response = None, token: str = "", request: Request = None):
    """
    Sets secure HttpOnly session cookie and cross-site request forgery (CSRF) token cookie
    when requested by browser clients or when session cookies are active.
    """
    if response is None or not should_set_cookies(request):
        return

    is_secure = settings.ENVIRONMENT == "production" or (request is not None and request.url.scheme == "https")
    max_age = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    response.set_cookie(
        key="careermind_session",
        value=token,
        max_age=max_age,
        expires=max_age,
        path="/",
        httponly=True,
        secure=is_secure,
        samesite="lax",
    )

    csrf_token = secrets.token_urlsafe(32)
    response.set_cookie(
        key="careermind_csrf",
        value=csrf_token,
        max_age=max_age,
        expires=max_age,
        path="/",
        httponly=False,
        secure=is_secure,
        samesite="lax",
    )


def clear_auth_cookies(response: Response = None):
    """
    Clears session and CSRF cookies.
    """
    if response is not None:
        response.delete_cookie(key="careermind_session", path="/")
        response.delete_cookie(key="careermind_csrf", path="/")


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    response: Response = Response(),
    request: Request = None,
):
    canonical_email = str(user_in.email).strip().lower()
    if db.query(User).filter(func.lower(User.email) == canonical_email).first():
        raise HTTPException(status_code=400, detail="A user with this email ID already exists.")
    # SQLite can reuse a deleted numeric ID. A fresh session generation prevents
    # the deleted account's JWTs from authenticating as a later account with that ID.
    user = User(email=canonical_email, full_name=user_in.full_name,
                hashed_password=get_password_hash(user_in.password),
                session_version=secrets.randbelow(1_000_000_000) + 1)
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="A user with this email ID already exists.")
    db.refresh(user)
    token = create_access_token(user.id, timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES), session_version=user.session_version)
    set_auth_cookies(response, token, request)
    return Token(access_token=token, user=UserResponse.model_validate(user))


@router.post("/login", response_model=Token)
def login(
    user_in: UserLogin,
    db: Session = Depends(get_db),
    response: Response = Response(),
    request: Request = None,
):
    canonical_email = str(user_in.email).strip().lower()
    user = db.query(User).filter(func.lower(User.email) == canonical_email).first()
    if not user or not user.is_active or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email address or password.")
    token = create_access_token(user.id, timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES), session_version=user.session_version)
    set_auth_cookies(response, token, request)
    return Token(access_token=token, user=UserResponse.model_validate(user))


@router.get("/me", response_model=UserResponse)
def read_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/logout", status_code=204)
def logout(
    request: Request = None,
    response: Response = Response(),
    token: Optional[str] = Depends(oauth2_scheme),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    clear_auth_cookies(response)
    raw_token = token or (request.cookies.get("careermind_session") if request else None)
    if raw_token:
        try:
            payload = jwt.decode(raw_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM], options={"verify_exp": False})
            db.query(RevokedToken).filter(RevokedToken.expires_at < datetime.now(timezone.utc)).delete()
            db.merge(RevokedToken(
                token_hash=hashlib.sha256(raw_token.encode()).hexdigest(),
                expires_at=datetime.fromtimestamp(payload.get("exp", 0), timezone.utc)
            ))
            db.commit()
        except Exception as exc:
            db.rollback()
            raise HTTPException(503, "Could not revoke your session. Please retry signing out.") from exc


@router.post("/change-password", response_model=Token)
def change_password(
    body: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    response: Response = Response(),
    request: Request = None,
):
    if not _password_attempts.allow(current_user.id):
        raise HTTPException(429, "Too many password-change attempts. Retry in a minute.", headers={"Retry-After": "60"})
    if not verify_password(body.current_password, current_user.hashed_password):
        raise HTTPException(400, "Your current password is incorrect.")
    if body.current_password == body.new_password:
        raise HTTPException(400, "Choose a different new password.")
    previous_version = current_user.session_version
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
    set_auth_cookies(response, token, request)
    return Token(access_token=token, user=UserResponse.model_validate(current_user))


@router.post("/forgot-password")
def forgot_password(
    body: ForgotPasswordRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    client_key = request.client.host if request.client else "unknown"
    if not _forgot_attempts.allow(client_key):
        raise HTTPException(429, "Too many password-reset requests. Retry in a minute.", headers={"Retry-After": "60"})

    if not email_service.is_smtp_configured():
        raise HTTPException(503, "Password recovery email is unavailable. Please contact support or try again later.")

    canonical_email = str(body.email).strip().lower()
    user = db.query(User).filter(func.lower(User.email) == canonical_email).first()

    if user and user.is_active:
        # Invalidate any prior unused reset tokens for this user
        db.query(AccountToken).filter(
            AccountToken.user_id == user.id,
            AccountToken.token_type == "password_reset",
            AccountToken.used_at.is_(None)
        ).delete()

        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        account_token = AccountToken(
            user_id=user.id,
            token_hash=token_hash,
            token_type="password_reset",
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
            created_at=datetime.now(timezone.utc)
        )
        db.add(account_token)
        db.commit()

        email_service.send_password_reset_email(user.email, raw_token)

    return {
        "detail": "Request received. If an eligible account exists and email delivery succeeds, you will receive password reset instructions. If no email arrives, retry later or contact support.",
        "email_delivery_configured": email_service.is_smtp_configured()
    }


@router.post("/reset-password")
def reset_password(
    body: ResetPasswordRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    client_key = request.client.host if request.client else "unknown"
    if not _reset_attempts.allow(client_key):
        raise HTTPException(429, "Too many password reset attempts. Retry in a minute.", headers={"Retry-After": "60"})

    token_hash = hashlib.sha256(body.token.encode()).hexdigest()
    now = datetime.now(timezone.utc)

    account_token = db.query(AccountToken).filter(
        AccountToken.token_hash == token_hash,
        AccountToken.token_type == "password_reset",
        AccountToken.used_at.is_(None)
    ).first()

    if not account_token:
        raise HTTPException(400, "Invalid or expired password reset token.")

    # Check expiry handling timezone-aware comparison
    token_exp = account_token.expires_at
    if token_exp.tzinfo is None:
        token_exp = token_exp.replace(tzinfo=timezone.utc)

    if token_exp <= now:
        raise HTTPException(400, "Invalid or expired password reset token.")

    user = db.query(User).filter(User.id == account_token.user_id).first()
    if not user or not user.is_active:
        raise HTTPException(400, "Account is invalid or inactive.")

    # Claim the single-use token atomically, including across worker processes.
    claimed = db.execute(update(AccountToken).where(
        AccountToken.id == account_token.id,
        AccountToken.used_at.is_(None),
        AccountToken.expires_at > now,
    ).values(used_at=now), execution_options={"synchronize_session": False})
    if claimed.rowcount != 1:
        db.rollback()
        raise HTTPException(400, "Invalid or expired password reset token.")
    # Invalidate existing sessions
    db.execute(update(User).where(User.id == user.id).values(
        hashed_password=get_password_hash(body.new_password),
        session_version=User.session_version + 1,
    ), execution_options={"synchronize_session": False})

    db.commit()

    return {"detail": "Password has been reset successfully. Please sign in with your new password."}


@router.post("/send-verification")
def send_email_verification(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not _verification_attempts.allow(current_user.id):
        raise HTTPException(429, "Too many verification requests. Retry in a minute.", headers={"Retry-After": "60"})

    if current_user.is_verified:
        return {"detail": "Email is already verified."}

    # Invalidate prior unused verification tokens
    db.query(AccountToken).filter(
        AccountToken.user_id == current_user.id,
        AccountToken.token_type == "email_verification",
        AccountToken.used_at.is_(None)
    ).delete()

    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    account_token = AccountToken(
        user_id=current_user.id,
        token_hash=token_hash,
        token_type="email_verification",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        created_at=datetime.now(timezone.utc)
    )
    db.add(account_token)
    db.commit()

    delivery = email_service.send_verification_email(current_user.email, raw_token)
    if not delivery["delivered"]:
        raise HTTPException(503, "Verification email could not be sent. Please try again later or contact support.")

    return {
        "detail": "Verification email has been sent.",
        "email_delivery_configured": email_service.is_smtp_configured()
    }


@router.post("/verify-email")
def verify_email(
    body: VerifyEmailRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    client_key = request.client.host if request.client else "unknown"
    if not _verify_token_attempts.allow(client_key):
        raise HTTPException(429, "Too many verification attempts. Retry in a minute.", headers={"Retry-After": "60"})

    token_hash = hashlib.sha256(body.token.encode()).hexdigest()
    now = datetime.now(timezone.utc)

    account_token = db.query(AccountToken).filter(
        AccountToken.token_hash == token_hash,
        AccountToken.token_type == "email_verification",
        AccountToken.used_at.is_(None)
    ).first()

    if not account_token:
        raise HTTPException(400, "Invalid or expired verification token.")

    token_exp = account_token.expires_at
    if token_exp.tzinfo is None:
        token_exp = token_exp.replace(tzinfo=timezone.utc)

    if token_exp <= now:
        raise HTTPException(400, "Invalid or expired verification token.")

    user = db.query(User).filter(User.id == account_token.user_id).first()
    if not user or not user.is_active:
        raise HTTPException(400, "Account is invalid or inactive.")

    account_token.used_at = now
    user.is_verified = True
    db.commit()

    return {"detail": "Email verified successfully."}


@router.get("/export")
def export_account_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    def record_data(record):
        return {column.name: getattr(record, column.name) for column in record.__table__.columns} if record else None

    data = {
        "export_metadata": {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "format_version": "1.0",
            "account_id": current_user.id
        },
        "user_profile": {
            "id": current_user.id,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "target_job_role": current_user.target_job_role,
            "preferred_ai_model": current_user.preferred_ai_model,
            "is_verified": current_user.is_verified,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
            "updated_at": current_user.updated_at.isoformat() if current_user.updated_at else None,
        },
        "resume_sessions": [
            {
                "id": s.id,
                "file_name": s.file_name,
                "file_type": s.file_type,
                "parsed_data": s.parsed_data,
                "raw_text": s.raw_text,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in current_user.resume_sessions
        ],
        "career_reports": [
            {
                "id": r.id,
                "job_role": r.job_role,
                "field": r.field,
                "experience_level": r.experience_level,
                "nex_score": r.nex_score,
                "nex_score_breakdown": r.nex_score_breakdown,
                "resume_score": r.resume_score,
                "ats_score": r.ats_score,
                "readiness_score": r.readiness_score,
                "analysis_data": r.analysis_data,
                "gap_analysis": r.gap_analysis,
                "roadmap_data": r.roadmap_data,
                "project_recommendations": r.project_recommendations,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in current_user.reports
        ],
        "chat_sessions": [
            {
                "id": cs.id,
                "title": cs.title,
                "session_date": cs.session_date,
                "resume_session_id": cs.resume_session_id,
                "messages": [
                    {
                        "id": m.id,
                        "role": m.role,
                        "content": m.content,
                        "created_at": m.created_at.isoformat() if m.created_at else None,
                    }
                    for m in cs.messages
                ],
                "created_at": cs.created_at.isoformat() if cs.created_at else None,
            }
            for cs in current_user.chat_sessions
        ],
        "interview_sessions": [
            {
                "id": iv.id,
                "target_role": iv.target_role,
                "interview_type": iv.interview_type,
                "overall_score": iv.overall_score,
                "history": iv.history,
                "created_at": iv.created_at.isoformat() if iv.created_at else None,
            }
            for iv in current_user.interview_sessions
        ],
        "research_jobs": [
            {
                "id": rj.id,
                "status": rj.status,
                "preferences": rj.request_data,
                "report_id": rj.report_id,
                "error": rj.error,
                "created_at": rj.created_at.isoformat() if rj.created_at else None,
            }
            for rj in current_user.research_jobs
        ],
        "career_profile": record_data(current_user.career_profile),
        "career_memory": record_data(current_user.career_memory),
        "resume_versions": [record_data(version) for version in db.query(ResumeVersion).filter(
            ResumeVersion.resume_session_id.in_([s.id for s in current_user.resume_sessions])
        ).all()],
    }

    content = json.dumps(data, indent=2, default=str)
    return Response(
        content=content,
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="careermind-export-user-{current_user.id}.json"'
        }
    )


@router.delete("/delete")
def delete_account(
    body: AccountDeleteRequest,
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not _delete_attempts.allow(current_user.id):
        raise HTTPException(429, "Too many deletion attempts. Retry in a minute.", headers={"Retry-After": "60"})

    if body.confirmation != "DELETE MY ACCOUNT":
        raise HTTPException(status_code=400, detail='Confirmation phrase must be "DELETE MY ACCOUNT".')

    if not verify_password(body.password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect password.")

    # 2. Revoke currently active token
    auth_header = request.headers.get("authorization")
    raw_token = auth_header[7:].strip() if auth_header and auth_header.lower().startswith("bearer ") else request.cookies.get("careermind_session")
    if raw_token:
        try:
            payload = jwt.decode(raw_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM], options={"verify_exp": False})
            db.merge(RevokedToken(
                token_hash=hashlib.sha256(raw_token.encode()).hexdigest(),
                expires_at=datetime.fromtimestamp(payload.get("exp", 0), timezone.utc)
            ))
        except Exception:
            pass

    # 3. Clear auth cookies
    clear_auth_cookies(response)

    # 4. Delete user record (cascades to all user tables)
    db.delete(current_user)
    # Check relational constraints before touching files. Only remove this user's
    # owned upload directory; never trust arbitrary file paths stored in records.
    db.flush()
    remove_owned_directory(os.path.join(settings.UPLOAD_DIR, f"user_{current_user.id}"), settings.UPLOAD_DIR)
    db.commit()

    return {"detail": "Account and all associated personal data have been permanently deleted."}
