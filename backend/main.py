"""FastAPI application entry point for CallGuard AI."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.core.config import settings
from backend.core.logging_config import setup_logging
from backend.db.base import close_db, init_db

# Set up logging immediately so all module-level loggers see the config
setup_logging()

logger: structlog.BoundLogger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """FastAPI lifespan: run startup tasks before yield, teardown after."""
    logger.info("CallGuard AI starting up", version=settings.version, debug=settings.debug)
    await init_db()
    yield
    logger.info("CallGuard AI shutting down")
    await close_db()


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="CallGuard AI",
    description=(
        "AI-powered call screening and management system. "
        "Protects users from unwanted calls using real-time AI analysis."
    ),
    version=settings.version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ---------------------------------------------------------------------------
from fastapi import Request, Response

# Middleware
# ---------------------------------------------------------------------------

@app.middleware("http")
async def cors_middleware(request: Request, call_next):
    origin = request.headers.get("origin")
    if request.method == "OPTIONS":
        response = Response(status_code=204)
    else:
        response = await call_next(request)

    if origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Max-Age"] = "86400"
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_origin_regex=r".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

from backend.api.routes.auth import router as auth_router  # noqa: E402
from backend.api.routes.calls import router as calls_router  # noqa: E402
from backend.api.routes.dashboard import router as dashboard_router  # noqa: E402
from backend.api.routes.health import router as health_router  # noqa: E402
from backend.api.routes.notifications import router as notifications_router  # noqa: E402
from backend.api.routes.telephony import router as telephony_router  # noqa: E402
from backend.api.websocket import router as ws_router  # noqa: E402

app.include_router(health_router)
app.include_router(auth_router, prefix="/api/v1")
app.include_router(calls_router, prefix="/api/v1")
app.include_router(telephony_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(notifications_router, prefix="/api/v1")
app.include_router(ws_router)  # WebSocket routes carry their own paths


# ---------------------------------------------------------------------------
# Root endpoint
# ---------------------------------------------------------------------------


@app.get("/", tags=["root"], summary="API information")
async def root() -> dict:
    """Return basic API information."""
    return {
        "service": "CallGuard AI",
        "version": settings.version,
        "docs": "/docs",
        "health": "/health",
        "api_base": "/api/v1",
    }
