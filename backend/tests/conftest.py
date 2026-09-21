"""Pytest configuration, fixtures, and helpers for the CallGuard AI test suite."""

from __future__ import annotations

import asyncio
import os
import uuid
from typing import AsyncGenerator, Generator

# ---------------------------------------------------------------------------
# IMPORTANT: Set DATABASE_URL to SQLite BEFORE importing any backend modules.
# Use a unique per-run file so tests from different runs don't collide.
# ---------------------------------------------------------------------------
_TEST_DB_FILE = f"test_callguard_{uuid.uuid4().hex[:8]}.db"
_TEST_DB_URL = f"sqlite+aiosqlite:///{_TEST_DB_FILE}"

os.environ["DATABASE_URL"] = _TEST_DB_URL
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production-only")
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("DEBUG", "false")

import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine  # noqa: E402

# Now safe to import backend modules
from backend.db.base import Base  # noqa: E402
from backend.db.session import get_db  # noqa: E402
from backend.main import app  # noqa: E402
from backend.schemas.call import IncomingCallRequest  # noqa: E402
from backend.schemas.user import UserCreate  # noqa: E402
from backend.services import call_service, user_service  # noqa: E402

# ---------------------------------------------------------------------------
# In-memory SQLite engine for tests (unique per test run)
# ---------------------------------------------------------------------------

test_engine = create_async_engine(
    _TEST_DB_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


# ---------------------------------------------------------------------------
# Session-scoped event loop
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def event_loop():
    """Create a single event loop for the entire test session."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


# ---------------------------------------------------------------------------
# Database fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_tables():
    """Create all tables once per test session."""
    import backend.db.models  # noqa: F401 — register ORM models with Base

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()
    # Clean up the test db file
    import os as _os
    try:
        _os.remove(_TEST_DB_FILE)
    except FileNotFoundError:
        pass


@pytest_asyncio.fixture
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield a test database session that rolls back after each test."""
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


# ---------------------------------------------------------------------------
# Dependency override + TestClient
# ---------------------------------------------------------------------------


@pytest.fixture
def client(test_db: AsyncSession) -> Generator[TestClient, None, None]:
    """HTTP test client with the DB dependency overridden to use the test DB."""

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield test_db

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

_TEST_USER_EMAIL = "testuser@example.com"
_TEST_USER_PASSWORD = "Str0ng!Pass#2026"


@pytest_asyncio.fixture
async def test_user(test_db: AsyncSession):
    """Create (or reuse) a test user and return the ORM instance."""
    existing = await user_service.get_user_by_email(test_db, _TEST_USER_EMAIL)
    if existing:
        return existing
    user = await user_service.create_user(
        test_db,
        UserCreate(
            email=_TEST_USER_EMAIL,
            password=_TEST_USER_PASSWORD,
            full_name="Test User",
        ),
    )
    await test_db.commit()
    return user


@pytest.fixture
def auth_headers(client: TestClient, test_user) -> dict[str, str]:
    """Return an Authorization header dict for the test user."""
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": _TEST_USER_EMAIL, "password": _TEST_USER_PASSWORD},
    )
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Sample call fixture
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def sample_call(test_db: AsyncSession, test_user):
    """Create and return a sample Call record for tests."""
    import uuid as _uuid
    call = await call_service.create_call(
        test_db,
        IncomingCallRequest(
            caller_number="+15550001234",
            virtual_number="+15559876543",
            telephony_call_id=f"test-call-{_uuid.uuid4().hex[:8]}",
            telephony_provider="mock",
        ),
        user_id=test_user.id,
    )
    await test_db.commit()
    return call
