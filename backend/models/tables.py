"""SQLAlchemy ORM table definitions for CallGuard AI.

All 11 tables are defined here with:
- UUID primary keys (uuid4 default)
- Proper foreign-key constraints with cascade rules
- Composite and single-column indexes on frequently queried columns
- JSON columns for flexible payload storage
- Full __repr__ methods for debugging
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.database import Base
from backend.models.enums import (
    ActionStatus,
    ActionType,
    CallerType,
    CallStatus,
    Decision,
    InitiatedBy,
    Intent,
    InterviewStage,
    NotificationType,
    ParticipantType,
    RiskLevel,
    Speaker,
)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _uuid() -> uuid.UUID:
    return uuid.uuid4()


def _now() -> datetime:
    return datetime.utcnow()


# ===========================================================================
# 1. users
# ===========================================================================

class User(Base):
    """Application user (owner of one or more virtual phone numbers)."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_uuid, nullable=False
    )
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(256), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    phone_number: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_now, onupdate=_now, nullable=False
    )

    # Relationships
    calls: Mapped[List["Call"]] = relationship(
        "Call", back_populates="user", cascade="all, delete-orphan"
    )
    notifications: Mapped[List["Notification"]] = relationship(
        "Notification", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} active={self.is_active}>"


# ===========================================================================
# 2. calls
# ===========================================================================

class Call(Base):
    """Represents a single inbound call managed by CallGuard AI."""

    __tablename__ = "calls"
    __table_args__ = (
        Index("ix_calls_user_id", "user_id"),
        Index("ix_calls_status", "status"),
        Index("ix_calls_created_at", "created_at"),
        Index("ix_calls_user_status", "user_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_uuid, nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20), default=CallStatus.RINGING.value, nullable=False
    )
    caller_number: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    caller_name: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    virtual_number: Mapped[str] = mapped_column(String(30), nullable=False)
    telephony_call_id: Mapped[Optional[str]] = mapped_column(
        String(256), unique=True, nullable=True
    )
    telephony_provider: Mapped[str] = mapped_column(
        String(50), default="mock", nullable=False
    )
    started_at: Mapped[datetime] = mapped_column(DateTime, default=_now, nullable=False)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="calls")
    participants: Mapped[List["CallParticipant"]] = relationship(
        "CallParticipant", back_populates="call", cascade="all, delete-orphan"
    )
    transcript: Mapped[Optional["Transcript"]] = relationship(
        "Transcript", back_populates="call", uselist=False, cascade="all, delete-orphan"
    )
    analysis: Mapped[Optional["CallAnalysis"]] = relationship(
        "CallAnalysis", back_populates="call", uselist=False, cascade="all, delete-orphan"
    )
    recruitment_details: Mapped[Optional["RecruitmentDetails"]] = relationship(
        "RecruitmentDetails", back_populates="call", uselist=False, cascade="all, delete-orphan"
    )
    risk_events: Mapped[List["RiskEvent"]] = relationship(
        "RiskEvent", back_populates="call", cascade="all, delete-orphan"
    )
    decisions: Mapped[List["DecisionRecord"]] = relationship(
        "DecisionRecord", back_populates="call", cascade="all, delete-orphan"
    )
    notifications: Mapped[List["Notification"]] = relationship(
        "Notification", back_populates="call", cascade="all, delete-orphan"
    )
    actions: Mapped[List["CallAction"]] = relationship(
        "CallAction", back_populates="call", cascade="all, delete-orphan"
    )
    transcript_segments: Mapped[List["TranscriptSegment"]] = relationship(
        "TranscriptSegment", back_populates="call", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<Call id={self.id} status={self.status!r} "
            f"caller={self.caller_number!r} user_id={self.user_id}>"
        )


# ===========================================================================
# 3. call_participants
# ===========================================================================

class CallParticipant(Base):
    """A participant (caller, AI agent, or human operator) within a call."""

    __tablename__ = "call_participants"
    __table_args__ = (Index("ix_call_participants_call_id", "call_id"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_uuid, nullable=False
    )
    call_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("calls.id", ondelete="CASCADE"),
        nullable=False,
    )
    participant_type: Mapped[str] = mapped_column(String(30), nullable=False)
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=_now, nullable=False)
    left_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    call: Mapped["Call"] = relationship("Call", back_populates="participants")

    def __repr__(self) -> str:
        return (
            f"<CallParticipant id={self.id} call_id={self.call_id} "
            f"type={self.participant_type!r}>"
        )


# ===========================================================================
# 4. transcripts
# ===========================================================================

class Transcript(Base):
    """Full rolling transcript of a call, assembled from segments."""

    __tablename__ = "transcripts"
    __table_args__ = (
        UniqueConstraint("call_id", name="uq_transcripts_call_id"),
        Index("ix_transcripts_call_id", "call_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_uuid, nullable=False
    )
    call_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("calls.id", ondelete="CASCADE"),
        nullable=False,
    )
    full_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    word_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_now, onupdate=_now, nullable=False
    )

    # Relationships
    call: Mapped["Call"] = relationship("Call", back_populates="transcript")
    segments: Mapped[List["TranscriptSegment"]] = relationship(
        "TranscriptSegment", back_populates="transcript", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<Transcript id={self.id} call_id={self.call_id} "
            f"words={self.word_count}>"
        )


# ===========================================================================
# 5. transcript_segments
# ===========================================================================

class TranscriptSegment(Base):
    """An individual utterance within a call transcript."""

    __tablename__ = "transcript_segments"
    __table_args__ = (
        Index("ix_transcript_segments_transcript_id", "transcript_id"),
        Index("ix_transcript_segments_call_id", "call_id"),
        Index("ix_transcript_segments_speaker", "speaker"),
        Index("ix_transcript_segments_start_ms", "start_ms"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_uuid, nullable=False
    )
    transcript_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("transcripts.id", ondelete="CASCADE"),
        nullable=False,
    )
    call_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("calls.id", ondelete="CASCADE"),
        nullable=False,
    )
    speaker: Mapped[str] = mapped_column(String(20), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    start_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    end_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now, nullable=False)

    # Relationships
    transcript: Mapped["Transcript"] = relationship("Transcript", back_populates="segments")
    call: Mapped["Call"] = relationship("Call", back_populates="transcript_segments")

    def __repr__(self) -> str:
        snippet = (self.text or "")[:40]
        return (
            f"<TranscriptSegment id={self.id} speaker={self.speaker!r} "
            f"start_ms={self.start_ms} text={snippet!r}>"
        )


# ===========================================================================
# 6. call_analysis
# ===========================================================================

class CallAnalysis(Base):
    """AI-generated analysis record for a call (one-to-one with calls)."""

    __tablename__ = "call_analysis"
    __table_args__ = (
        UniqueConstraint("call_id", name="uq_call_analysis_call_id"),
        Index("ix_call_analysis_call_id", "call_id"),
        Index("ix_call_analysis_risk_level", "risk_level"),
        Index("ix_call_analysis_intent", "intent"),
        Index("ix_call_analysis_caller_type", "caller_type"),
        Index("ix_call_analysis_decision", "decision"),
        Index("ix_call_analysis_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_uuid, nullable=False
    )
    call_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("calls.id", ondelete="CASCADE"),
        nullable=False,
    )
    # Caller classification
    caller_type: Mapped[str] = mapped_column(
        String(20), default=CallerType.UNKNOWN.value, nullable=False
    )
    caller_type_confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Intent
    intent: Mapped[str] = mapped_column(
        String(30), default=Intent.UNKNOWN.value, nullable=False
    )
    secondary_intent: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    intent_confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Risk
    risk_level: Mapped[str] = mapped_column(
        String(20), default=RiskLevel.LOW.value, nullable=False
    )
    risk_confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    risk_indicators: Mapped[Any] = mapped_column(JSON, nullable=False, default=list)

    # Decision
    decision: Mapped[str] = mapped_column(
        String(30), default=Decision.AI_HANDLE.value, nullable=False
    )
    decision_reason: Mapped[str] = mapped_column(Text, nullable=False, default="")
    decision_confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Model versioning
    caller_model_version: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    intent_model_version: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    risk_model_version: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    analysis_latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_now, onupdate=_now, nullable=False
    )

    # Relationships
    call: Mapped["Call"] = relationship("Call", back_populates="analysis")

    def __repr__(self) -> str:
        return (
            f"<CallAnalysis id={self.id} call_id={self.call_id} "
            f"intent={self.intent!r} risk={self.risk_level!r} decision={self.decision!r}>"
        )


# ===========================================================================
# 7. recruitment_details
# ===========================================================================

class RecruitmentDetails(Base):
    """Structured data extracted from recruitment calls (one-to-one with calls)."""

    __tablename__ = "recruitment_details"
    __table_args__ = (
        UniqueConstraint("call_id", name="uq_recruitment_details_call_id"),
        Index("ix_recruitment_details_call_id", "call_id"),
        Index("ix_recruitment_details_extracted_at", "extracted_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_uuid, nullable=False
    )
    call_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("calls.id", ondelete="CASCADE"),
        nullable=False,
    )
    company: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    recruiter_name: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    position: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    interview_stage: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    interview_date: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    interview_time: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    next_step: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_legitimate: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    legitimacy_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    extracted_at: Mapped[datetime] = mapped_column(DateTime, default=_now, nullable=False)

    # Relationships
    call: Mapped["Call"] = relationship("Call", back_populates="recruitment_details")

    def __repr__(self) -> str:
        return (
            f"<RecruitmentDetails id={self.id} call_id={self.call_id} "
            f"company={self.company!r} position={self.position!r}>"
        )


# ===========================================================================
# 8. risk_events
# ===========================================================================

class RiskEvent(Base):
    """An individual risk signal detected during a call."""

    __tablename__ = "risk_events"
    __table_args__ = (
        Index("ix_risk_events_call_id", "call_id"),
        Index("ix_risk_events_severity", "severity"),
        Index("ix_risk_events_detected_at", "detected_at"),
        Index("ix_risk_events_call_severity", "call_id", "severity"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_uuid, nullable=False
    )
    call_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("calls.id", ondelete="CASCADE"),
        nullable=False,
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(
        String(20), default=RiskLevel.LOW.value, nullable=False
    )
    timestamp_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    detected_at: Mapped[datetime] = mapped_column(DateTime, default=_now, nullable=False)

    # Relationships
    call: Mapped["Call"] = relationship("Call", back_populates="risk_events")

    def __repr__(self) -> str:
        return (
            f"<RiskEvent id={self.id} call_id={self.call_id} "
            f"type={self.event_type!r} severity={self.severity!r}>"
        )


# ===========================================================================
# 9. decisions
# ===========================================================================

class DecisionRecord(Base):
    """Immutable audit trail of every AI decision made during a call."""

    __tablename__ = "decisions"
    __table_args__ = (
        Index("ix_decisions_call_id", "call_id"),
        Index("ix_decisions_risk_level", "risk_level"),
        Index("ix_decisions_intent", "intent"),
        Index("ix_decisions_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_uuid, nullable=False
    )
    call_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("calls.id", ondelete="CASCADE"),
        nullable=False,
    )
    decision: Mapped[str] = mapped_column(String(30), nullable=False)
    decision_reason: Mapped[str] = mapped_column(Text, nullable=False)
    caller_type: Mapped[str] = mapped_column(String(20), nullable=False)
    caller_type_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    intent: Mapped[str] = mapped_column(String(30), nullable=False)
    intent_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False)
    risk_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    risk_indicators: Mapped[Any] = mapped_column(JSON, nullable=False, default=list)
    decision_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    model_version: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now, nullable=False)

    # Relationships
    call: Mapped["Call"] = relationship("Call", back_populates="decisions")

    def __repr__(self) -> str:
        return (
            f"<DecisionRecord id={self.id} call_id={self.call_id} "
            f"decision={self.decision!r} risk={self.risk_level!r}>"
        )


# ===========================================================================
# 10. notifications
# ===========================================================================

class Notification(Base):
    """In-app / push notification sent to a user about a call event."""

    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_user_id", "user_id"),
        Index("ix_notifications_call_id", "call_id"),
        Index("ix_notifications_read", "read"),
        Index("ix_notifications_created_at", "created_at"),
        Index("ix_notifications_user_read", "user_id", "read"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_uuid, nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    call_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("calls.id", ondelete="SET NULL"),
        nullable=True,
    )
    notification_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="notifications")
    call: Mapped[Optional["Call"]] = relationship("Call", back_populates="notifications")

    def __repr__(self) -> str:
        return (
            f"<Notification id={self.id} user_id={self.user_id} "
            f"type={self.notification_type!r} read={self.read}>"
        )


# ===========================================================================
# 11. call_actions
# ===========================================================================

class CallAction(Base):
    """An action executed on a call (transfer, end, flag, etc.)."""

    __tablename__ = "call_actions"
    __table_args__ = (
        Index("ix_call_actions_call_id", "call_id"),
        Index("ix_call_actions_status", "status"),
        Index("ix_call_actions_created_at", "created_at"),
        Index("ix_call_actions_call_status", "call_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_uuid, nullable=False
    )
    call_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("calls.id", ondelete="CASCADE"),
        nullable=False,
    )
    action_type: Mapped[str] = mapped_column(String(30), nullable=False)
    initiated_by: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default=ActionStatus.PENDING.value, nullable=False
    )
    details: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    call: Mapped["Call"] = relationship("Call", back_populates="actions")

    def __repr__(self) -> str:
        return (
            f"<CallAction id={self.id} call_id={self.call_id} "
            f"type={self.action_type!r} status={self.status!r}>"
        )
