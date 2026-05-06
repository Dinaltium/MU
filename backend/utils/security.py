"""
utils/security.py

This module owns ALL authentication and authorisation primitives.

WHY A DEDICATED SECURITY MODULE:
  Scattering auth logic across routers leads to inconsistency — one
  router might forget to check a claim, another might use a weaker
  algorithm. Centralising here means:
    - One place to audit
    - One place to upgrade (e.g. switch to RS256)
    - Every router imports from the same source of truth

JWT STRATEGY:
  • HS256 with a 256-bit random secret (generated once, stored in env)
  • Access token: 15-minute lifetime — short so stolen tokens expire fast
  • Each token carries: sub (user_id), role, jti (UUID for revocation)
  • JTI denylist in Redis — logout actually revokes the token

BRUTE-FORCE PROTECTION:
  • Failed login counter in DB (failed_logins column)
  • After 5 failures → account locked for 15 minutes (locked_until)
  • Rate limiter in Redis: max 10 login attempts / 10 min per IP

PASSWORD HASHING:
  • bcrypt with work factor 12 — slow enough to make offline cracking
    impractical, fast enough for production use (< 200ms per hash)
  • We NEVER store or log the plaintext password anywhere

ROLE HIERARCHY:
  • admin  → can do anything
  • doctor → can access their own patients and consultations
  • patient → can access only their own data
"""

import os
import uuid
import logging
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from utils.cache import is_token_revoked, is_rate_limited

logger = logging.getLogger(__name__)

SECRET_KEY = os.environ.get("SECRET_KEY", "CHANGE_ME_IN_PROD")
ALGORITHM = os.environ.get("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "15")
)

bearer_scheme = HTTPBearer()


# ──────────────────────────────────────────────────────────
# Password utilities
# ──────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    """
    Hash a password with bcrypt work factor 12.

    WHY 12:
      Work factor doubles computation time per unit. Factor 12 ≈ 200ms
      on modern hardware — tolerable for login, but makes a brute-force
      of 1 billion passwords take ~6,000 years.
    """
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt(rounds=12)).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# ──────────────────────────────────────────────────────────
# Token utilities
# ──────────────────────────────────────────────────────────

def create_access_token(user_id: str, role: str) -> tuple[str, str]:
    """
    Create a signed JWT access token.

    Returns (token_string, jti) so the caller can store the JTI for
    future revocation.

    WHY SHORT EXPIRY (15 min):
      If an attacker captures a token from logs or a bug, the window
      of exploitation is at most 15 minutes. Combine with the JTI
      denylist to achieve effective logout.
    """
    jti = str(uuid.uuid4())
    expire = datetime.now(tz=timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "sub":  user_id,
        "role": role,
        "jti":  jti,
        "exp":  expire,
        "iat":  datetime.now(tz=timezone.utc),
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token, jti


def decode_token(token: str) -> dict:
    """
    Decode and validate a JWT. Raises HTTPException on any problem.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from exc


# ──────────────────────────────────────────────────────────
# FastAPI dependency — protects any route
# ──────────────────────────────────────────────────────────

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    """
    FastAPI dependency that:
      1. Extracts the Bearer token from the Authorization header
      2. Decodes and validates the JWT signature and expiry
      3. Checks the JTI denylist (logout / revocation)
      4. Returns the payload dict {sub, role, jti, …}

    WHY CHECK DENYLIST ON EVERY REQUEST:
      JWT is stateless by design, which means there's no built-in way
      to invalidate one before it expires. The denylist solves this —
      when a doctor logs out, we add the JTI to Redis and every
      subsequent request with that token is rejected.
    """
    token = credentials.credentials
    payload = decode_token(token)

    jti = payload.get("jti")
    if not jti or await is_token_revoked(jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
        )

    return payload


def require_role(*roles: str):
    """
    Dependency factory that restricts a route to specific roles.

    Usage:
        @router.get("/admin-only")
        async def admin_route(user=Depends(require_role("admin"))):
            ...
    """
    async def _check(user: dict = Depends(get_current_user)) -> dict:
        if user["role"] not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user['role']}' is not authorised for this resource",
            )
        return user
    return _check


# ──────────────────────────────────────────────────────────
# IP-based rate limiter dependency
# ──────────────────────────────────────────────────────────

async def login_rate_limit(request: Request) -> None:
    """
    Allow at most 10 login attempts per IP per 10-minute window.

    WHY IP-BASED (not user-based) FOR LOGIN:
      An attacker trying to brute-force accounts rotates usernames.
      An IP-based limiter catches the attack regardless of which
      account is targeted. We layer user-based lockout on top.
    """
    ip = request.client.host if request.client else "unknown"
    key = f"rate:login:{ip}"
    if await is_rate_limited(key, limit=10, window_seconds=600):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please wait 10 minutes.",
        )
