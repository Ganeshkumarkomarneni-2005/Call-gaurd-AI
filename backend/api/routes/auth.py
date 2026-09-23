"""Authentication routes: register, login, current user."""

from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.security import (
    create_access_token,
    create_password_reset_token,
    get_current_user,
    verify_password_reset_token,
)
from backend.db.session import get_db
from backend.schemas.user import (
    ForgotPasswordRequest,
    MessageResponse,
    ResetPasswordRequest,
    Token,
    UserCreate,
    UserResponse,
)
from backend.services import email_service, user_service

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


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    summary="Request a password reset link",
)
async def forgot_password(
    payload: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """Send a password reset link to the given email address.

    To protect against user enumeration, this endpoint returns a success
    message regardless of whether the email address exists in the database.
    """
    user = await user_service.get_user_by_email(db, payload.email)
    if user is not None and user.is_active:
        token = create_password_reset_token(payload.email)
        result = await email_service.send_password_reset_email(payload.email, token)
        logger.info("Password reset requested", email=payload.email)
        return MessageResponse(
            message="If this email is registered, a password reset link has been sent.",
            reset_link=result.get("reset_link"),
        )

    logger.info("Password reset requested for unknown/inactive email", email=payload.email)
    return MessageResponse(
        message="If this email is registered, a password reset link has been sent."
    )


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    summary="Reset password using a valid reset token",
)
async def reset_password(
    payload: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """Validate a reset token and update the user's password."""
    email = verify_password_reset_token(payload.token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token.",
        )

    user = await user_service.update_user_password(db, email, payload.new_password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User account not found.",
        )

    return MessageResponse(message="Password has been successfully updated. You can now log in.")


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

