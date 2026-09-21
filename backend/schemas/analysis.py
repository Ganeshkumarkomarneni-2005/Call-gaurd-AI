"""Pydantic schemas for AI agent inputs and outputs."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Shared input types
# ---------------------------------------------------------------------------


class ConversationTurn(BaseModel):
    """A single speaker turn in a conversation."""

    speaker: str = Field(..., description="'agent' or 'caller'")
    text: str
    timestamp_ms: int = Field(..., ge=0, description="Offset from call start in ms")


class ClassificationInput(BaseModel):
    """Input sent to AI classification agents."""

    call_id: UUID
    conversation: List[ConversationTurn]
    audio_features: Optional[Dict[str, Any]] = None


# ---------------------------------------------------------------------------
# Caller classification
# ---------------------------------------------------------------------------


class CallerClassificationResult(BaseModel):
    """Result from the caller-type classifier."""

    caller_type: str = Field(
        ..., description="human | ai | robocall | unknown"
    )
    confidence: float = Field(..., ge=0.0, le=1.0)
    evidence: List[str] = Field(default_factory=list)
    model_version: str


# ---------------------------------------------------------------------------
# Intent classification
# ---------------------------------------------------------------------------


class IntentClassificationResult(BaseModel):
    """Result from the intent classifier."""

    intent: str
    secondary_intent: Optional[str] = None
    confidence: float = Field(..., ge=0.0, le=1.0)
    evidence: List[str] = Field(default_factory=list)
    model_version: str


# ---------------------------------------------------------------------------
# Risk assessment
# ---------------------------------------------------------------------------


class RiskIndicator(BaseModel):
    """A single risk signal detected in the call."""

    indicator_type: str
    description: str
    severity: str = Field(..., description="low | medium | high | critical")
    confidence: float = Field(..., ge=0.0, le=1.0)


class RiskAssessmentResult(BaseModel):
    """Result from the risk-assessment agent."""

    risk_level: str = Field(..., description="low | medium | high | critical")
    confidence: float = Field(..., ge=0.0, le=1.0)
    indicators: List[RiskIndicator] = Field(default_factory=list)
    explanation: str


# ---------------------------------------------------------------------------
# Recruitment extraction
# ---------------------------------------------------------------------------


class RecruitmentExtractionResult(BaseModel):
    """Structured data extracted from a recruitment call."""

    company: Optional[str] = None
    recruiter_name: Optional[str] = None
    position: Optional[str] = None
    interview_stage: Optional[str] = None
    interview_date: Optional[str] = None
    interview_time: Optional[str] = None
    next_step: Optional[str] = None
    is_legitimate: bool = True
    legitimacy_reason: Optional[str] = None
    confidence: float = Field(..., ge=0.0, le=1.0)


# ---------------------------------------------------------------------------
# Decision
# ---------------------------------------------------------------------------


class DecisionResult(BaseModel):
    """Final handling decision produced by the decision agent."""

    decision: str = Field(
        ...,
        description="continue_ai | transfer_human | block | end_call",
    )
    reason: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    caller_type: str
    intent: Optional[str] = None
    risk_level: str
    requires_human_review: bool = False


# ---------------------------------------------------------------------------
# Handoff summary
# ---------------------------------------------------------------------------


class HandoffSummary(BaseModel):
    """Summary sent to the human agent when a call is transferred."""

    call_id: UUID
    caller_type: str
    intent: Optional[str] = None
    risk_level: str
    company: Optional[str] = None
    position: Optional[str] = None
    conversation_summary: str
    recommended_action: str
