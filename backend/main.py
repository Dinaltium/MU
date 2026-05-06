"""
main.py — RxBridge FastAPI Application Entry Point

SECURITY ARCHITECTURE SUMMARY:
  Every incoming request passes through this stack:

  Internet → (TLS) → FastAPI → CORS middleware → Rate limit → Auth → ABAC → Handler

  1. TLS          : enforced by Railway/Vercel; never serve plaintext
  2. CORS         : whitelist only known frontend origins
  3. Rate limit   : IP-based throttle on sensitive endpoints (auth router)
  4. Auth         : JWT Bearer token validation + denylist check (every route)
  5. ABAC         : attribute-based checks within each route handler
  6. Audit log    : every protected action writes to audit_log table

LIFESPAN EVENTS:
  startup  → init DB schema, start background monitoring task
  shutdown → (pool cleanup handled by asyncpg)

WHY NOT expose /docs in production:
  The Swagger UI at /docs shows all endpoints, request schemas, and
  allows direct invocation without authentication. In production, set
  docs_url=None and redoc_url=None unless behind a VPN.
"""

import asyncio
import os
import sys
import logging
from contextlib import asynccontextmanager

# ──────────────────────────────────────────────────────────
# Windows DLL Fix for PyTorch/pgmpy
#
# WHY: In some Windows environments, PyTorch's c10.dll fails to initialize
#      with "WinError 1114" when imported in a spawned subprocess (like
#      uvicorn's reloader). Explicitly adding the torch lib directory
#      to the DLL search path often resolves this.
# ──────────────────────────────────────────────────────────
if sys.platform == "win32":
    # Try to find torch/lib without importing torch first (to avoid the crash)
    potential_torch_paths = [
        os.path.join(os.path.dirname(sys.executable), "Lib", "site-packages", "torch", "lib"),
        os.path.join(os.path.dirname(os.path.dirname(sys.executable)), "Lib", "site-packages", "torch", "lib"),
    ]
    for path in potential_torch_paths:
        if os.path.exists(path):
            os.add_dll_directory(path)
            break
    # Also set OpenMP duplicate lib policy just in case
    os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"


from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from routers import auth, consultations, patients, alerts, monitoring
from utils.db import init_db
from agents.monitoring import start_monitoring

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────
# Startup / shutdown lifespan
# ──────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("RxBridge starting up...")
    await init_db()
    asyncio.create_task(start_monitoring())
    logger.info("Background monitoring task started")
    yield
    logger.info("RxBridge shutting down")


# ──────────────────────────────────────────────────────────
# Application
# ──────────────────────────────────────────────────────────

IS_PRODUCTION = os.environ.get("ENVIRONMENT", "development") == "production"

app = FastAPI(
    title="RxBridge API",
    version="1.0.0",
    lifespan=lifespan,
    # WHY disable docs in production:
    #   Swagger UI makes it trivial to probe every endpoint interactively.
    #   Restricting it to development environments reduces the attack surface.
    docs_url=None if IS_PRODUCTION else "/docs",
    redoc_url=None if IS_PRODUCTION else "/redoc",
)

# ──────────────────────────────────────────────────────────
# CORS
#
# WHY STRICT ORIGINS:
#   allow_origins=["*"] would permit any website to make credentialed
#   requests to our API, enabling CSRF. We list only our own domains.
#   In dev, localhost:3000 is allowed. In prod, update to the Vercel URL.
# ──────────────────────────────────────────────────────────

ALLOWED_ORIGINS = os.environ.get(
    "ALLOWED_ORIGINS",
    "http://localhost:3000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    allow_credentials=True,
    max_age=600,   # pre-flight cache duration (seconds)
)

# ──────────────────────────────────────────────────────────
# Security response headers middleware
#
# WHY EACH HEADER:
#   X-Content-Type-Options: prevents MIME-type sniffing
#   X-Frame-Options: prevents clickjacking
#   Referrer-Policy: prevents leaking our API URL to third-party trackers
#   Permissions-Policy: opt out of browser features we don't use
# ──────────────────────────────────────────────────────────

@app.middleware("http")
async def add_security_headers(request: Request, call_next) -> Response:
    response = await call_next(request)
    response.headers["X-Content-Type-Options"]  = "nosniff"
    response.headers["X-Frame-Options"]          = "DENY"
    response.headers["Referrer-Policy"]          = "no-referrer"
    response.headers["Permissions-Policy"]       = "camera=(), microphone=(), geolocation=()"
    if IS_PRODUCTION:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

# ──────────────────────────────────────────────────────────
# Global exception handler
#
# WHY NOT LET EXCEPTIONS PROPAGATE NATURALLY:
#   Default FastAPI 500 errors include Python tracebacks in development
#   mode, which leak internal details (file paths, function names,
#   library versions). We return a generic message instead.
# ──────────────────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred. Our team has been notified."},
    )

# ──────────────────────────────────────────────────────────
# Routers
# ──────────────────────────────────────────────────────────

app.include_router(auth.router,          prefix="/api/auth")
app.include_router(patients.router,      prefix="/api/patients")
app.include_router(consultations.router, prefix="/api/consultations")
app.include_router(alerts.router,        prefix="/api/alerts")
app.include_router(monitoring.router,    prefix="/api/monitoring")


@app.get("/health")
async def health():
    """
    WHY /health (not /):
      Load balancers and container orchestrators (Railway, Docker Compose)
      hit /health to determine if the service is alive. This endpoint
      requires no authentication so it works before auth middleware loads.
      It intentionally returns minimal information — no version strings
      that could aid vulnerability fingerprinting.
    """
    return {"status": "ok"}
