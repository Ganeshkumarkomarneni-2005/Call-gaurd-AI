"""Pydantic schemas for dashboard statistics and notifications."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel


class DashboardStats(BaseModel):
    """Aggregated statistics shown on the dashboard."""

    total_calls: int = 0
    today_calls: int = 0
    ai_callers: int = 0
    human_callers: int = 0
    robocalls: int = 0
    unknown_callers: int = 0
    recruitment_calls: int = 0
    promotional_calls: int = 0
    fraud_calls: int = 0
    transferred_calls: int = 0
    ai_handled_calls: int = 0
    risk_distribution: Dict[str, int] = {}
    intent_distribution: Dict[str, int] = {}
    caller_type_distribution: Dict[str, int] = {}


class NotificationResponse(BaseModel):
    """Single notification record."""

    id: UUID
    call_id: Optional[UUID] = None
    notification_type: str
    title: str
    body: str
    read: bool
    read_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationListResponse(BaseModel):
    """Paginated notification list with unread count."""

    notifications: List[NotificationResponse]
    unread_count: int
    total: int
