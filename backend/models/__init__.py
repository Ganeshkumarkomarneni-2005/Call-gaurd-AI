"""Models package.

Imports all ORM models so that SQLAlchemy can discover them when
``Base.metadata.create_all()`` or Alembic ``env.py`` imports this package.
"""
from __future__ import annotations

from backend.models.database import Base, get_db, get_sync_db, init_db, close_db  # noqa: F401
from backend.models.enums import (  # noqa: F401
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
from backend.models.tables import (  # noqa: F401
    Call,
    CallAction,
    CallAnalysis,
    CallParticipant,
    DecisionRecord,
    Notification,
    RecruitmentDetails,
    RiskEvent,
    Transcript,
    TranscriptSegment,
    User,
)

__all__ = [
    # Database helpers
    "Base",
    "get_db",
    "get_sync_db",
    "init_db",
    "close_db",
    # Enums
    "ActionStatus",
    "ActionType",
    "CallerType",
    "CallStatus",
    "Decision",
    "InitiatedBy",
    "Intent",
    "InterviewStage",
    "NotificationType",
    "ParticipantType",
    "RiskLevel",
    "Speaker",
    # ORM Models
    "Call",
    "CallAction",
    "CallAnalysis",
    "CallParticipant",
    "DecisionRecord",
    "Notification",
    "RecruitmentDetails",
    "RiskEvent",
    "Transcript",
    "TranscriptSegment",
    "User",
]
