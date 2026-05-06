"""
app/core/redis_client.py
Async Redis client — JWT blacklist, rate-limit counters, cache.
"""
from __future__ import annotations

import redis.asyncio as aioredis

from app.core.config import settings

redis_client: aioredis.Redis = aioredis.from_url(
    settings.REDIS_URL,
    decode_responses=True,
    encoding="utf-8",
)


async def ping() -> bool:
    try:
        return await redis_client.ping()
    except Exception:
        return False


async def blacklist_token(jti: str, ttl_seconds: int = 86400) -> None:
    """Add a JTI to the revocation set with TTL matching token expiry."""
    await redis_client.setex(f"blacklist:{jti}", ttl_seconds, "1")


async def is_token_blacklisted(jti: str) -> bool:
    result = await redis_client.get(f"blacklist:{jti}")
    return result is not None


async def cache_set(key: str, value: str, ttl: int) -> None:
    await redis_client.setex(key, ttl, value)


async def cache_get(key: str) -> str | None:
    return await redis_client.get(key)


async def cache_delete(key: str) -> None:
    await redis_client.delete(key)
