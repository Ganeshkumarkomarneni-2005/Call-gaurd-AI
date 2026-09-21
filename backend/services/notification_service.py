"""Notification service — create, query, and mark-read operations."""

from __future__ import annotations

from typing import Optional
from uuid import UUID

import structlog
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models import Notification
from backend.utils.time_utils import now_utc

logger: structlog.BoundLogger = structlog.get_logger(__name__)


async def create_notification(
    db: AsyncSession,
    user_id: UUID,
    notification_type: str,
    title: str,
    body: str,
    call_id: Optional[UUID] = None,
) -> Notification:
    """Create and persist a new notification.

    Args:
        db: Async database session.
        user_id: Recipient user identifier.
        notification_type: Category string (e.g. ``"call_alert"``).
        title: Short notification title.
        body: Full notification body text.
        call_id: Optional associated call identifier.

    Returns:
        The persisted :class:`Notification` instance.
    """
    notification = Notification(
        user_id=user_id,
        call_id=call_id,
        notification_type=notification_type,
        title=title,
        body=body,
    )
    db.add(notification)
    await db.flush()
    await db.refresh(notification)
    logger.info(
        "Notification created",
        notification_id=str(notification.id),
        user_id=str(user_id),
        type=notification_type,
    )
    return notification


async def get_user_notifications(
    db: AsyncSession,
    user_id: UUID,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Notification], int]:
    """Return a paginated list of notifications for a user.

    Args:
        db: Async database session.
        user_id: Target user.
        page: 1-based page number.
        page_size: Items per page.

    Returns:
        A ``(notifications, total_count)`` tuple.
    """
    offset = (page - 1) * page_size

    count_result = await db.execute(
        select(func.count()).select_from(Notification).where(Notification.user_id == user_id)
    )
    total = count_result.scalar_one()

    result = await db.execute(
        select(Notification)
        .where(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    notifications = list(result.scalars().all())
    return notifications, total


async def mark_read(
    db: AsyncSession,
    notification_id: UUID,
    user_id: UUID,
) -> bool:
    """Mark a single notification as read.

    Args:
        db: Async database session.
        notification_id: The notification to update.
        user_id: Owning user (for ownership check).

    Returns:
        ``True`` if updated, ``False`` if not found / not owned.
    """
    result = await db.execute(
        update(Notification)
        .where(
            Notification.id == notification_id,
            Notification.user_id == user_id,
            Notification.read.is_(False),
        )
        .values(read=True, read_at=now_utc())
        .returning(Notification.id)
    )
    updated = result.scalar_one_or_none()
    if updated:
        logger.info("Notification marked read", notification_id=str(notification_id))
    return updated is not None


async def mark_all_read(db: AsyncSession, user_id: UUID) -> int:
    """Mark every unread notification for *user_id* as read.

    Returns:
        Number of notifications updated.
    """
    result = await db.execute(
        update(Notification)
        .where(
            Notification.user_id == user_id,
            Notification.read.is_(False),
        )
        .values(read=True, read_at=now_utc())
        .returning(Notification.id)
    )
    count = len(result.fetchall())
    logger.info("All notifications marked read", user_id=str(user_id), count=count)
    return count
