"""Telephony webhook routes for Exotel and Twilio."""

from __future__ import annotations

from typing import Any, Optional
import structlog
from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models import Call, User
from backend.db.session import get_db
from backend.services.notification_service import create_notification
from backend.utils.time_utils import now_utc

logger: structlog.BoundLogger = structlog.get_logger(__name__)

router = APIRouter(prefix="/telephony", tags=["telephony"])


@router.api_route("/webhook", methods=["GET", "POST"], summary="Incoming telephony webhook")
async def telephony_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Handle incoming call webhook from Exotel or Twilio.
    
    Accepts both GET and POST requests sent by Exotel's Passthru applet or Twilio voice webhook.
    """
    params: dict[str, Any] = {}
    if request.method == "POST":
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            try:
                params = await request.json()
            except Exception:
                params = {}
        else:
            form = await request.form()
            params = dict(form)
    else:
        params = dict(request.query_params)

    logger.info("Incoming telephony webhook received", params=params)

    # Extract standard fields (Exotel uses CallSid, From, To; Twilio uses CallSid, From, To)
    call_sid = params.get("CallSid") or params.get("CallUUID") or params.get("call_sid") or "unknown"
    caller_number = params.get("From") or params.get("Caller") or params.get("caller") or "Unknown Caller"
    virtual_number = params.get("To") or params.get("Called") or params.get("virtual_number") or ""

    # Find the primary active user to assign the call to
    user_result = await db.execute(select(User).order_by(User.created_at.asc()).limit(1))
    user = user_result.scalars().first()

    if user:
        # Create Call record in DB
        new_call = Call(
            user_id=user.id,
            status="active",
            caller_number=str(caller_number),
            caller_name="Exotel Incoming Caller",
            virtual_number=str(virtual_number),
            telephony_call_id=str(call_sid),
            telephony_provider="exotel",
            started_at=now_utc(),
        )
        db.add(new_call)
        await db.commit()
        await db.refresh(new_call)

        # Dispatch immediate Telegram & SMS notification to user
        await create_notification(
            db=db,
            user_id=user.id,
            notification_type="call_incoming",
            title="📞 Incoming Call via Exotel",
            body=f"Incoming screened call from {caller_number} on {virtual_number}.",
            call_id=new_call.id,
        )

    # Return standard 200 OK so Exotel Passthru proceeds smoothly
    return Response(content="OK", media_type="text/plain", status_code=status.HTTP_200_OK)
