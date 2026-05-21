import os

import pytest
from httpx import ASGITransport, AsyncClient

# Set required env vars before importing app (Settings is instantiated at import time)
os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test"
)
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("JWT_SECRET", "test-secret-key-at-least-32-bytes-long!!")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("AGENT_TOKEN_SALT", "test-salt")

from app.main import app


@pytest.fixture
async def client():
    """Async test client for FastAPI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
