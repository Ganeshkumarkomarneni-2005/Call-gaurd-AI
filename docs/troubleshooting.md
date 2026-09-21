# CallGuard AI — Troubleshooting Guide

**Version:** 1.0  
**Last Updated:** 2026-09-21

---

## 1. Backend Issues

### 1.1 Server won't start

**Error:** `ModuleNotFoundError: No module named 'backend'`

**Fix:**
```bash
# Run from project root, not from backend/
cd "d:\Call gaurd AI"
python -m uvicorn backend.main:app --reload
```

---

**Error:** `ModuleNotFoundError: No module named 'fastapi'`

**Fix:**
```bash
pip install -r requirements.txt
```

---

**Error:** `pydantic_settings.env_settings.BaseSettings` import error

**Fix:**
```bash
pip install pydantic-settings==2.5.2
```

---

**Error:** `sqlalchemy.exc.OperationalError: could not connect to server`

**Fix:** PostgreSQL is not running. Start it:
```bash
docker-compose up postgres -d
```
Or use SQLite for development by changing `DATABASE_URL` in `.env`.

---

**Error:** `AttributeError: 'Settings' object has no attribute 'version'`

**Fix:** Check `backend/core/config.py`. The `version` field may be missing:
```python
version: str = "0.1.0"
```

---

### 1.2 Database Issues

**Error:** `asyncpg.exceptions.InvalidCatalogNameError: database "callguard" does not exist`

**Fix:**
```bash
docker exec -it callguard-postgres psql -U callguard -c "CREATE DATABASE callguard;"
```
Or run:
```bash
docker-compose up -d postgres
```
The docker-compose creates the database automatically.

---

**Error:** `alembic.util.exc.CommandError: Can't locate revision`

**Fix:**
```bash
alembic upgrade head
```

---

**Error:** `sqlalchemy.exc.ProgrammingError: relation "users" does not exist`

**Fix:** Tables not created. Run:
```bash
python -c "import asyncio; from backend.db.base import init_db; asyncio.run(init_db())"
```

---

### 1.3 Authentication Issues

**Error:** `401 Unauthorized` on all requests

**Fix:** Include the Authorization header:
```
Authorization: Bearer <your_token>
```
Token is obtained from `POST /api/v1/auth/login`.

---

**Error:** JWT token expired

**Fix:** Login again to get a new token. Increase `ACCESS_TOKEN_EXPIRE_MINUTES` in `.env` for development.

---

### 1.4 Test Failures

**Error:** `pytest: command not found`

**Fix:**
```bash
pip install pytest pytest-asyncio pytest-cov
```

---

**Error:** `ImportError` during test collection

**Fix:** Run tests from project root:
```bash
cd "d:\Call gaurd AI"
pytest backend/tests/ -v
```

---

**Error:** `RuntimeError: Timeout context manager should be used inside a task`

**Fix:** Add `asyncio_mode = "auto"` to `pytest.ini` or `pyproject.toml`:
```ini
[pytest]
asyncio_mode = auto
```

---

**Error:** Tests fail with `aiosqlite` not found

**Fix:**
```bash
pip install aiosqlite==0.20.0
```

---

## 2. Docker Issues

### 2.1 docker-compose errors

**Error:** `Cannot connect to the Docker daemon`

**Fix:** Start Docker Desktop on Windows.

---

**Error:** Port 5432 already in use

**Fix:**
```bash
# Stop local PostgreSQL if running
net stop postgresql-x64-16  # Windows

# Or change the port in docker-compose.yml
ports:
  - "5433:5432"
```

---

**Error:** `docker-compose: command not found`

**Fix:** Use `docker compose` (newer syntax):
```bash
docker compose up -d
```

---

## 3. ML / Colab Issues

### 3.1 Notebook won't load in Colab

**Fix:** Ensure the `.ipynb` files are valid JSON:
```bash
python -c "import json; json.load(open('ml/notebooks/01_data_understanding.ipynb'))"
```

---

### 3.2 HuggingFace dataset download fails in Colab

**Error:** `ConnectionError` or timeout

**Fix:**
```python
# In Colab, add retry logic:
import os
os.environ['HF_DATASETS_OFFLINE'] = '0'
# Or use:
dataset = load_dataset("clinc_oos", "plus", download_mode="force_redownload")
```

---

### 3.3 GPU not available in Colab

**Fix:** Runtime → Change runtime type → GPU (T4)

> [!NOTE]
> GPU is only needed for DistilBERT fine-tuning in notebooks 03 and 07.
> All other notebooks can run on CPU.

---

### 3.4 `ModuleNotFoundError` in Colab notebooks

**Fix:** Each notebook has a setup cell:
```python
!pip install scikit-learn pandas numpy matplotlib seaborn datasets transformers
```
Run this cell first.

---

### 3.5 Synthetic data generator fails

**Error:** `json.JSONDecodeError` when loading synthetic_conversations.jsonl

**Fix:** Regenerate:
```bash
cd "d:\Call gaurd AI"
python ml/scripts/synthetic_data_generator.py
```

---

## 4. Frontend Issues (Phase 22 — not yet built)

> [!NOTE]
> The frontend has not been built yet. These are anticipated issues.

**Error:** `npm: command not found`

**Fix:** Install Node.js from https://nodejs.org/

---

**Error:** `next: command not found`

**Fix:**
```bash
cd frontend
npm install
npm run dev
```

---

**Error:** API connection refused

**Fix:** Ensure backend is running on port 8000:
```bash
python -m uvicorn backend.main:app --reload --port 8000
```
Check `NEXT_PUBLIC_API_URL=http://localhost:8000` in `.env.local`.

---

## 5. Mock Provider Issues

### 5.1 Mock telephony call not creating

**Error:** `422 Unprocessable Entity` on POST /calls/incoming

**Fix:** Ensure all required fields:
```json
{
  "caller_number": "+911234567890",
  "virtual_number": "+919999999999",
  "telephony_call_id": "test-001",
  "telephony_provider": "mock"
}
```

---

### 5.2 Mock LLM returning unexpected responses

**Fix:** MockLLMProvider returns from a predefined response dict. Check `backend/services/llm/mock_llm.py` for available response templates.

---

## 6. Environment Variables

### Missing .env file

**Fix:**
```bash
cp .env.example .env
# Edit .env with your values
```

### Secrets showing in logs

**Fix:** Never set `DEBUG=true` in production. Ensure logging_config.py filters:
```python
# Already implemented in backend/core/logging_config.py
# Sensitive fields are excluded from log output
```

---

## 7. Windows-Specific Issues

### PowerShell `&&` not supported

**Fix:** Use separate commands:
```powershell
cd "d:\Call gaurd AI"
python -m uvicorn backend.main:app --reload
```

### Path issues with spaces in directory name

**Fix:** Always quote the path:
```powershell
cd "d:\Call gaurd AI"
```

### Python not found

**Fix:** Install Python 3.11 from python.org and add to PATH. Verify:
```powershell
python --version
```

---

## 8. Getting Help

1. Check `docs/project-status.md` for current known issues
2. Check `docs/api.md` for correct endpoint formats
3. Run `GET /health` to verify the backend is running
4. Check structured logs — all events include `call_id`, `component`, `event`, `timestamp`
