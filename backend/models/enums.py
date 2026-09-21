"""Domain enumerations used across models, schemas, and business logic."""
from __future__ import annotations

from enum import Enum


class CallerType(str, Enum):
    """Classification of the entity that placed the call."""

    HUMAN = "HUMAN"
    AI = "AI"
    ROBOCALL = "ROBOCALL"
    UNKNOWN = "UNKNOWN"


class Intent(str, Enum):
    """High-level intent inferred from the call content."""

    RECRUITMENT = "RECRUITMENT"
    PROMOTIONAL = "PROMOTIONAL"
    FRAUD = "FRAUD"
    CUSTOMER_SERVICE = "CUSTOMER_SERVICE"
    DELIVERY = "DELIVERY"
    PERSONAL = "PERSONAL"
    OTHER = "OTHER"
    UNKNOWN = "UNKNOWN"


class RiskLevel(str, Enum):
    """Assessed risk level for a call."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Decision(str, Enum):
    """Action the AI agent decided to take for a call."""

    AI_HANDLE = "AI_HANDLE"
    NOTIFY = "NOTIFY"
    TRANSFER = "TRANSFER"
    END = "END"
    FLAG_FOR_REVIEW = "FLAG_FOR_REVIEW"


class CallStatus(str, Enum):
    """Lifecycle status of a call."""

    RINGING = "RINGING"
    ACTIVE = "ACTIVE"
    ENDED = "ENDED"
    TRANSFERRED = "TRANSFERRED"
    FAILED = "FAILED"


class InterviewStage(str, Enum):
    """Stage of a recruitment interview process."""

    INITIAL = "INITIAL"
    TECHNICAL = "TECHNICAL"
    HR = "HR"
    FINAL = "FINAL"
    UNKNOWN = "UNKNOWN"


class ActionType(str, Enum):
    """Type of action taken on a call."""

    TRANSFER = "TRANSFER"
    END = "END"
    FLAG = "FLAG"
    CONTINUE = "CONTINUE"
    NOTIFY = "NOTIFY"


class ActionStatus(str, Enum):
    """Execution status of a call action."""

    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class InitiatedBy(str, Enum):
    """Who triggered a call action."""

    AGENT = "AGENT"
    USER = "USER"
    SYSTEM = "SYSTEM"


class Speaker(str, Enum):
    """Speaker role in a transcript segment."""

    CALLER = "CALLER"
    AGENT = "AGENT"


class ParticipantType(str, Enum):
    """Type of participant in a call."""

    CALLER = "CALLER"
    AGENT = "AGENT"
    HUMAN_OPERATOR = "HUMAN_OPERATOR"


class NotificationType(str, Enum):
    """Category of in-app notification."""

    RECRUITMENT_DETECTED = "RECRUITMENT_DETECTED"
    FRAUD_DETECTED = "FRAUD_DETECTED"
    HIGH_RISK = "HIGH_RISK"
    TRANSFER_REQUESTED = "TRANSFER_REQUESTED"
    UNKNOWN_CALLER = "UNKNOWN_CALLER"
    CALL_ENDED = "CALL_ENDED"
    CALL_STARTED = "CALL_STARTED"


class Severity(str, Enum):
    """Severity rating for risk and fraud indicators."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class FraudIndicatorType(str, Enum):
    """Categories of fraud signals detected during conversation."""

    OTP_REQUEST = "OTP_REQUEST"
    PAYMENT_REQUEST = "PAYMENT_REQUEST"
    CREDENTIAL_REQUEST = "CREDENTIAL_REQUEST"
    URGENCY = "URGENCY"
    IMPERSONATION = "IMPERSONATION"
    THREAT = "THREAT"
    SENSITIVE_PII = "SENSITIVE_PII"
    SUSPICIOUS_LINK = "SUSPICIOUS_LINK"
    JOB_REGISTRATION_FEE = "JOB_REGISTRATION_FEE"
    GENERAL = "GENERAL"


