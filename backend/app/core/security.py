"""
app/core/security.py
JWT creation/verification, password hashing, role guards.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# ── Crypto setup ──────────────────────────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ── JWT ───────────────────────────────────────────────────────────────────────
def create_access_token(data: dict) -> str:
    payload = data.copy()
    now = datetime.now(timezone.utc)
    payload.update({
        "iat": now,
        "exp": now + timedelta(hours=settings.ACCESS_TOKEN_EXPIRE_HOURS),
        "jti": str(uuid.uuid4()),
    })
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: dict) -> str:
    payload = data.copy()
    now = datetime.now(timezone.utc)
    payload.update({
        "iat": now,
        "exp": now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        "jti": str(uuid.uuid4()),
        "type": "refresh",
    })
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("sub") is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is invalid or expired",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ── Redis blacklist check (lazy import to avoid circular deps) ────────────────
async def _is_token_revoked(jti: str) -> bool:
    try:
        from app.core.redis_client import redis_client  # type: ignore
        result = await redis_client.get(f"blacklist:{jti}")
        return result is not None
    except Exception:
        return False  # If Redis is down, allow token (fail-open for availability)


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> dict:
    payload = decode_token(token)
    jti = payload.get("jti", "")
    if jti and await _is_token_revoked(jti):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked")
    return {
        "sub": payload["sub"],
        "role": payload.get("role"),
        "profile_id": payload.get("profile_id"),
        "jti": jti,
        "email": payload.get("email", ""),
    }


# ── Role guards ───────────────────────────────────────────────────────────────
def _require_role(role: str):
    async def guard(current_user: Annotated[dict, Depends(get_current_user)]) -> dict:
        if current_user.get("role") != role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access restricted to {role} accounts",
            )
        return current_user
    return guard


require_patient = _require_role("patient")
require_doctor = _require_role("doctor")
require_lab = _require_role("lab")
require_admin = _require_role("admin")


async def require_any_role(current_user: Annotated[dict, Depends(get_current_user)]) -> dict:
    """Allow any authenticated user."""
    return current_user
