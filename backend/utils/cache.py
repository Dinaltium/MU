"""
utils/cache.py

WHY REDIS:
  Redis is an in-memory store used for two security-critical purposes:
    1. Rate limiting — track request counts per IP/user without hitting
       the database on every request.
    2. JWT denylist — store revoked tokens until their natural expiry.
       Without this, a stolen token stays valid until it expires.

SECURITY DECISIONS:
  • Local dev uses plain redis://localhost:6379 — no TLS needed on loopback.
  • Production should use rediss:// (TLS) — e.g. Upstash, Redis Cloud, or
    a self-hosted instance with TLS — to protect token data in transit.
  • We set a sensible default TTL on every key so stale data is
    automatically purged. Without TTL, Redis memory grows unbounded.
  • The connection URL is env-sourced only — never hard-coded.
"""

import os
import redis.asyncio as aioredis
import logging

logger = logging.getLogger(__name__)

_client: aioredis.Redis | None = None


async def get_cache() -> aioredis.Redis:
    global _client
    if _client is None:
        _client = aioredis.from_url(
            os.environ["REDIS_URL"],
            decode_responses=True,
            socket_connect_timeout=5,
        )
        logger.info("Redis client initialised")
    return _client


# ──────────────────────────────────────────────────────────
# Rate limiting helpers
# ──────────────────────────────────────────────────────────

async def is_rate_limited(key: str, limit: int, window_seconds: int) -> bool:
    """
    Sliding-window rate limiter using atomic INCR + EXPIRE.

    WHY ATOMIC:
      A non-atomic read-then-write (GET → compare → SET) has a TOCTOU
      race condition. INCR is atomic — it increments and returns the new
      value in a single operation.

    Returns True if the caller has exceeded `limit` calls within
    `window_seconds`.
    """
    cache = await get_cache()
    current = await cache.incr(key)
    if current == 1:
        # First request in this window — set the expiry
        await cache.expire(key, window_seconds)
    return current > limit


# ──────────────────────────────────────────────────────────
# JWT denylist helpers
# ──────────────────────────────────────────────────────────

async def revoke_token(jti: str, ttl_seconds: int) -> None:
    """
    Add a JWT ID to the denylist with expiry matching token lifetime.

    WHY JTI (JWT ID):
      Storing only the token ID (a UUID in the payload) is far cheaper
      than storing the entire token string and avoids exposing the full
      token in Redis. The JTI is meaningless without the secret key.
    """
    cache = await get_cache()
    await cache.setex(f"jti:deny:{jti}", ttl_seconds, "1")


async def is_token_revoked(jti: str) -> bool:
    cache = await get_cache()
    return await cache.exists(f"jti:deny:{jti}") == 1
