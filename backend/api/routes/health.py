"""Health check endpoint."""

from datetime import datetime

from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", summary="Service health check")
async def health_check() -> dict:
    """Return service liveness information."""
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "CallGuard AI",
        "version": "0.1.0",
    }
