from collections.abc import AsyncGenerator

import redis.asyncio as aioredis

from app.config import settings

redis_client = aioredis.from_url(
    settings.REDIS_URL,
    decode_responses=True,
)


async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    try:
        yield redis_client
    finally:
        pass  # connection pool managed by lifespan


async def redis_health_check() -> bool:
    try:
        return await redis_client.ping()
    except Exception:
        return False
