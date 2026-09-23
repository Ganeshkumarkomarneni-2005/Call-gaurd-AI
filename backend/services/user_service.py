"""User service — CRUD and authentication helpers."""

from __future__ import annotations

from typing import Optional
from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.security import hash_password, verify_password
from backend.db.models import User
from backend.schemas.user import UserCreate

logger: structlog.BoundLogger = structlog.get_logger(__name__)


async def create_user(db: AsyncSession, data: UserCreate) -> User:
    """Create and persist a new user.

    Args:
        db: Async database session.
        data: Validated ``UserCreate`` payload.

    Returns:
        The newly created :class:`User` ORM instance.

    Raises:
        ValueError: If a user with the same e-mail already exists.
    """
    existing = await get_user_by_email(db, data.email)
    if existing is not None:
        raise ValueError(f"User with email '{data.email}' already exists")

    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
        phone_number=data.phone_number,
    )
    db.add(user)
    await db.flush()  # populate user.id without committing
    await db.refresh(user)
    logger.info("User created", user_id=str(user.id), email=user.email)
    return user


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Fetch a user by e-mail address.

    Returns:
        :class:`User` if found, else ``None``.
    """
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: UUID) -> Optional[User]:
    """Fetch a user by primary key.

    Returns:
        :class:`User` if found, else ``None``.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def authenticate_user(
    db: AsyncSession, email: str, password: str
) -> Optional[User]:
    """Verify credentials and return the user on success.

    Args:
        db: Async database session.
        email: The user's e-mail address.
        password: Plain-text password to verify.

    Returns:
        The :class:`User` on success, or ``None`` on failure.
    """
    user = await get_user_by_email(db, email)
    if user is None:
        # Run hash verification anyway to mitigate timing attacks.
        # Use a valid bcrypt hash of a dummy value so passlib doesn't raise.
        _DUMMY_HASH = "$2b$12$K.W2wRWXN5uIAJaDp/5Rx.wqGrGTQz6u0X5JELjfnm1YEI4a.y5LG"
        verify_password("__dummy__", _DUMMY_HASH)
        logger.warning("Auth failed: user not found", email=email)
        return None
    if not verify_password(password, user.hashed_password):
        logger.warning("Auth failed: wrong password", email=email)
        return None
    if not user.is_active:
        logger.warning("Auth failed: inactive account", email=email)
        return None
    return user


async def update_user_password(
    db: AsyncSession, email: str, new_password: str
) -> Optional[User]:
    """Update password for an existing user account.

    Args:
        db: Async database session.
        email: User email address.
        new_password: New plain-text password to hash and store.

    Returns:
        The updated :class:`User` if found, or ``None``.
    """
    user = await get_user_by_email(db, email)
    if user is None:
        return None

    user.hashed_password = hash_password(new_password)
    await db.flush()
    await db.refresh(user)
    logger.info("User password updated successfully", user_id=str(user.id), email=email)
    return user

