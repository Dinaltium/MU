FROM python:3.12-slim

# WHY SLIM:
#   The slim image excludes compilers, build tools, and most system
#   libraries that are not needed at runtime. Fewer packages = fewer
#   CVE exposure. Alpine is even smaller but has glibc compatibility
#   issues with some Python C-extensions (asyncpg, bcrypt).

# WHY NON-ROOT USER:
#   By default, Docker containers run as root. If an attacker exploits
#   the application, they get root inside the container. A non-root user
#   limits what they can do. Container escape vulnerabilities are much
#   more dangerous when the process is root.

WORKDIR /app

# Create non-root user first
RUN addgroup --system rxbridge && adduser --system --ingroup rxbridge rxbridge

# Copy and install dependencies before copying source
# WHY THIS ORDER:
#   Docker layer cache — if requirements.txt hasn't changed, pip install
#   is skipped on subsequent builds. This makes builds 10x faster.
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Drop privileges
USER rxbridge

# Expose only the application port
EXPOSE 8000

# WHY UVICORN WITH WORKERS:
#   2 workers × (2 × CPU + 1) is the Gunicorn formula. On Railway free
#   tier with 1 shared CPU, 2 workers is sufficient and avoids memory
#   pressure. Each worker is a separate process — a crash in one does
#   not take down the service.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
