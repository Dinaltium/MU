# ─────────────────────────────────────────────────────────────
# RxBridge Local Development Runner
# ─────────────────────────────────────────────────────────────

$ErrorActionPreference = "Stop"

$ROOT = $PSScriptRoot
$BACKEND = Join-Path $ROOT "backend"
$VENV    = Join-Path $ROOT ".venv"
$PYTHON  = Join-Path $VENV "Scripts\python.exe"
$PIP     = Join-Path $VENV "Scripts\pip.exe"
$UV      = Join-Path $VENV "Scripts\uvicorn.exe"
$ENV_FILE = Join-Path $ROOT ".env"

if (-not (Test-Path $ENV_FILE)) {
    Write-Host "  [ERROR] .env file not found." -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $PYTHON)) {
    Write-Host "  Creating virtual environment..." -ForegroundColor Cyan
    python -m venv $VENV
}

Write-Host "  Checking dependencies..." -ForegroundColor Cyan
& $PIP install -r "$BACKEND\requirements.txt" --upgrade

Write-Host "  Loading environment..." -ForegroundColor Cyan
Get-Content $ENV_FILE | Where-Object { $_ -match "^\s*[^#]" -and $_ -match "=" } | ForEach-Object {
    $parts = $_ -split "=", 2
    $key   = $parts[0].Trim()
    $value = $parts[1].Trim()
    [System.Environment]::SetEnvironmentVariable($key, $value, "Process")
}

$REDIS_URL = [System.Environment]::GetEnvironmentVariable("REDIS_URL", "Process")
if ($REDIS_URL -like "redis://localhost*") {
    $redisCli = Get-Command redis-cli -ErrorAction SilentlyContinue
    if ($redisCli) {
        $ping = & redis-cli ping 2>&1
        if ($ping -ne "PONG") {
            Write-Host "  [WARN] Local Redis is not responding." -ForegroundColor Yellow
        } else {
            Write-Host "  Redis OK" -ForegroundColor Green
        }
    }
}

Write-Host "  Starting RxBridge API..." -ForegroundColor Green
& $PYTHON -m uvicorn "main:app" --host 127.0.0.1 --port 8000 --reload --reload-dir "$BACKEND" --app-dir "$BACKEND" --env-file "$ENV_FILE" --log-level info
