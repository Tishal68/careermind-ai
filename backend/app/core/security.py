import bcrypt
import secrets
import hashlib
import base64
from datetime import datetime, timedelta, timezone
from typing import Any, Union
import jwt
from app.core.config import settings


def _password_digest(password: str) -> bytes:
    return base64.b64encode(hashlib.sha256(password.encode("utf-8")).digest())


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        if hashed_password.startswith("bcrypt-sha256$"):
            return bcrypt.checkpw(_password_digest(plain_password), hashed_password.removeprefix("bcrypt-sha256$").encode())
        # Preserve existing bcrypt accounts, but never accept a truncated password.
        raw = plain_password.encode("utf-8")
        return len(raw) <= 72 and bcrypt.checkpw(raw, hashed_password.encode())
    except (ValueError, TypeError):
        return False


def get_password_hash(password: str) -> str:
    return "bcrypt-sha256$" + bcrypt.hashpw(_password_digest(password), bcrypt.gensalt()).decode()


def create_access_token(subject: Union[str, Any], expires_delta: timedelta = None, *, session_version: int = 0) -> str:
    """Generate a JWT access token with expiration."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expire, "sub": str(subject), "jti": secrets.token_urlsafe(24), "sv": session_version}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt
