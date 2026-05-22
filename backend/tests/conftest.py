import os

import pytest
from httpx import ASGITransport, AsyncClient
from httpx_ws.transport import ASGIWebSocketTransport
from sqlalchemy import text

# Set required env vars before importing app (Settings is instantiated at import time)
os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://serverpulse:serverpulse@localhost:5432/test"
)
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("JWT_SECRET", "test-secret-key-at-least-32-bytes-long!!")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("AGENT_TOKEN_SALT", "test-salt")

from app.database import async_session, get_db
from app.main import app


@pytest.fixture(autouse=True)
async def clean_db():
    """Truncate all tables and flush Redis before each test to ensure isolation."""
    from app.redis_client import redis_client
    from app.ws.manager import manager

    # Reset connection manager from previous tests
    manager.active.clear()

    async with async_session() as session:
        await session.execute(text("TRUNCATE TABLE metrics, servers, users RESTART IDENTITY CASCADE"))
        await session.commit()

    # Flush Redis to clear any stale pub/sub messages
    try:
        await redis_client.flushdb()
    except Exception:
        pass


@pytest.fixture
async def client():
    """Async test client for FastAPI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def ws_client():
    """Async test client with WebSocket transport for FastAPI app."""
    transport = ASGIWebSocketTransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
