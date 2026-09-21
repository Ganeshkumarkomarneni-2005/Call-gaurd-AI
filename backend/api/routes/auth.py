"""Authentication routes: register, login, current user."""

from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.security import create_access_token, get_current_user
from backend.db.session import get_db
from backend.schemas.user import Token, UserCreate, UserResponse
from backend.services import user_service

logger: structlog.BoundLogger = structlog.get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=Token,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
async def register(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> Token:
    """Create a new user account and return a bearer token.

    Args:
        payload: Registration details (email, password, full_name).
        db: Injected database session.

    Raises:
        HTTPException: 409 if the e-mail is already in use.
    """
    try:
        user = await user_service.create_user(db, payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc

    access_token = create_access_token(data={"sub": user.email})
    logger.info("User registered", user_id=str(user.id))
    return Token(access_token=access_token)


@router.post(
    "/login",
    response_model=Token,
    summary="Authenticate and obtain a bearer token",
)
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Token:
    """Validate credentials from an OAuth2 password form and return a token.

    Args:
        form: Standard OAuth2 form with ``username`` (email) and ``password``.
        db: Injected database session.

    Raises:
        HTTPException: 401 on invalid credentials.
    """
    user = await user_service.authenticate_user(db, form.username, form.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.email})
    logger.info("User logged in", user_id=str(user.id))
    return Token(access_token=access_token)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current authenticated user",
)
async def me(current_user=Depends(get_current_user)) -> UserResponse:
    """Return the profile of the currently authenticated user.

    Args:
        current_user: Resolved via the ``get_current_user`` dependency.
    """
    return UserResponse.model_validate(current_user)
