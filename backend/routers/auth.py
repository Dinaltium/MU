"""
routers/auth.py

WHY THIS ROUTER IS THE MOST SECURITY-SENSITIVE FILE:
  Authentication is the gateway to the entire system. Every weakness
  here becomes a weakness everywhere else. Design choices explained
  inline throughout.

ENDPOINTS:
  POST /api/auth/register  — create account
  POST /api/auth/login     — authenticate, receive JWT
  POST /api/auth/logout    — revoke current JWT
  GET  /api/auth/me        — return current user profile
"""

import logging
from datetime import timezone, datetime

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, EmailStr, field_validator

from utils.db import get_pool
from utils.security import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    login_rate_limit,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from utils.cache import revoke_token, is_rate_limited

router = APIRouter(tags=["auth"])
logger = logging.getLogger(__name__)

MAX_FAILED_LOGINS = 5
LOCKOUT_MINUTES   = 15


# ──────────────────────────────────────────────────────────
# Request/Response models — Pydantic validates inputs
# ──────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email:    EmailStr            # Pydantic validates email format
    password: str
    name:     str
    role:     str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        """
        WHY ENFORCE PASSWORD STRENGTH AT THE MODEL LEVEL:
          If we only enforce it in the route handler, a future refactor
          could accidentally bypass the check. Validators on the model
          run on every instantiation — no route can skip them.
        """
        if len(v) < 10:
            raise ValueError("Password must be at least 10 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain an uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain a digit")
        return v

    @field_validator("role")
    @classmethod
    def valid_role(cls, v: str) -> str:
        if v not in ("doctor", "patient"):
            raise ValueError("role must be 'doctor' or 'patient'")
        return v


class LoginRequest(BaseModel):
    email:    EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    expires_in:   int = ACCESS_TOKEN_EXPIRE_MINUTES * 60


# ──────────────────────────────────────────────────────────
# Register
# ──────────────────────────────────────────────────────────

@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest):
    """
    Create a new user account.

    WHY WE HASH BEFORE INSERT (not after):
      If the INSERT fails (e.g. duplicate email), the plaintext password
      was never written anywhere. The hash is computed entirely in memory
      and the plaintext is discarded immediately after hashing.
    """
    pool   = await get_pool()
    pw_hash = hash_password(body.password)

    async with pool.acquire() as conn:
        try:
            row = await conn.fetchrow(
                """
                INSERT INTO users (email, password_hash, name, role)
                VALUES ($1, $2, $3, $4)
                RETURNING id, email, role
                """,
                body.email.lower(),   # normalise — prevents hello@X and hello@x duplicates
                pw_hash,
                body.name,
                body.role,
            )
        except Exception:
            # WHY GENERIC ERROR: revealing "email already exists" leaks
            # which emails are registered (user enumeration attack).
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Registration failed. Email may already be in use.",
            )

    logger.info("New user registered: %s (%s)", row["email"], row["role"])
    return {"id": str(row["id"]), "email": row["email"], "role": row["role"]}


# ──────────────────────────────────────────────────────────
# Login
# ──────────────────────────────────────────────────────────

@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    _rate: None = Depends(login_rate_limit),   # IP-based throttle
):
    """
    Authenticate and return a short-lived JWT.

    TIMING ATTACK MITIGATION:
      We always call verify_password even when the user doesn't exist,
      using a dummy hash. This prevents an attacker from timing the
      response to discover valid emails (faster response = no user).
    """
    DUMMY_HASH = "$2b$12$fakehashfakehashfakehashfakehashfakehashfakehash"

    pool = await get_pool()
    async with pool.acquire() as conn:
        user = await conn.fetchrow(
            "SELECT * FROM users WHERE email = $1",
            body.email.lower(),
        )

    if user is None:
        verify_password(body.password, DUMMY_HASH)  # constant-time dummy
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    # Account lockout check
    if user["locked_until"] and user["locked_until"] > datetime.now():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account locked. Try again after {user['locked_until'].isoformat()}",
        )

    if not verify_password(body.password, user["password_hash"]):
        async with pool.acquire() as conn:
            new_count = (user["failed_logins"] or 0) + 1
            if new_count >= MAX_FAILED_LOGINS:
                from datetime import timedelta
                lock_until = datetime.now(tz=timezone.utc) + timedelta(minutes=LOCKOUT_MINUTES)
                await conn.execute(
                    "UPDATE users SET failed_logins=$1, locked_until=$2 WHERE id=$3::uuid",
                    new_count, lock_until, str(user["id"])
                )
                logger.warning("Account locked after %d failures: %s", new_count, user["email"])
            else:
                await conn.execute(
                    "UPDATE users SET failed_logins=$1 WHERE id=$2::uuid",
                    new_count, str(user["id"])
                )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    # Successful login — reset failure counter
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET failed_logins=0, locked_until=NULL WHERE id=$1::uuid",
            str(user["id"])
        )

    token, jti = create_access_token(str(user["id"]), user["role"])
    logger.info("Login success: %s", user["email"])
    return TokenResponse(access_token=token)


# ──────────────────────────────────────────────────────────
# Logout — token revocation
# ──────────────────────────────────────────────────────────

@router.post("/logout")
async def logout(user: dict = Depends(get_current_user)):
    """
    Revoke the current JWT by adding its JTI to the Redis denylist.

    WHY THIS MATTERS:
      Without active revocation, a doctor who logs out from one device
      still has a valid token that could be replayed for up to 15 minutes.
      The denylist closes this window immediately.
    """
    await revoke_token(user["jti"], ttl_seconds=ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    logger.info("Token revoked for user %s", user["sub"])
    return {"detail": "Logged out successfully"}


# ──────────────────────────────────────────────────────────
# Current user profile
# ──────────────────────────────────────────────────────────

@router.get("/me")
async def me(user: dict = Depends(get_current_user)):
    """
    Return non-sensitive profile fields.

    WHY NOT RETURN THE FULL USER ROW:
      The users table contains password_hash, mfa_secret, and
      failed_logins. These must never leave the database layer.
      We fetch only what the client legitimately needs.
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, email, name, role FROM users WHERE id = $1::uuid",
            user["sub"]
        )
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    return dict(row)
