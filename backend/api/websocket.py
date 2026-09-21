"""WebSocket handler for real-time call and notification events.

Supported event types
----------------------
- call.started          — new call began
- call.audio            — audio chunk / stream update
- transcript.updated    — new transcript segment
- caller.type.detected  — AI classified the caller
- intent.detected       — intent identified
- risk.updated          — risk level changed
- recruitment.detected  — recruitment data extracted
- notification.created  — new user notification
- transfer.requested    — human transfer requested
- transfer.completed    — transfer completed
- call.ended            — call finished
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, List, Optional
from uuid import UUID

import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger: structlog.BoundLogger = structlog.get_logger(__name__)

router = APIRouter(tags=["websocket"])


# ---------------------------------------------------------------------------
# Connection Manager
# ---------------------------------------------------------------------------


class ConnectionManager:
    """Manages WebSocket connections, grouped by call_id and user_id."""

    def __init__(self) -> None:
        # call_id -> list of active WebSocket connections
        self._call_connections: Dict[str, List[WebSocket]] = {}
        # user_id -> list of active WebSocket connections
        self._user_connections: Dict[str, List[WebSocket]] = {}

    # ------------------------------------------------------------------
    # Call-level connections
    # ------------------------------------------------------------------

    async def connect_to_call(self, call_id: str, websocket: WebSocket) -> None:
        """Accept a new connection and register it under *call_id*."""
        await websocket.accept()
        self._call_connections.setdefault(call_id, []).append(websocket)
        logger.info("WS client connected to call", call_id=call_id)

    def disconnect_from_call(self, call_id: str, websocket: WebSocket) -> None:
        """Remove *websocket* from the call bucket."""
        bucket = self._call_connections.get(call_id, [])
        try:
            bucket.remove(websocket)
        except ValueError:
            pass
        if not bucket:
            self._call_connections.pop(call_id, None)
        logger.info("WS client disconnected from call", call_id=call_id)

    async def send_to_call(
        self, call_id: str, event_type: str, data: Dict[str, Any]
    ) -> None:
        """Broadcast an event to all connections watching *call_id*."""
        message = json.dumps({"event": event_type, "data": data})
        stale: List[WebSocket] = []
        for ws in list(self._call_connections.get(call_id, [])):
            try:
                await ws.send_text(message)
            except Exception:  # noqa: BLE001
                stale.append(ws)
        for ws in stale:
            self.disconnect_from_call(call_id, ws)

    # ------------------------------------------------------------------
    # User-level connections (notifications)
    # ------------------------------------------------------------------

    async def connect_user(self, user_id: str, websocket: WebSocket) -> None:
        """Accept and register a notification connection for *user_id*."""
        await websocket.accept()
        self._user_connections.setdefault(user_id, []).append(websocket)
        logger.info("WS client connected for notifications", user_id=user_id)

    def disconnect_user(self, user_id: str, websocket: WebSocket) -> None:
        """Remove *websocket* from the user notification bucket."""
        bucket = self._user_connections.get(user_id, [])
        try:
            bucket.remove(websocket)
        except ValueError:
            pass
        if not bucket:
            self._user_connections.pop(user_id, None)
        logger.info("WS client disconnected from notifications", user_id=user_id)

    async def send_to_user(
        self, user_id: str, event_type: str, data: Dict[str, Any]
    ) -> None:
        """Send a notification event to all connections for *user_id*."""
        message = json.dumps({"event": event_type, "data": data})
        stale: List[WebSocket] = []
        for ws in list(self._user_connections.get(user_id, [])):
            try:
                await ws.send_text(message)
            except Exception:  # noqa: BLE001
                stale.append(ws)
        for ws in stale:
            self.disconnect_user(user_id, ws)

    async def broadcast(self, event_type: str, data: Dict[str, Any]) -> None:
        """Broadcast an event to every connected WebSocket client."""
        message = json.dumps({"event": event_type, "data": data})
        all_ws: List[WebSocket] = []
        for bucket in self._call_connections.values():
            all_ws.extend(bucket)
        for bucket in self._user_connections.values():
            all_ws.extend(bucket)
        await asyncio.gather(
            *(ws.send_text(message) for ws in all_ws), return_exceptions=True
        )


# Singleton shared across the application
ws_manager = ConnectionManager()


# ---------------------------------------------------------------------------
# WebSocket endpoints
# ---------------------------------------------------------------------------


@router.websocket("/ws/{call_id}")
async def call_websocket(call_id: str, websocket: WebSocket) -> None:
    """WebSocket endpoint for real-time events of a specific call.

    Clients connect here to receive live transcript updates, analysis
    results, and call state changes.

    Args:
        call_id: The call UUID string to subscribe to.
        websocket: Injected WebSocket connection.
    """
    await ws_manager.connect_to_call(call_id, websocket)
    try:
        # Send initial connection acknowledgment
        await websocket.send_text(
            json.dumps(
                {
                    "event": "connected",
                    "data": {"call_id": call_id, "message": "Subscribed to call events"},
                }
            )
        )
        # Keep connection open; server pushes events, client may send pings
        while True:
            try:
                raw = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                msg = json.loads(raw)
                if msg.get("type") == "ping":
                    await websocket.send_text(json.dumps({"event": "pong"}))
            except asyncio.TimeoutError:
                # Send keepalive ping
                await websocket.send_text(json.dumps({"event": "ping"}))
    except WebSocketDisconnect:
        logger.info("Call WS disconnected", call_id=call_id)
    finally:
        ws_manager.disconnect_from_call(call_id, websocket)


@router.websocket("/ws/notifications/{user_id}")
async def notification_websocket(user_id: str, websocket: WebSocket) -> None:
    """WebSocket endpoint for real-time user notifications.

    Clients connect here to receive push notifications without polling.

    Args:
        user_id: The user UUID string to subscribe to.
        websocket: Injected WebSocket connection.
    """
    await ws_manager.connect_user(user_id, websocket)
    try:
        await websocket.send_text(
            json.dumps(
                {
                    "event": "connected",
                    "data": {
                        "user_id": user_id,
                        "message": "Subscribed to notification events",
                    },
                }
            )
        )
        while True:
            try:
                raw = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                msg = json.loads(raw)
                if msg.get("type") == "ping":
                    await websocket.send_text(json.dumps({"event": "pong"}))
            except asyncio.TimeoutError:
                await websocket.send_text(json.dumps({"event": "ping"}))
    except WebSocketDisconnect:
        logger.info("Notification WS disconnected", user_id=user_id)
    finally:
        ws_manager.disconnect_user(user_id, websocket)
