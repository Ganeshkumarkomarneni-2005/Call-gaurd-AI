"""SQLAlchemy engine and session factory (sync + async)."""
from __future__ import annotations

import structlog
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from backend.core.config import settings

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Declarative base -- all ORM models inherit from this.
# ---------------------------------------------------------------------------
class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""


# ---------------------------------------------------------------------------
# Synchronous engine (used by Alembic and admin tooling)
# ---------------------------------------------------------------------------
sync_engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    echo=settings.debug,
)

SyncSession: sessionmaker[Session] = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
)


# ---------------------------------------------------------------------------
# Asynchronous engine (used by FastAPI request handlers)
# ---------------------------------------------------------------------------
async_database_url: str = settings.database_url.replace(
    "postgresql://", "postgresql+asyncpg://"
)

async_engine = create_async_engine(
    async_database_url,
    pool_pre_ping=True,
    echo=settings.debug,
)

AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ---------------------------------------------------------------------------
# Dependency helpers
# ---------------------------------------------------------------------------

async def get_db() -> AsyncSession:  # type: ignore[override]
    """FastAPI async dependency: yields an AsyncSession with auto-commit / rollback."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_sync_db() -> Session:  # type: ignore[override]
    """Sync dependency for scripts / Alembic: yields a Session with auto-commit / rollback."""
    db = SyncSession()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Lifecycle helpers
# ---------------------------------------------------------------------------

async def init_db() -> None:
    """Create all tables on startup (development / testing only).

    In production, use Alembic migrations instead.
    """
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("database.initialized")


async def close_db() -> None:
    """Dispose async engine connections on application shutdown."""
    await async_engine.dispose()
    logger.info("database.closed")
