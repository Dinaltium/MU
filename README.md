# RxBridge

AI-powered clinical decision support system for antibiotic prescribing in resource-limited settings.

---

## ⚡ Local Development (No Docker)

### Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Python | 3.11+ | [python.org](https://www.python.org/downloads/) |
| Git | any | [git-scm.com](https://git-scm.com/) |

**No Docker. No local Redis. No local PostgreSQL.**
We use free cloud services that require zero local installation:

| Service | Purpose | Free tier |
|---------|---------|-----------|
| [Neon](https://neon.tech) | PostgreSQL database | 512 MB storage, always free |
| [Upstash](https://upstash.com) | Redis (rate limiting, token revocation) | 10k requests/day free |
| [Groq](https://console.groq.com) | LLM (Llama 3 70B) | Free, 6000 tokens/min |

---

### 1. Clone & configure

```powershell
git clone <repo-url>
cd "AI Decision Support"

# Create your .env from the template
Copy-Item .env.example .env
```

Open `.env` and fill in:
- `DATABASE_URL` — from your Neon project dashboard
- `REDIS_URL` — from your Upstash Redis dashboard (use `rediss://` scheme)
- `GROQ_API_KEY` — from console.groq.com
- `SECRET_KEY` — run `python -c "import secrets; print(secrets.token_hex(32))"`

---

### 2. Start the backend

```powershell
.\dev.ps1
```

That's it. The script will:
1. Create a Python virtual environment in `.venv/` (first run only)
2. Install all dependencies from `backend/requirements.txt`
3. Load your `.env` file
4. Start uvicorn with **hot-reload** on `http://localhost:8000`

---

### 3. Verify it's running

| URL | What you'll see |
|-----|----------------|
| `http://localhost:8000/health` | `{"status":"ok"}` |
| `http://localhost:8000/docs` | Swagger UI (all endpoints) |

---

### Daily workflow

```powershell
# Start
.\dev.ps1

# Stop
Ctrl+C
```

Uvicorn watches all `.py` files under `backend/` and restarts automatically when you save a file.

---

## 🚀 Production Deployment (Docker — hosting only)

The `Dockerfile` and `docker-compose.deploy.yml` are used **only for hosting** (Railway, Render, VPS). They are not used locally.

### Deploy to Railway

1. Push to GitHub
2. New project → Deploy from GitHub → select `backend/` as root
3. Add all `.env` variables in the Railway dashboard
4. Railway auto-detects the `Dockerfile` and builds it

### Deploy manually with Docker

```bash
# Build and run (production mode)
docker compose -f docker-compose.deploy.yml up -d --build
```

---

## 📁 Project Structure

```
AI Decision Support/
├── dev.ps1                    ← Run this for local development
├── .env.example               ← Copy to .env and fill in
├── .env                       ← Your secrets (git-ignored)
├── docker-compose.deploy.yml  ← Production hosting only
│
└── backend/
    ├── main.py                ← FastAPI app entry point
    ├── requirements.txt
    ├── Dockerfile             ← Production container image
    │
    ├── agents/                ← 8 AI pipeline agents
    ├── models/                ← Scientific models (Bayes, PK/PD, CUSUM)
    ├── pipeline/              ← Orchestrator + shared state
    ├── routers/               ← HTTP endpoints (auth, patients, …)
    ├── utils/                 ← DB, cache, LLM, security helpers
    └── data/                  ← JSON databases (formulary, MIC, interactions)
```

---

## 🔒 Security

See [security.md](security.md) for the full 10-layer security architecture with reasoning for every decision.

---

## 🧪 First API call (example)

```powershell
# Register a doctor account
Invoke-RestMethod -Uri http://localhost:8000/api/auth/register `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"email":"dr.smith@clinic.com","password":"SecurePass1","name":"Dr Smith","role":"doctor"}'

# Login
Invoke-RestMethod -Uri http://localhost:8000/api/auth/login `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"email":"dr.smith@clinic.com","password":"SecurePass1"}'
```

# MU
