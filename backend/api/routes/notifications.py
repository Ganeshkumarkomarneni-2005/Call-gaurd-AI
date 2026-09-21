"""Notification routes — list, mark read, mark all read."""

from __future__ import annotations

from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.security import get_current_user
from backend.db.models import User
from backend.db.session import get_db
from backend.schemas.dashboard import NotificationListResponse, NotificationResponse
from backend.services import notification_service

logger: structlog.BoundLogger = structlog.get_logger(__name__)

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get(
    "",
    response_model=NotificationListResponse,
    summary="List user notifications (paginated)",
)
async def list_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> NotificationListResponse:
    """Return a paginated list of notifications for the authenticated user."""
    notifications, total = await notification_service.get_user_notifications(
        db, user_id=current_user.id, page=page, page_size=page_size
    )
    unread = sum(1 for n in notifications if not n.read)
    return NotificationListResponse(
        notifications=[NotificationResponse.model_validate(n) for n in notifications],
        unread_count=unread,
        total=total,
    )


@router.post(
    "/{notification_id}/read",
    summary="Mark a single notification as read",
)
async def mark_notification_read(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Mark the specified notification as read.

    Raises:
        HTTPException: 404 if the notification is not found or not owned by the user.
    """
    updated = await notification_service.mark_read(
        db, notification_id=notification_id, user_id=current_user.id
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found or already read",
        )
    return {"notification_id": str(notification_id), "read": True}


@router.post(
    "/read-all",
    summary="Mark all notifications as read",
)
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Mark every unread notification for the authenticated user as read."""
    count = await notification_service.mark_all_read(db, user_id=current_user.id)
    logger.info(
        "All notifications marked read", user_id=str(current_user.id), count=count
    )
    return {"marked_read": count}
