"""
app/db/database.py
Async SQLAlchemy engine, session factory, and table initialiser.
"""
from __future__ import annotations

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# ── Engine ────────────────────────────────────────────────────────────────────
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True,
    pool_recycle=3600,
    # SQLite tuning (noop on Postgres/asyncpg)
    connect_args={"check_same_thread": False}
    if "sqlite" in settings.DATABASE_URL
    else {},
)

# ── Session factory ───────────────────────────────────────────────────────────
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=True,
    autocommit=False,
)


# ── Base class ────────────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    pass


# ── DB initialiser ────────────────────────────────────────────────────────────
async def init_db() -> None:
    """Import all models to register them with Base.metadata, then create tables."""
    # These imports MUST happen before create_all so SQLAlchemy sees the mappers.
    from app.models import (  # noqa: F401
        audit_log,
        calendar_event,
        consent,
        diagnosis,
        doctor,
        doctor_patient,
        lab,
        lab_order,
        lab_report,
        medication,
        notification,
        patient,
        pipeline_run,
        recovery,
        report,
        sos_alert,
        user,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# ── Dependency ────────────────────────────────────────────────────────────────
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
