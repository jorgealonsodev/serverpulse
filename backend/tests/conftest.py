import os

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Set required env vars before importing app (Settings is instantiated at import time)
os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://serverpulse:serverpulse@localhost:5432/test"
)
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("JWT_SECRET", "test-secret-key-at-least-32-bytes-long!!")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("AGENT_TOKEN_SALT", "test-salt")

from app.database import get_db
from app.main import app


@pytest.fixture
async def client():
    """Async test client for FastAPI app with per-test DB session."""
    # Create a fresh engine for this test's event loop
    test_engine = create_async_engine(
        os.environ["DATABASE_URL"],
        pool_size=5,
        pool_pre_ping=True,
        echo=False,
    )
    test_session_factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async def override_get_db():
        async with test_session_factory() as session:
            try:
                yield session
            finally:
                await session.close()

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # Cleanup
    app.dependency_overrides.clear()
    await test_engine.dispose()
