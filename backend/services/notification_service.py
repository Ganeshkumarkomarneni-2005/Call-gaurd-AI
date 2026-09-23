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


import os
import httpx

async def send_telegram_alert(title: str, body: str, call_id: Optional[UUID] = None) -> bool:
    """Send an instant formatted alert to Telegram."""
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not bot_token or not chat_id:
        return False

    message_text = (
        f"🛡️ *CallGuard AI Alert*\n\n"
        f"*{title}*\n"
        f"{body}\n"
    )
    if call_id:
        message_text += f"\n🔍 *Call ID*: `{str(call_id)[:8]}`"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"https://api.telegram.org/bot{bot_token}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": message_text,
                    "parse_mode": "Markdown",
                },
            )
            return resp.status_code == 200
    except Exception as exc:
        logger.warning("Failed to send Telegram alert", error=str(exc))
        return False


async def send_sms_alert(title: str, body: str, to_number: Optional[str] = None) -> bool:
    """Send an SMS alert via Exotel."""
    sid = os.environ.get("EXOTEL_SID")
    api_key = os.environ.get("EXOTEL_API_KEY") or sid
    token = os.environ.get("EXOTEL_TOKEN")
    from_num = os.environ.get("EXOTEL_FROM_NUMBER")
    recipient = to_number or os.environ.get("USER_ALERT_PHONE_NUMBER")

    if not all([sid, token, from_num, recipient]):
        return False

    sms_url = f"https://api.exotel.com/v1/Accounts/{sid}/Sms/send.json"
    sms_body = f"CallGuard Alert: {title} - {body}"[:150]

    try:
        async with httpx.AsyncClient(auth=(api_key, token), timeout=10.0) as client:
            resp = await client.post(
                sms_url,
                data={
                    "From": from_num,
                    "To": recipient,
                    "Body": sms_body,
                },
            )
            return resp.status_code in (200, 201)
    except Exception as exc:
        logger.warning("Failed to send SMS alert", error=str(exc))
        return False


async def create_notification(
    db: AsyncSession,
    user_id: UUID,
    notification_type: str,
    title: str,
    body: str,
    call_id: Optional[UUID] = None,
) -> Notification:
    """Create and persist a new notification and dispatch external alerts."""
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

    # Dispatch to Telegram and SMS in background
    try:
        await send_telegram_alert(title, body, call_id)
        await send_sms_alert(title, body)
    except Exception as e:
        logger.warning("External alert dispatch failed", error=str(e))

    logger.info(
        "Notification created and dispatched",
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
