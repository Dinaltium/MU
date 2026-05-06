"""
app/main.py
FastAPI entry point. Configures middleware, routes, and lifespan.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONErrorResponse

from app.core.config import settings
from app.db.database import init_db
from app.api.routes import (
    auth, patients, doctors, labs, diagnoses,
    medications, recovery, reports, calendar,
    sos, notifications, ai_assist, admin
)
from app.api.websocket import router as ws_router

# ── Logging Setup ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ── Lifespan (Startup/Shutdown) ───────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}...")
    try:
        await init_db()
        logger.info("Database tables initialized successfully.")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        
    yield
    
    # Shutdown
    logger.info("Shutting down...")

# ── App Instance ──────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/api/docs" if not settings.is_production else None,
    redoc_url="/api/redoc" if not settings.is_production else None,
)

# ── Middleware ────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Global Error Handler ──────────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONErrorResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"success": False, "error": "Internal server error. Our team has been notified."}
    )

# ── Routes ────────────────────────────────────────────────────────────────────
API_PREFIX = "/api/v1"

app.include_router(auth.router, prefix=f"{API_PREFIX}/auth", tags=["Authentication"])
app.include_router(patients.router, prefix=f"{API_PREFIX}/patients", tags=["Patients"])
app.include_router(doctors.router, prefix=f"{API_PREFIX}/doctors", tags=["Doctors"])
app.include_router(labs.router, prefix=f"{API_PREFIX}/labs", tags=["Labs"])
app.include_router(diagnoses.router, prefix=f"{API_PREFIX}/diagnoses", tags=["Diagnoses"])
app.include_router(medications.router, prefix=f"{API_PREFIX}/medications", tags=["Medications"])
app.include_router(recovery.router, prefix=f"{API_PREFIX}/recovery", tags=["Recovery Tracking"])
app.include_router(reports.router, prefix=f"{API_PREFIX}/reports", tags=["Reports"])
app.include_router(calendar.router, prefix=f"{API_PREFIX}/calendar", tags=["Calendar"])
app.include_router(sos.router, prefix=f"{API_PREFIX}/sos", tags=["SOS Emergency"])
app.include_router(notifications.router, prefix=f"{API_PREFIX}/notifications", tags=["Notifications"])
app.include_router(ai_assist.router, prefix=f"{API_PREFIX}/ai", tags=["AI Clinical Assist"])
app.include_router(admin.router, prefix=f"{API_PREFIX}/admin", tags=["Administration"])

# WebSocket
app.include_router(ws_router, tags=["WebSockets"])

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": settings.APP_VERSION, "environment": settings.ENVIRONMENT}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
