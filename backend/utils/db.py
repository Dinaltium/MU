"""
utils/db.py

WHY ASYNCPG + CONNECTION POOL:
  asyncpg is the fastest PostgreSQL driver for Python — 3-5x faster than
  psycopg2 for high-concurrency workloads. A shared pool (not per-request
  connections) means we don't pay SSL handshake overhead on every API call.

SECURITY DECISIONS:
  1. Single pool instance — avoids connection proliferation that could
     exhaust Neon's connection limit (500 on free tier).
  2. ssl="require" is enforced — ensures the wire between us and Neon is
     always TLS-encrypted even on private networks. Without this, an
     attacker with network access could read patient data in transit.
  3. min_size=2, max_size=10 — limits blast radius if a bug causes
     connection leaks; the pool will not spiral beyond 10 open sockets.
  4. The connection string is read from the environment variable only;
     it is never hard-coded or logged. Logging the DATABASE_URL would
     expose credentials in log aggregators.
"""

import asyncpg
import os
import logging

logger = logging.getLogger(__name__)

_pool: asyncpg.Pool | None = None


async def get_pool() -> asyncpg.Pool:
    """
    Return the shared connection pool, creating it on first call.

    WHY LAZY INIT:
      FastAPI starts the pool inside the lifespan context manager so it
      is created after the event loop exists. Calling asyncpg.create_pool()
      at module import time would fail because no loop is running yet.
    """
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            dsn=os.environ["DATABASE_URL"],
            min_size=2,
            max_size=10,
            ssl="require",          # Enforce TLS — never plaintext
            command_timeout=30,     # Prevent slow queries from hanging forever
        )
        logger.info("Database pool created (min=2, max=10, ssl=require)")
    return _pool


async def init_db() -> None:
    """
    Called once at startup to verify connectivity and run schema DDL.

    WHY NOT ALEMBIC:
      For the hackathon scope, running DDL in init_db is fast enough.
      In production, migrate to Alembic for version-controlled migrations
      and zero-downtime schema changes.
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                email           VARCHAR UNIQUE NOT NULL,
                password_hash   VARCHAR NOT NULL,
                name            VARCHAR NOT NULL,
                role            VARCHAR NOT NULL CHECK (role IN ('doctor','patient','admin')),
                telegram_handle VARCHAR,
                mfa_secret      VARCHAR,           -- TOTP secret (encrypted at rest)
                failed_logins   INTEGER DEFAULT 0, -- brute-force counter
                locked_until    TIMESTAMP,         -- account lockout expiry
                created_at      TIMESTAMP DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS patients (
                id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id         UUID REFERENCES users(id) ON DELETE CASCADE,
                doctor_id       UUID REFERENCES users(id),
                name            VARCHAR NOT NULL,
                age             INTEGER CHECK (age > 0 AND age < 150),
                gender          VARCHAR,
                location        VARCHAR,
                weight_kg       FLOAT CHECK (weight_kg > 0),
                renal_function  FLOAT DEFAULT 1.0 CHECK (renal_function >= 0 AND renal_function <= 1),
                conditions      JSONB DEFAULT '[]',
                allergies       JSONB DEFAULT '[]',
                medications     JSONB DEFAULT '[]',
                created_at      TIMESTAMP DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS consultations (
                id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                doctor_id       UUID REFERENCES users(id),
                patient_id      UUID REFERENCES patients(id) ON DELETE CASCADE,
                symptoms        JSONB NOT NULL,
                pipeline_output JSONB,
                status          VARCHAR DEFAULT 'running'
                                  CHECK (status IN ('running','complete','failed')),
                created_at      TIMESTAMP DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS recommendations (
                id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                consultation_id  UUID REFERENCES consultations(id) ON DELETE CASCADE,
                drug_name        VARCHAR NOT NULL,
                diagnosis        VARCHAR NOT NULL,
                resistance_risk  VARCHAR CHECK (resistance_risk IN ('LOW','MODERATE','HIGH')),
                efficacy_score   FLOAT,
                safety_score     FLOAT,
                doctor_approved  BOOLEAN DEFAULT FALSE,
                created_at       TIMESTAMP DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS monitoring_checkins (
                id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                patient_id       UUID REFERENCES patients(id) ON DELETE CASCADE,
                consultation_id  UUID REFERENCES consultations(id) ON DELETE CASCADE,
                feel_status      VARCHAR NOT NULL CHECK (feel_status IN ('better','same','worse')),
                symptom_severity INTEGER CHECK (symptom_severity BETWEEN 1 AND 10),
                recovery_score   FLOAT,
                cusum_value      FLOAT,
                created_at       TIMESTAMP DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS alerts (
                id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                target_id   UUID NOT NULL,
                target_type VARCHAR NOT NULL CHECK (target_type IN ('doctor','patient')),
                alert_type  VARCHAR NOT NULL,
                severity    VARCHAR NOT NULL CHECK (severity IN ('LOW','MODERATE','HIGH','CRITICAL')),
                message     TEXT NOT NULL,
                read        BOOLEAN DEFAULT FALSE,
                created_at  TIMESTAMP DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS audit_log (
                id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id     UUID REFERENCES users(id),
                action      VARCHAR NOT NULL,   -- e.g. 'VIEW_PATIENT', 'APPROVE_DRUG'
                resource_id UUID,
                ip_address  INET,
                created_at  TIMESTAMP DEFAULT NOW()
            );

            -- Indexes for common query patterns
            CREATE INDEX IF NOT EXISTS idx_consultations_doctor   ON consultations(doctor_id);
            CREATE INDEX IF NOT EXISTS idx_consultations_patient  ON consultations(patient_id);
            CREATE INDEX IF NOT EXISTS idx_alerts_target          ON alerts(target_id, read);
            CREATE INDEX IF NOT EXISTS idx_audit_user             ON audit_log(user_id, created_at);
        """)
        logger.info("Database schema verified / initialised")
