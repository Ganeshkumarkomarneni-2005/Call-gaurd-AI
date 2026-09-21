"""Call service — CRUD, status management, and dashboard aggregation."""

from __future__ import annotations

import json
from datetime import date
from typing import Any, Optional
from uuid import UUID

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.db.models import Call, CallAnalysis, Notification, Transcript
from backend.schemas.call import IncomingCallRequest
from backend.schemas.dashboard import DashboardStats
from backend.utils.time_utils import now_utc

logger: structlog.BoundLogger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


async def create_call(
    db: AsyncSession,
    data: IncomingCallRequest,
    user_id: Optional[UUID] = None,
) -> Call:
    """Create a new call record from an incoming telephony webhook.

    Args:
        db: Async database session.
        data: Validated incoming-call payload.
        user_id: Optional owner; resolved from virtual number mapping at the
            routing layer.

    Returns:
        The persisted :class:`Call` instance with ``status="ringing"``.
    """
    call = Call(
        user_id=user_id,
        status="ringing",
        caller_number=data.caller_number,
        virtual_number=data.virtual_number,
        telephony_call_id=data.telephony_call_id,
        telephony_provider=data.telephony_provider,
        started_at=now_utc(),
    )
    db.add(call)
    await db.flush()
    await db.refresh(call)
    logger.info(
        "Call created",
        call_id=str(call.id),
        caller=data.caller_number,
        virtual_number=data.virtual_number,
    )
    return call


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------


async def get_call(db: AsyncSession, call_id: UUID) -> Optional[Call]:
    """Fetch a call by primary key.

    Returns:
        :class:`Call` if found, else ``None``.
    """
    result = await db.execute(select(Call).where(Call.id == call_id))
    return result.scalar_one_or_none()


async def list_calls(
    db: AsyncSession,
    user_id: Optional[UUID] = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Call], int]:
    """Return a paginated list of calls, optionally filtered by owner.

    Args:
        db: Async database session.
        user_id: If provided, restrict to calls belonging to this user.
        page: 1-based page number.
        page_size: Rows per page (max 100).

    Returns:
        ``(calls, total_count)`` tuple.
    """
    page_size = min(page_size, 100)
    offset = (page - 1) * page_size

    base_q = select(Call)
    count_q = select(func.count()).select_from(Call)
    if user_id is not None:
        base_q = base_q.where(Call.user_id == user_id)
        count_q = count_q.where(Call.user_id == user_id)

    total = (await db.execute(count_q)).scalar_one()
    calls = list(
        (
            await db.execute(
                base_q.order_by(Call.created_at.desc()).offset(offset).limit(page_size)
            )
        )
        .scalars()
        .all()
    )
    return calls, total


async def get_call_with_details(db: AsyncSession, call_id: UUID) -> Optional[dict[str, Any]]:
    """Fetch a call with all related data eagerly loaded.

    Returns:
        A dict with keys ``call``, ``transcript``, ``analysis``,
        ``recruitment_details``, ``risk_events``, ``decisions``, ``actions``.
        Returns ``None`` if the call does not exist.
    """
    result = await db.execute(
        select(Call)
        .options(
            selectinload(Call.transcript).selectinload(Transcript.segments),
            selectinload(Call.analysis),
            selectinload(Call.recruitment_details),
        )
        .where(Call.id == call_id)
    )
    call = result.scalar_one_or_none()
    if call is None:
        return None

    return {
        "call": call,
        "transcript": call.transcript,
        "analysis": call.analysis,
        "recruitment_details": call.recruitment_details,
        "risk_events": [],   # populated by risk-event service in future wave
        "decisions": [],
        "actions": [],
    }


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------


async def update_call_status(
    db: AsyncSession,
    call_id: UUID,
    status: str,
) -> Optional[Call]:
    """Update the status of an existing call.

    Args:
        db: Async database session.
        call_id: Call to update.
        status: New status string (e.g. ``"active"``, ``"ended"``).

    Returns:
        Updated :class:`Call`, or ``None`` if not found.
    """
    call = await get_call(db, call_id)
    if call is None:
        return None
    call.status = status
    call.updated_at = now_utc()
    await db.flush()
    await db.refresh(call)
    logger.info("Call status updated", call_id=str(call_id), status=status)
    return call


async def end_call(db: AsyncSession, call_id: UUID) -> Optional[Call]:
    """Mark a call as ended, computing duration if possible.

    Returns:
        Updated :class:`Call`, or ``None`` if not found.
    """
    call = await get_call(db, call_id)
    if call is None:
        return None

    ended = now_utc()
    call.status = "ended"
    call.ended_at = ended
    if call.started_at:
        # Normalise both to naive UTC to avoid offset-aware vs offset-naive errors.
        # SQLite stores naive datetimes; now_utc() may return an aware datetime.
        ended_naive = ended.replace(tzinfo=None) if ended.tzinfo else ended
        started_naive = (
            call.started_at.replace(tzinfo=None)
            if call.started_at.tzinfo
            else call.started_at
        )
        delta = ended_naive - started_naive
        call.duration_seconds = max(0, int(delta.total_seconds()))
    call.updated_at = ended
    await db.flush()
    await db.refresh(call)
    logger.info("Call ended", call_id=str(call_id), duration=call.duration_seconds)
    return call


# ---------------------------------------------------------------------------
# Dashboard aggregation
# ---------------------------------------------------------------------------


async def get_dashboard_stats(
    db: AsyncSession,
    user_id: Optional[UUID] = None,
) -> DashboardStats:
    """Compute dashboard statistics, optionally scoped to a user.

    Args:
        db: Async database session.
        user_id: If provided, restrict stats to this user's calls.

    Returns:
        Populated :class:`DashboardStats` schema.
    """
    # --- total calls ---
    total_q = select(func.count()).select_from(Call)
    if user_id:
        total_q = total_q.where(Call.user_id == user_id)
    total_calls: int = (await db.execute(total_q)).scalar_one()

    # --- today's calls ---
    today = date.today()
    today_q = select(func.count()).select_from(Call).where(
        func.date(Call.created_at) == today
    )
    if user_id:
        today_q = today_q.where(Call.user_id == user_id)
    today_calls: int = (await db.execute(today_q)).scalar_one()

    # --- caller type distribution from analyses ---
    analysis_q = (
        select(CallAnalysis.caller_type, func.count().label("cnt"))
        .join(Call, Call.id == CallAnalysis.call_id)
        .group_by(CallAnalysis.caller_type)
    )
    if user_id:
        analysis_q = analysis_q.where(Call.user_id == user_id)
    caller_type_rows = (await db.execute(analysis_q)).all()
    caller_type_dist: dict[str, int] = {row.caller_type: row.cnt for row in caller_type_rows}

    # --- risk distribution ---
    risk_q = (
        select(CallAnalysis.risk_level, func.count().label("cnt"))
        .join(Call, Call.id == CallAnalysis.call_id)
        .group_by(CallAnalysis.risk_level)
    )
    if user_id:
        risk_q = risk_q.where(Call.user_id == user_id)
    risk_rows = (await db.execute(risk_q)).all()
    risk_dist: dict[str, int] = {row.risk_level: row.cnt for row in risk_rows}

    # --- intent distribution ---
    intent_q = (
        select(CallAnalysis.intent, func.count().label("cnt"))
        .join(Call, Call.id == CallAnalysis.call_id)
        .where(CallAnalysis.intent.isnot(None))
        .group_by(CallAnalysis.intent)
    )
    if user_id:
        intent_q = intent_q.where(Call.user_id == user_id)
    intent_rows = (await db.execute(intent_q)).all()
    intent_dist: dict[str, int] = {row.intent: row.cnt for row in intent_rows}

    # --- transferred / ai-handled ---
    transferred = (
        await db.execute(
            select(func.count())
            .select_from(Call)
            .where(Call.status == "transferred")
        )
    ).scalar_one()
    ai_handled = (
        await db.execute(
            select(func.count())
            .select_from(Call)
            .where(Call.status == "ai_handled")
        )
    ).scalar_one()

    return DashboardStats(
        total_calls=total_calls,
        today_calls=today_calls,
        ai_callers=caller_type_dist.get("ai", 0),
        human_callers=caller_type_dist.get("human", 0),
        robocalls=caller_type_dist.get("robocall", 0),
        unknown_callers=caller_type_dist.get("unknown", 0),
        recruitment_calls=intent_dist.get("recruitment", 0),
        promotional_calls=intent_dist.get("promotional", 0),
        fraud_calls=intent_dist.get("fraud", 0),
        transferred_calls=transferred,
        ai_handled_calls=ai_handled,
        risk_distribution=risk_dist,
        intent_distribution=intent_dist,
        caller_type_distribution=caller_type_dist,
    )
