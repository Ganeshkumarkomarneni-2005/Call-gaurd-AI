"""JWT authentication helpers and password hashing for CallGuard AI."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import structlog
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.db.session import get_db

logger: structlog.BoundLogger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def hash_password(password: str) -> str:
    """Return a bcrypt hash of *password*."""
    return _pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if *plain* matches *hashed*."""
    return _pwd_context.verify(plain, hashed)


# ---------------------------------------------------------------------------
# JWT tokens
# ---------------------------------------------------------------------------

_ALGORITHM = "HS256"


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a signed JWT access token.

    Args:
        data: Payload claims to encode (e.g. ``{"sub": email}``).
        expires_delta: Token lifetime; defaults to ``settings.access_token_expire_minutes``.

    Returns:
        Encoded JWT string.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=_ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and verify a JWT token.

    Returns:
        The payload dict on success, or ``None`` if invalid / expired.
    """
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[_ALGORITHM])
    except JWTError as exc:
        logger.debug("JWT decode failed", error=str(exc))
        return None


def create_password_reset_token(email: str, expires_minutes: int = 15) -> str:
    """Create a signed JWT token specifically for password resets.

    Args:
        email: User email address.
        expires_minutes: Token validity lifetime (default 15 mins).

    Returns:
        Encoded JWT token string.
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    payload = {
        "sub": email,
        "scope": "password_reset",
        "exp": expire,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=_ALGORITHM)


def verify_password_reset_token(token: str) -> Optional[str]:
    """Verify a password reset token and return the associated email address.

    Args:
        token: JWT reset token.

    Returns:
        The email address if valid, or None if invalid/expired.
    """
    payload = decode_access_token(token)
    if payload is None:
        return None
    if payload.get("scope") != "password_reset":
        return None
    return payload.get("sub")



# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------

_credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    """FastAPI dependency that resolves the currently authenticated user.

    Raises:
        HTTPException: 401 if the token is missing, invalid, or the user
            no longer exists.
    """
    # Import here to avoid circular imports
    from backend.services.user_service import get_user_by_email  # noqa: PLC0415

    payload = decode_access_token(token)
    if payload is None:
        raise _credentials_exception

    email: Optional[str] = payload.get("sub")
    if email is None:
        raise _credentials_exception

    user = await get_user_by_email(db, email)
    if user is None:
        raise _credentials_exception
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account",
        )
    return user
