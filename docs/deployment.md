# CallGuard AI — Deployment Guide

**Document ID:** DEPLOY-001  
**Version:** 1.0  
**Date:** 2026-09-17  

---

## 1. Local Development Setup

### 1.1 Prerequisites

| Tool | Version | Notes |
|------|---------|-------|
| Python | 3.11+ | pyenv recommended |
| Node.js | 18+ | nvm recommended |
| PostgreSQL | 16+ | Or use Docker |
| Git | Any | |
| Docker (optional) | 24+ | For containerized setup |

### 1.2 Step-by-Step Setup

```bash
# 1. Clone repository
git clone https://github.com/your-org/callguard-ai.git
cd callguard-ai

# 2. Python virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/macOS)
source venv/bin/activate

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Copy environment template
cp .env.example .env
# Edit .env — at minimum, set SECRET_KEY and DATABASE_URL

# 5. Create database (if not using Docker)
createdb callguard

# 6. Run database migrations
alembic upgrade head

# 7. Install frontend dependencies
cd frontend
npm install
cd ..

# 8. Start backend
uvicorn backend.main:app --reload --port 8000

# 9. Start frontend (new terminal)
cd frontend
npm run dev
```

**Verify:**
- Backend: http://localhost:8000/health → should return `{"status": "healthy"}`
- API docs: http://localhost:8000/docs
- Frontend: http://localhost:3000

---

## 2. Docker Deployment

### 2.1 Prerequisites

- Docker 24+
- Docker Compose 2.x (included with Docker Desktop)

### 2.2 Start All Services

```bash
# Build and start all services
docker compose up --build

# Start in background
docker compose up -d --build

# Check status
docker compose ps

# View logs
docker compose logs -f backend
docker compose logs -f frontend

# Stop all services
docker compose down

# Stop and remove all data (WARNING: irreversible)
docker compose down -v
```

### 2.3 Individual Service Commands

```bash
# Rebuild only the backend
docker compose build backend
docker compose up -d backend

# Run migrations inside container
docker compose exec backend alembic upgrade head

# Open psql inside postgres container
docker compose exec postgres psql -U callguard -d callguard

# Run tests inside container
docker compose exec backend pytest
```

### 2.4 Docker Compose Services

| Service | Container | Port | Volume |
|---------|-----------|------|--------|
| postgres | callguard_postgres | 5432 | callguard_postgres_data |
| redis | callguard_redis | 6379 | callguard_redis_data |
| backend | callguard_backend | 8000 | (source mounted in dev) |
| frontend | callguard_frontend | 3000 | — |

---

## 3. Production Deployment

### 3.1 Recommended Stack

| Component | Platform | Notes |
|-----------|---------|-------|
| Frontend | **Vercel** | Auto-deploy from GitHub; global CDN |
| Backend | **Railway** or **Render** | Docker-based; auto-scaling |
| Database | **Neon** or **Supabase** | Managed PostgreSQL; connection pooling included |
| Redis | **Upstash** | Managed Redis; pay-per-use |

### 3.2 Vercel (Frontend)

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
cd frontend
vercel

# Set environment variables in Vercel dashboard:
# NEXT_PUBLIC_API_URL = https://your-backend.railway.app
# NEXT_PUBLIC_WS_URL  = wss://your-backend.railway.app
```

**Auto-deploy:** Connect GitHub repo → Vercel auto-deploys on push to `main`.

### 3.3 Railway (Backend)

1. Create Railway project
2. Connect GitHub repository
3. Set build command: (Railway detects Dockerfile automatically)
4. Set environment variables (see section 4)
5. Add PostgreSQL plugin (or use Neon)
6. Deploy

**Railway environment variables** (add in Railway dashboard):
```
APP_ENV=production
DEBUG=false
SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_urlsafe(32))">
DATABASE_URL=<from Railway PostgreSQL plugin or Neon>
TELEPHONY_PROVIDER=exotel
EXOTEL_SID=<your sid>
EXOTEL_TOKEN=<your token>
# ... all other required vars
```

### 3.4 Render (Backend Alternative)

1. Create new Web Service
2. Connect GitHub repository
3. Set build command: `docker build -t callguard .`
4. Set start command: (from Dockerfile CMD)
5. Add environment variables
6. Deploy

### 3.5 Neon (Database)

1. Create Neon account and project
2. Copy connection string: `postgresql://user:pass@ep-xxx.neon.tech/callguard?sslmode=require`
3. Set as `DATABASE_URL` in backend environment
4. Run migrations: `alembic upgrade head` (from local machine with Neon connection string)

### 3.6 Production Checklist

```
□ SECRET_KEY is a cryptographically random 32+ character string
□ DEBUG=false
□ CORS_ORIGINS is set to exact production frontend URL (not *)
□ DATABASE_URL uses SSL (sslmode=require)
□ All external providers are real (not mock)
□ HTTPS is enforced at reverse proxy / platform level
□ Health check endpoint returns 200
□ Alembic migrations run successfully
□ At least one admin user created
□ ML models are loaded (check /health response)
□ Rate limiting is active
□ Monitoring configured (see section 7)
```

---

## 4. Environment Variables Reference

Complete reference for all environment variables.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `APP_NAME` | No | `CallGuard AI` | Application display name |
| `APP_ENV` | No | `development` | `development`, `production`, `test` |
| `DEBUG` | No | `true` | Enable debug mode (disable in production) |
| `SECRET_KEY` | **YES** | — | JWT signing key (min 32 chars) |
| `ALGORITHM` | No | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `60` | Access token lifetime |
| `DATABASE_URL` | **YES** | — | PostgreSQL connection URL |
| `TELEPHONY_PROVIDER` | No | `mock` | `mock` or `exotel` |
| `EXOTEL_SID` | If exotel | — | Exotel account SID |
| `EXOTEL_TOKEN` | If exotel | — | Exotel auth token |
| `EXOTEL_FROM_NUMBER` | If exotel | — | Exotel from number |
| `EXOTEL_SUBDOMAIN` | If exotel | — | Exotel subdomain |
| `STT_PROVIDER` | No | `mock` | `mock`, `google`, `deepgram` |
| `GOOGLE_SPEECH_API_KEY` | If google | — | Google Speech API key |
| `DEEPGRAM_API_KEY` | If deepgram | — | Deepgram API key |
| `TTS_PROVIDER` | No | `mock` | `mock`, `google`, `elevenlabs` |
| `GOOGLE_TTS_API_KEY` | If google | — | Google TTS API key |
| `ELEVENLABS_API_KEY` | If elevenlabs | — | ElevenLabs API key |
| `LLM_PROVIDER` | No | `mock` | `mock`, `openai`, `gemini`, `anthropic` |
| `OPENAI_API_KEY` | If openai | — | OpenAI API key |
| `GEMINI_API_KEY` | If gemini | — | Google Gemini API key |
| `ANTHROPIC_API_KEY` | If anthropic | — | Anthropic API key |
| `NEXT_PUBLIC_API_URL` | No | `http://localhost:8000` | Backend URL for frontend |
| `NEXT_PUBLIC_WS_URL` | No | `ws://localhost:8000` | WebSocket URL for frontend |
| `NOTIFICATION_PROVIDER` | No | `web_push` | Push notification provider |
| `CORS_ORIGINS` | No | `http://localhost:3000,...` | Comma-separated allowed origins |

---

## 5. Health Checks

### 5.1 Health Endpoint

```bash
curl http://localhost:8000/health
```

Expected response (healthy):
```json
{
  "status": "healthy",
  "timestamp": "2026-09-17T10:30:00Z",
  "components": {
    "database": "healthy",
    "telephony_adapter": "healthy",
    "stt_adapter": "healthy",
    "tts_adapter": "healthy",
    "llm_adapter": "healthy",
    "intent_model": "loaded",
    "fraud_model": "loaded",
    "caller_type_model": "loaded",
    "recruitment_model": "loaded"
  }
}
```

Response (degraded — database down):
```json
{
  "status": "degraded",
  "components": {
    "database": "unhealthy: connection refused",
    "telephony_adapter": "healthy",
    ...
  }
}
```
HTTP 503 when any critical component is unhealthy.

### 5.2 Docker Health Check

The Dockerfile includes a health check:
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
```

View health status:
```bash
docker inspect callguard_backend | python -m json.tool | grep Health -A 10
```

---

## 6. Scaling Considerations

### 6.1 Vertical Scaling (Single Instance)

Minimum production sizing:
- **CPU:** 2 vCPU
- **RAM:** 2GB (includes ML models in memory)
- **Storage:** 10GB (for database and logs)

### 6.2 Horizontal Scaling

Backend is designed for horizontal scaling:
- **Stateless:** No in-memory session state (JWT-based auth)
- **Database:** Shared PostgreSQL with connection pooling
- **WebSocket:** Requires Redis for pub/sub across instances (not implemented in v1 — planned)

**Current limitation:** WebSocket events are in-process. Multiple backend instances require Redis pub/sub (Phase 19 planned improvement).

### 6.3 Database Scaling

- Use connection pooling (asyncpg pool: 2–10 connections per instance)
- Add read replica for reporting queries if needed
- Partition `call_transcripts` table by date if call volume exceeds 1M records

---

## 7. Monitoring

### 7.1 Recommended Monitoring Stack

| Tool | Purpose |
|------|---------|
| **Sentry** | Error tracking and performance monitoring |
| **Uptime Robot** | Uptime monitoring for `/health` endpoint |
| **Grafana + Prometheus** | Metrics dashboards (optional, advanced) |
| **Railway/Render metrics** | Built-in CPU/memory/request metrics |

### 7.2 Key Metrics to Monitor

| Metric | Alert Threshold |
|--------|----------------|
| Health check failures | Any failure → alert |
| API error rate (5xx) | > 1% over 5 minutes |
| Pipeline latency (p95) | > 3 seconds |
| Database connection errors | Any error |
| ML model inference errors | > 0.5% of calls |
| Blocked calls rate | Sudden spike (may indicate attack) |

### 7.3 Log Aggregation

Structured JSON logs (via structlog) can be shipped to:
- **Datadog**
- **Papertrail**
- **CloudWatch** (AWS)
- **Google Cloud Logging**

Configure by piping Docker logs to the log aggregator of choice.
