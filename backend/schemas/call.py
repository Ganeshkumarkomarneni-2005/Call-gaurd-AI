"""Pydantic schemas for call-related endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Incoming call request
# ---------------------------------------------------------------------------


class IncomingCallRequest(BaseModel):
    """Payload posted by the telephony provider when a call arrives."""

    caller_number: str = Field(..., description="E.164 caller phone number")
    virtual_number: str = Field(..., description="Virtual/DID number that was called")
    telephony_call_id: str = Field(..., description="Provider-assigned call identifier")
    telephony_provider: str = Field(
        default="twilio", description="Telephony provider name"
    )


# ---------------------------------------------------------------------------
# Call
# ---------------------------------------------------------------------------


class CallResponse(BaseModel):
    """Summary of a single call record."""

    id: UUID
    user_id: Optional[UUID] = None
    status: str
    caller_number: str
    caller_name: Optional[str] = None
    virtual_number: str
    telephony_provider: str
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CallListResponse(BaseModel):
    """Paginated list of calls."""

    calls: List[CallResponse]
    total: int
    page: int
    page_size: int


# ---------------------------------------------------------------------------
# Transcript
# ---------------------------------------------------------------------------


class TranscriptSegmentResponse(BaseModel):
    """A single utterance in the call transcript."""

    id: UUID
    speaker: str
    text: str
    start_ms: int
    end_ms: int
    confidence: float

    model_config = {"from_attributes": True}


class TranscriptResponse(BaseModel):
    """Full transcript of a call."""

    id: UUID
    call_id: UUID
    full_text: str
    summary: Optional[str] = None
    segments: List[TranscriptSegmentResponse] = []
    word_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------


class CallAnalysisResponse(BaseModel):
    """AI analysis results for a call."""

    id: UUID
    call_id: UUID
    caller_type: str
    caller_type_confidence: float
    intent: Optional[str] = None
    secondary_intent: Optional[str] = None
    intent_confidence: float
    risk_level: str
    risk_confidence: float
    risk_indicators: List[str] = []
    decision: str
    decision_reason: Optional[str] = None
    decision_confidence: float
    analysis_latency_ms: Optional[int] = None
    created_at: datetime

    @field_validator("risk_indicators", mode="before")
    @classmethod
    def parse_risk_indicators(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            try:
                import json
                parsed = json.loads(v)
                return parsed if isinstance(parsed, list) else [str(parsed)]
            except Exception:
                return [v] if v else []
        return v or []

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Recruitment
# ---------------------------------------------------------------------------


class RecruitmentDetailsResponse(BaseModel):
    """Structured recruitment details extracted from a call."""

    id: UUID
    call_id: UUID
    company: Optional[str] = None
    recruiter_name: Optional[str] = None
    position: Optional[str] = None
    interview_stage: Optional[str] = None
    interview_date: Optional[str] = None
    interview_time: Optional[str] = None
    next_step: Optional[str] = None
    is_legitimate: bool
    legitimacy_reason: Optional[str] = None
    extracted_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Detailed call view (joined)
# ---------------------------------------------------------------------------


class CallDetailResponse(BaseModel):
    """Full detail of a call including all related data."""

    call: CallResponse
    transcript: Optional[TranscriptResponse] = None
    analysis: Optional[CallAnalysisResponse] = None
    recruitment_details: Optional[RecruitmentDetailsResponse] = None
    risk_events: List[Dict[str, Any]] = []
    decisions: List[Dict[str, Any]] = []
    actions: List[Dict[str, Any]] = []


# ---------------------------------------------------------------------------
# Transfer
# ---------------------------------------------------------------------------


class TransferRequest(BaseModel):
    """Request body for initiating a human transfer."""

    destination_number: str = Field(
        ..., description="E.164 phone number to transfer to"
    )
    agent_notes: Optional[str] = Field(
        None, max_length=1024, description="Context notes for the receiving agent"
    )
