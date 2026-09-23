"""Pydantic schemas for user-related requests and responses."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    """Payload for registering a new user."""

    email: EmailStr
    password: str = Field(..., min_length=8, description="Minimum 8 characters")
    full_name: str = Field(..., min_length=1, max_length=255)
    phone_number: Optional[str] = Field(None, max_length=32)

    @field_validator("password")
    @classmethod
    def _password_strength(cls, v: str) -> str:
        if v.isdigit():
            raise ValueError("Password must not be entirely numeric")
        return v


class UserLogin(BaseModel):
    """Payload for authenticating an existing user."""

    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Public representation of a user account."""

    id: UUID
    email: EmailStr
    full_name: str
    phone_number: Optional[str] = None
    is_active: bool
    is_admin: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    """JWT bearer token response."""

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Data embedded inside a JWT token."""

    email: Optional[str] = None


class ForgotPasswordRequest(BaseModel):
    """Payload for requesting a password reset email."""

    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Payload for submitting a new password using a reset token."""

    token: str = Field(..., min_length=1, description="Reset token from email")
    new_password: str = Field(..., min_length=8, description="Minimum 8 characters")

    @field_validator("new_password")
    @classmethod
    def _password_strength(cls, v: str) -> str:
        if v.isdigit():
            raise ValueError("Password must not be entirely numeric")
        return v


class MessageResponse(BaseModel):
    """Generic status and message response."""

    message: str
    reset_link: Optional[str] = None

