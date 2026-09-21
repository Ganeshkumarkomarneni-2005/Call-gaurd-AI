"""Call management routes."""

from __future__ import annotations

import asyncio
import json
from typing import Optional
from uuid import UUID

import structlog
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.security import get_current_user
from backend.db.models import User
from backend.db.session import get_db
from backend.schemas.call import (
    CallDetailResponse,
    CallListResponse,
    CallResponse,
    IncomingCallRequest,
    TranscriptResponse,
    TransferRequest,
)
from backend.services import call_service

logger: structlog.BoundLogger = structlog.get_logger(__name__)

router = APIRouter(prefix="/calls", tags=["calls"])


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _call_or_404(call) -> None:  # noqa: ANN001
    if call is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Call not found"
        )


async def _trigger_ai_pipeline(call_id: str) -> None:
    """Placeholder for the async AI analysis pipeline.

    In a production deployment this would enqueue a Celery task or publish
    to a message broker.  For now, it is a no-op coroutine that avoids
    blocking the HTTP response.
    """
    logger.info("AI analysis pipeline triggered", call_id=call_id)
    await asyncio.sleep(0)  # yield control


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/incoming",
    response_model=CallResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record an incoming call and trigger AI analysis",
)
async def incoming_call(
    payload: IncomingCallRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> CallResponse:
    """Create a call record when a new call arrives from the telephony provider.

    The AI analysis pipeline is triggered as a background task so the
    telephony webhook receives an immediate ``201`` response.
    """
    call = await call_service.create_call(db, payload)
    background_tasks.add_task(_trigger_ai_pipeline, str(call.id))
    logger.info("Incoming call recorded", call_id=str(call.id))
    return CallResponse.model_validate(call)


@router.get(
    "",
    response_model=CallListResponse,
    summary="List calls (paginated)",
)
async def list_calls(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CallListResponse:
    """Return a paginated list of calls belonging to the authenticated user."""
    calls, total = await call_service.list_calls(
        db, user_id=current_user.id, page=page, page_size=page_size
    )
    return CallListResponse(
        calls=[CallResponse.model_validate(c) for c in calls],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{call_id}",
    response_model=CallDetailResponse,
    summary="Get full call details",
)
async def get_call(
    call_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CallDetailResponse:
    """Return the full detail view of a call including transcript and analysis."""
    details = await call_service.get_call_with_details(db, call_id)
    if details is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Call not found"
        )
    call = details["call"]
    # Ownership check (admins can see all)
    if not current_user.is_admin and call.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )
    return CallDetailResponse(
        call=CallResponse.model_validate(call),
        transcript=details["transcript"],
        analysis=details["analysis"],
        recruitment_details=details["recruitment_details"],
        risk_events=details["risk_events"],
        decisions=details["decisions"],
        actions=details["actions"],
    )


@router.get(
    "/{call_id}/transcript",
    response_model=Optional[TranscriptResponse],
    summary="Get call transcript",
)
async def get_transcript(
    call_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Optional[TranscriptResponse]:
    """Return the transcript of the specified call."""
    details = await call_service.get_call_with_details(db, call_id)
    if details is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Call not found"
        )
    transcript = details["transcript"]
    if transcript is None:
        return None
    return TranscriptResponse.model_validate(transcript)


@router.get(
    "/{call_id}/summary",
    summary="Get call transcript summary",
)
async def get_summary(
    call_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return the AI-generated summary for a call transcript."""
    details = await call_service.get_call_with_details(db, call_id)
    if details is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Call not found"
        )
    transcript = details["transcript"]
    return {
        "call_id": str(call_id),
        "summary": transcript.summary if transcript else None,
    }


@router.get(
    "/{call_id}/analysis",
    summary="Get call AI analysis",
)
async def get_analysis(
    call_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return the AI analysis results for the specified call."""
    details = await call_service.get_call_with_details(db, call_id)
    if details is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Call not found"
        )
    analysis = details["analysis"]
    if analysis is None:
        return {"call_id": str(call_id), "analysis": None}

    # Deserialise risk_indicators stored as JSON string
    risk_indicators = []
    try:
        risk_indicators = json.loads(analysis.risk_indicators or "[]")
    except (json.JSONDecodeError, TypeError):
        pass

    return {
        "call_id": str(call_id),
        "caller_type": analysis.caller_type,
        "caller_type_confidence": analysis.caller_type_confidence,
        "intent": analysis.intent,
        "risk_level": analysis.risk_level,
        "risk_indicators": risk_indicators,
        "decision": analysis.decision,
    }


@router.post(
    "/{call_id}/transfer",
    summary="Transfer call to human agent",
)
async def transfer_call(
    call_id: UUID,
    payload: TransferRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Initiate a transfer of the call to a human agent.

    Updates call status to ``"transferring"`` and records the destination.
    """
    call = await call_service.get_call(db, call_id)
    _call_or_404(call)
    updated = await call_service.update_call_status(db, call_id, "transferring")
    logger.info(
        "Call transfer initiated",
        call_id=str(call_id),
        destination=payload.destination_number,
    )
    return {
        "call_id": str(call_id),
        "status": updated.status,
        "destination_number": payload.destination_number,
        "agent_notes": payload.agent_notes,
        "message": "Transfer initiated",
    }


@router.post(
    "/{call_id}/continue",
    summary="Continue AI handling of call",
)
async def continue_call(
    call_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Resume AI handling for a call that was paused or flagged for review."""
    call = await call_service.get_call(db, call_id)
    _call_or_404(call)
    updated = await call_service.update_call_status(db, call_id, "active")
    logger.info("Call continued by AI", call_id=str(call_id))
    return {"call_id": str(call_id), "status": updated.status}


@router.post(
    "/{call_id}/end",
    response_model=CallResponse,
    summary="End an active call",
)
async def end_call(
    call_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CallResponse:
    """Mark a call as ended and compute its duration.

    Raises:
        HTTPException: 404 if the call does not exist.
    """
    call = await call_service.end_call(db, call_id)
    _call_or_404(call)
    logger.info("Call ended via API", call_id=str(call_id))
    return CallResponse.model_validate(call)
