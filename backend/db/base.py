"""SQLAlchemy declarative base and database initialisation helpers."""

from __future__ import annotations

import structlog
from sqlalchemy.orm import DeclarativeBase

logger: structlog.BoundLogger = structlog.get_logger(__name__)


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""


async def init_db() -> None:
    """Create all tables that don't exist yet.

    Called during application startup via the lifespan context manager.
    Supports both SQLite (local dev) and PostgreSQL (production).
    """
    from backend.db.session import get_engine  # noqa: PLC0415
    import backend.db.models  # noqa: F401, PLC0415  — register all models

    real_engine = get_engine()
    logger.info("Initialising database schema")
    async with real_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database schema ready")


async def close_db() -> None:
    """Dispose the engine connection pool on shutdown."""
    from backend.db.session import get_engine  # noqa: PLC0415

    real_engine = get_engine()
    logger.info("Closing database connections")
    await real_engine.dispose()
    logger.info("Database connections closed")
