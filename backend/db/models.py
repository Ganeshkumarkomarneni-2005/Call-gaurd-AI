"""ORM models for CallGuard AI.

All models use UUID primary keys and include ``created_at`` / ``updated_at``
timestamp columns that are set automatically.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator, CHAR
import uuid as _uuid_mod

from backend.db.base import Base


# ---------------------------------------------------------------------------
# UUID portability helper (SQLite stores as CHAR(36), Postgres uses native UUID)
# ---------------------------------------------------------------------------


class UUIDType(TypeDecorator):
    """Platform-independent UUID type stored as CHAR(36)."""

    impl = CHAR(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):  # noqa: ANN001
        if value is None:
            return None
        if isinstance(value, _uuid_mod.UUID):
            return str(value)
        return str(_uuid_mod.UUID(str(value)))

    def process_result_value(self, value, dialect):  # noqa: ANN001
        if value is None:
            return None
        return _uuid_mod.UUID(str(value))


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------


class User(Base):
    """Application user / account holder."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, primary_key=True, default=_uuid
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone_number: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now, nullable=False
    )

    calls: Mapped[list["Call"]] = relationship("Call", back_populates="user", lazy="select")
    notifications: Mapped[list["Notification"]] = relationship(
        "Notification", back_populates="user", lazy="select"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User id={self.id} email={self.email!r}>"


# ---------------------------------------------------------------------------
# Call
# ---------------------------------------------------------------------------


class Call(Base):
    """A single inbound phone call."""

    __tablename__ = "calls"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=_uuid)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUIDType, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(String(32), default="ringing", nullable=False)
    caller_number: Mapped[str] = mapped_column(String(32), nullable=False)
    caller_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    virtual_number: Mapped[str] = mapped_column(String(32), nullable=False)
    telephony_call_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    telephony_provider: Mapped[str] = mapped_column(String(64), default="twilio", nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now, nullable=False
    )

    user: Mapped[Optional[User]] = relationship("User", back_populates="calls")
    transcript: Mapped[Optional["Transcript"]] = relationship(
        "Transcript", back_populates="call", uselist=False, lazy="select"
    )
    analysis: Mapped[Optional["CallAnalysis"]] = relationship(
        "CallAnalysis", back_populates="call", uselist=False, lazy="select"
    )
    recruitment_details: Mapped[Optional["RecruitmentDetails"]] = relationship(
        "RecruitmentDetails", back_populates="call", uselist=False, lazy="select"
    )
    notifications: Mapped[list["Notification"]] = relationship(
        "Notification", back_populates="call", lazy="select"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Call id={self.id} status={self.status!r}>"


# ---------------------------------------------------------------------------
# Transcript
# ---------------------------------------------------------------------------


class Transcript(Base):
    """Full call transcript with NLP summary."""

    __tablename__ = "transcripts"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=_uuid)
    call_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("calls.id", ondelete="CASCADE"), nullable=False, index=True
    )
    full_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    word_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, nullable=False
    )

    call: Mapped[Call] = relationship("Call", back_populates="transcript")
    segments: Mapped[list["TranscriptSegment"]] = relationship(
        "TranscriptSegment", back_populates="transcript", lazy="select"
    )


class TranscriptSegment(Base):
    """Individual utterance within a transcript."""

    __tablename__ = "transcript_segments"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=_uuid)
    transcript_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType,
        ForeignKey("transcripts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    speaker: Mapped[str] = mapped_column(String(32), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    start_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    end_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)

    transcript: Mapped[Transcript] = relationship("Transcript", back_populates="segments")


# ---------------------------------------------------------------------------
# CallAnalysis
# ---------------------------------------------------------------------------


class CallAnalysis(Base):
    """AI analysis results for a call."""

    __tablename__ = "call_analyses"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=_uuid)
    call_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("calls.id", ondelete="CASCADE"), nullable=False, index=True
    )
    caller_type: Mapped[str] = mapped_column(String(32), default="unknown", nullable=False)
    caller_type_confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    intent: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    secondary_intent: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    intent_confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(16), default="low", nullable=False)
    risk_confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    risk_indicators: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    decision: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    decision_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    decision_confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    analysis_latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, nullable=False
    )

    call: Mapped[Call] = relationship("Call", back_populates="analysis")


# ---------------------------------------------------------------------------
# RecruitmentDetails
# ---------------------------------------------------------------------------


class RecruitmentDetails(Base):
    """Structured data extracted from a recruitment call."""

    __tablename__ = "recruitment_details"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=_uuid)
    call_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("calls.id", ondelete="CASCADE"), nullable=False, index=True
    )
    company: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    recruiter_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    position: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    interview_stage: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    interview_date: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    interview_time: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    next_step: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_legitimate: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    legitimacy_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    extracted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, nullable=False
    )

    call: Mapped[Call] = relationship("Call", back_populates="recruitment_details")


# ---------------------------------------------------------------------------
# Notification
# ---------------------------------------------------------------------------


class Notification(Base):
    """In-app notification for a user."""

    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    call_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUIDType, ForeignKey("calls.id", ondelete="SET NULL"), nullable=True
    )
    notification_type: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, nullable=False
    )

    user: Mapped[User] = relationship("User", back_populates="notifications")
    call: Mapped[Optional[Call]] = relationship("Call", back_populates="notifications")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Notification id={self.id} type={self.notification_type!r}>"
