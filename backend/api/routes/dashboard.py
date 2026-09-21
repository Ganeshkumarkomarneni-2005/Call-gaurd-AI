"""Dashboard routes — aggregate statistics and recent activity."""

from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.security import get_current_user
from backend.db.models import User
from backend.db.session import get_db
from backend.schemas.call import CallListResponse, CallResponse
from backend.schemas.dashboard import DashboardStats
from backend.services import call_service

logger: structlog.BoundLogger = structlog.get_logger(__name__)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get(
    "/statistics",
    response_model=DashboardStats,
    summary="Get aggregated dashboard statistics",
)
async def get_statistics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DashboardStats:
    """Return aggregated call and analysis statistics for the dashboard.

    Statistics are scoped to the authenticated user unless the user is an
    admin, in which case all calls are included.
    """
    user_id = None if current_user.is_admin else current_user.id
    stats = await call_service.get_dashboard_stats(db, user_id=user_id)
    logger.info("Dashboard stats requested", user_id=str(current_user.id))
    return stats


@router.get(
    "/recent-calls",
    response_model=CallListResponse,
    summary="Get the 10 most recent calls",
)
async def recent_calls(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CallListResponse:
    """Return the 10 most recent calls for the authenticated user."""
    user_id = None if current_user.is_admin else current_user.id
    calls, total = await call_service.list_calls(
        db, user_id=user_id, page=1, page_size=10
    )
    return CallListResponse(
        calls=[CallResponse.model_validate(c) for c in calls],
        total=total,
        page=1,
        page_size=10,
    )


@router.get(
    "/risk-summary",
    summary="Get risk level breakdown",
)
async def risk_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return the count of calls per risk level for charting."""
    user_id = None if current_user.is_admin else current_user.id
    stats = await call_service.get_dashboard_stats(db, user_id=user_id)
    return {
        "risk_distribution": stats.risk_distribution,
        "total_calls": stats.total_calls,
    }
