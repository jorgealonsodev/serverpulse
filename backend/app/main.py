from contextlib import asynccontextmanager
import asyncio
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import delete, text as sa_text

from app.config import settings
from app.database import async_session, engine
from app.models.metric import Metric
from app.redis_client import redis_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: verify DB and Redis connectivity

    db_ok = False
    try:
        async with async_session() as session:
            await session.execute(sa_text("SELECT 1"))
            db_ok = True
    except Exception:
        db_ok = False

    redis_ok = False
    try:
        redis_ok = await redis_client.ping()
    except Exception:
        redis_ok = False

    if not db_ok:
        raise RuntimeError("Database connection failed on startup")
    if not redis_ok:
        raise RuntimeError("Redis connection failed on startup")

    # Spawn cleanup background task
    async def _cleanup_old_metrics():
        while True:
            await asyncio.sleep(3600)
            try:
                async with async_session() as session:
                    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
                    await session.execute(
                        delete(Metric).where(Metric.received_at < cutoff)
                    )
                    await session.commit()
            except Exception:
                pass  # log in production

    cleanup_task = asyncio.create_task(_cleanup_old_metrics())
    app.state.cleanup_task = cleanup_task

    yield

    # Shutdown: cancel cleanup task, dispose connections
    app.state.cleanup_task.cancel()
    try:
        await app.state.cleanup_task
    except asyncio.CancelledError:
        pass
    await engine.dispose()
    await redis_client.close()


app = FastAPI(
    title="ServerPulse API",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware for frontend dev server
cors_origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()]
if cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.get("/health")
async def health():
    db_status = "ok"
    redis_status = "ok"

    # Check DB
    try:
        async with async_session() as session:
            await session.execute(sa_text("SELECT 1"))
    except Exception:
        db_status = "error"

    # Check Redis
    try:
        if not await redis_client.ping():
            redis_status = "error"
    except Exception:
        redis_status = "error"

    if db_status == "ok" and redis_status == "ok":
        return JSONResponse(
            status_code=200,
            content={"status": "ok", "db": db_status, "redis": redis_status},
        )
    return JSONResponse(
        status_code=503,
        content={"status": "error", "db": db_status, "redis": redis_status},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


# ---------------------------------------------------------------------------
# Future routers (placeholders — Fase 2+)
# ---------------------------------------------------------------------------
from app.api.auth import router as auth_router

app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])

from app.api.servers import router as servers_router

app.include_router(servers_router, prefix="/api/v1/servers", tags=["servers"])

from app.api.metrics import router as metrics_router

app.include_router(metrics_router, prefix="/api/v1/metrics", tags=["metrics"])

from app.api.ws import router as ws_router

app.include_router(ws_router, tags=["ws"])
#
# from app.api.users import router as users_router
# app.include_router(users_router, prefix="/api/v1/users", tags=["users"])
