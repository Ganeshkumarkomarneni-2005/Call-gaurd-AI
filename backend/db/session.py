"""SQLAlchemy async session factory and dependency for FastAPI.

The engine is created lazily on first access so that tests can patch
DATABASE_URL (via os.environ) before any backend module imports trigger
engine creation.
"""

from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# ---------------------------------------------------------------------------
# Lazy engine / session factory
# ---------------------------------------------------------------------------

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def _get_db_url() -> str:
    """Read DATABASE_URL from settings at call-time (not import-time)."""
    from backend.core.config import settings  # deferred import

    url = settings.database_url

    # Normalise dialect to async-capable driver
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)

    return url


def _build_engine() -> AsyncEngine:
    url = _get_db_url()
    connect_args = {"check_same_thread": False} if "sqlite" in url else {}
    from backend.core.config import settings  # deferred import

    return create_async_engine(
        url,
        echo=settings.debug,
        future=True,
        connect_args=connect_args,
    )


def get_engine() -> AsyncEngine:
    """Return (and lazily create) the async engine singleton."""
    global _engine
    if _engine is None:
        _engine = _build_engine()
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return (and lazily create) the session factory singleton."""
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )
    return _session_factory


# Backwards-compatible module-level names used by existing code.
# Accessing these properties triggers lazy initialisation.
class _EngineProxy:
    """Proxy that returns the real engine on attribute access."""

    def __getattr__(self, name: str):
        return getattr(get_engine(), name)

    def __repr__(self) -> str:  # pragma: no cover
        return repr(get_engine())


engine = _EngineProxy()  # type: ignore[assignment]


# AsyncSessionLocal is kept for backwards compatibility but prefers get_session_factory()
class _SessionFactoryProxy:
    def __call__(self, *args, **kwargs):
        return get_session_factory()(*args, **kwargs)

    def __getattr__(self, name: str):
        return getattr(get_session_factory(), name)


AsyncSessionLocal = _SessionFactoryProxy()  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session, rolling back on error."""
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
