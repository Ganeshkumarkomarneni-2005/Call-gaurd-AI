# CallGuard AI

```
  ██████╗ █████╗ ██╗     ██╗      ██████╗ ██╗   ██╗ █████╗ ██████╗ ██████╗      █████╗ ██╗
 ██╔════╝██╔══██╗██║     ██║     ██╔════╝ ██║   ██║██╔══██╗██╔══██╗██╔══██╗    ██╔══██╗██║
 ██║     ███████║██║     ██║     ██║  ███╗██║   ██║███████║██████╔╝██║  ██║    ███████║██║
 ██║     ██╔══██║██║     ██║     ██║   ██║██║   ██║██╔══██║██╔══██╗██║  ██║    ██╔══██║██║
 ╚██████╗██║  ██║███████╗███████╗╚██████╔╝╚██████╔╝██║  ██║██║  ██║██████╔╝    ██║  ██║██║
  ╚═════╝╚═╝  ╚═╝╚══════╝╚══════╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝     ╚═╝  ╚═╝╚═╝
```

> **Real-time AI call screening that understands intent, not just caller identity.**

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green.svg)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active_Development-orange.svg)]()

---

## Table of Contents

1. [Problem Statement](#problem-statement)
2. [Why Existing Solutions Fail](#why-existing-solutions-fail)
3. [Core Intelligence Principle](#core-intelligence-principle)
4. [Architecture Overview](#architecture-overview)
5. [Features](#features)
6. [Tech Stack](#tech-stack)
7. [ML Pipeline](#ml-pipeline)
8. [Datasets](#datasets)
9. [Installation](#installation)
10. [Environment Variables](#environment-variables)
11. [Running Locally](#running-locally)
12. [Running with Docker](#running-with-docker)
13. [Testing](#testing)
14. [ML Evaluation](#ml-evaluation)
15. [Deployment](#deployment)
16. [Demo Scenarios](#demo-scenarios)
17. [Limitations](#limitations)
18. [Future Improvements](#future-improvements)
19. [License](#license)

---

## Problem Statement

India sees **over 1.5 billion spam calls per month**. These aren't just annoying — they include:

- **Fraudulent banking calls** that impersonate RBI / SBI officers and steal OTPs
- **Fake job recruitment scams** targeting fresh graduates with advance-fee fraud
- **Loan fraud calls** promising instant credit with document theft as the goal
- **Insurance fraud calls** that collect premium payments and disappear
- **Sextortion calls** using scripted social engineering

Existing approaches: blacklists (Truecaller, DND registry) fail because:
1. Numbers rotate faster than lists can update
2. A legitimate recruiter's number can appear on a spam list
3. A registered telemarketer can still commit fraud
4. Intent cannot be inferred from a phone number

**CallGuard AI** intercepts calls in real-time, conducts a short automated conversation with the caller, classifies intent and risk, and notifies the call recipient — before they ever have to pick up.

---

## Why Existing Solutions Fail

| Solution | Mechanism | Failure Mode |
|----------|-----------|--------------|
| DND Registry | Block telemarketer numbers | Spoofed numbers bypass it |
| Truecaller | Crowdsourced spam labeling | False positives (legitimate numbers flagged), false negatives (new numbers) |
| Carrier-level spam detection | Statistical call pattern analysis | Cannot detect scripted social engineering |
| Call blocking apps | Known number blacklists | Fails for first-time fraud numbers |
| Voicemail screening | Passive — records after connection | No real-time action |

**None of these solutions understand what the caller is saying or what they want.**

---

## Core Intelligence Principle

> **CALLER TYPE ≠ INTENT ≠ RISK ≠ ACTION**

This is the fundamental insight that drives CallGuard AI's design:

```
Caller Type   → WHO is calling?         (telemarketer, recruiter, bank, unknown)
     ≠
Intent        → WHAT do they want?      (sell product, offer job, collect payment, extract OTP)
     ≠
Risk Level    → HOW dangerous is it?    (low, medium, high, critical)
     ≠
Action        → WHAT should we do?      (pass through, screen, block, alert, hand off)
```

**Examples:**

- A **legitimate bank** (known caller type) calling to **collect loan payment** (benign intent) → **Low risk** → **Pass through**
- A **recruiter** (known caller type) requesting **immediate advance fee payment** (fraud intent) → **Critical risk** → **Block + Alert**
- An **unknown number** just **confirming appointment time** (benign intent) → **Low risk** → **Pass through**
- A **registered telemarketer** asking for **Aadhaar + OTP** (fraud intent) → **Critical risk** → **Block + Alert**

Each dimension is classified independently by a dedicated ML model or agent.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CALLGUARD AI SYSTEM                               │
│                                                                             │
│  INBOUND CALL                                                               │
│  ───────────                                                                │
│  Caller ──────► Exotel / Mock ──────► Call Router Agent                    │
│                  (Telephony)                │                               │
│                                             ▼                               │
│                                    ┌─────────────────┐                     │
│                                    │  Voice Pipeline │                     │
│                                    │  STT → Text     │                     │
│                                    │  Text → TTS     │                     │
│                                    └────────┬────────┘                     │
│                                             │                               │
│                              ┌──────────────▼───────────────┐              │
│                              │     AI Agent Orchestrator     │              │
│                              │  ┌──────────────────────────┐│              │
│                              │  │  Conversation Agent      ││              │
│                              │  │  (manages dialog flow)   ││              │
│                              │  └──────────┬───────────────┘│              │
│                              │             │  parallel      │              │
│                              │   ┌─────────┼─────────┐      │              │
│                              │   ▼         ▼         ▼      │              │
│                              │  Intent  Caller   Fraud      │              │
│                              │  Agent   Type     Detection  │              │
│                              │          Agent    Agent      │              │
│                              │   ┌─────────┼─────────┐      │              │
│                              │   ▼         ▼         ▼      │              │
│                              │  Risk    Recruit.  Handoff   │              │
│                              │  Engine  Detector  Agent     │              │
│                              │          Agent               │              │
│                              │             │                 │              │
│                              │   ┌─────────▼─────────┐      │              │
│                              │   │   Decision Agent  │      │              │
│                              │   └─────────┬─────────┘      │              │
│                              └─────────────┼────────────────┘              │
│                                            │                               │
│                         ┌──────────────────▼──────────────────┐           │
│                         │           ACTION DISPATCHER          │           │
│                         │  PASS │ SCREEN │ BLOCK │ ALERT       │           │
│                         └──────────────┬──────────────────────┘           │
│                                        │                                   │
│                    ┌───────────────────┼──────────────────┐               │
│                    ▼                   ▼                  ▼               │
│             WebSocket Push      Call Connected       Call Blocked         │
│             (Dashboard)         (recipient picks up)  (caller notified)   │
│                    │                                                       │
│                    ▼                                                       │
│           Next.js Dashboard                                                │
│           (Live call status,                                               │
│            risk scores, alerts)                                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Features

### Core
- 🔊 **Real-time voice pipeline** — STT → AI processing → TTS response in <2s
- 🤖 **9-agent orchestration** — Specialized agents for each classification task
- 🧠 **Multi-dimensional risk scoring** — Intent × Caller Type × Fraud signals = Risk
- 📊 **Live dashboard** — WebSocket-powered real-time call monitoring
- 🛡️ **4-tier action system** — PASS / SCREEN / BLOCK / HUMAN_HANDOFF
- 🔔 **Instant notifications** — Browser push when high-risk call detected

### Intelligence
- 🎯 **Intent Classification** — 15-class classifier trained on CLINC150 + BANKING77
- 🚨 **Fraud Detection** — Pattern matching + ML on FTC robocall dataset
- 👔 **Recruitment Scam Detection** — Specialized classifier for job offer fraud
- 📍 **Recruitment Info Extraction** — Named entity extraction (company, salary, role)
- 🏢 **Caller Type Detection** — Telemarketer / Recruiter / Bank / Healthcare / Unknown
- ⚖️ **Risk Engine** — Rule-based fusion of all signal scores

### Infrastructure
- 🔄 **Mock mode** — Full simulation without any paid API keys
- 🐘 **PostgreSQL** — Complete call history, transcripts, decisions
- 🔐 **JWT authentication** — Secure dashboard access
- 🐳 **Docker** — One-command deployment
- 📝 **Structured logging** — JSON logs via structlog

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Backend Framework** | FastAPI 0.115 | Async REST + WebSocket API |
| **Web Server** | Uvicorn | ASGI server |
| **Database ORM** | SQLAlchemy 2.0 | Async DB access |
| **Database** | PostgreSQL 16 | Persistent storage |
| **Migrations** | Alembic | Schema versioning |
| **Validation** | Pydantic v2 | Request/response schemas |
| **Auth** | python-jose + passlib | JWT tokens + bcrypt |
| **ML Framework** | PyTorch 2.4 + scikit-learn | Model training/inference |
| **Transformers** | HuggingFace Transformers | Pre-trained NLP models |
| **Embeddings** | sentence-transformers | Semantic similarity |
| **Audio** | librosa + soundfile | Audio preprocessing |
| **NLP** | NLTK + spaCy | Text preprocessing |
| **Telephony** | Exotel (+ mock) | Call management |
| **STT** | Google Speech / Deepgram (+ mock) | Speech recognition |
| **TTS** | Google TTS / ElevenLabs (+ mock) | Voice synthesis |
| **LLM** | OpenAI / Gemini / Anthropic (+ mock) | Conversation agent |
| **Frontend** | Next.js 14 | Dashboard |
| **Logging** | structlog | Structured JSON logs |
| **Containerization** | Docker + Docker Compose | Deployment |

---

## ML Pipeline

CallGuard AI uses a **multi-model pipeline** where each model has a narrow, well-defined responsibility:

```
Raw Audio
    │
    ▼
[STT Engine] ──────► Transcript Text
                           │
         ┌─────────────────┼──────────────────────┐
         ▼                 ▼                       ▼
  [Intent           [Caller Type           [Fraud Signal
   Classifier]       Classifier]            Detector]
   15 classes        5 classes              Binary
         │                 │                       │
         └─────────────────┼───────────────────────┘
                           ▼
                    [Risk Engine]
                    Weighted fusion
                    of all scores
                           │
                           ▼
                   [Decision Agent]
                   Rule-based action
                   (PASS/SCREEN/BLOCK/HANDOFF)
```

### Models

| Model | Architecture | Task | Dataset |
|-------|-------------|------|---------|
| Intent Classifier | DistilBERT fine-tuned | 15-class text classification | CLINC150 + BANKING77 |
| Caller Type Detector | Logistic Regression / SVM | 5-class classification | Custom labeled data |
| Fraud Detector | XGBoost / DistilBERT | Binary classification | FTC data + custom |
| Recruitment Detector | DistilBERT fine-tuned | Binary + extraction | Custom dataset |
| Risk Engine | Rule-based fusion | Risk score [0.0–1.0] | N/A (rules) |

---

## Datasets

| Dataset | Purpose | Size | License |
|---------|---------|------|---------|
| CLINC150 | Intent classification baseline | 22,500 utterances | CC BY 3.0 |
| BANKING77 | Banking intent fine-tuning | 13,083 utterances | CC BY 4.0 |
| FTC Robocall Reports | Fraud call patterns | ~500K records | Public Domain |
| ASVspoof 2019 | Spoofed audio detection | 121,461 utterances | Research use |
| Custom CallGuard | Domain-specific intents | TBD | Proprietary |

See [docs/dataset-card.md](docs/dataset-card.md) for full details.

---

## Installation

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 16 (or Docker)
- Git

### Clone & Setup

```bash
# Clone the repository
git clone https://github.com/your-org/callguard-ai.git
cd callguard-ai

# Create Python virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/macOS)
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
# Edit .env with your values (or leave as mock for development)
```

### Database Setup

```bash
# Start PostgreSQL (if not using Docker)
# Create database
createdb callguard

# Run migrations
alembic upgrade head
```

### Frontend Setup

```bash
cd frontend
npm install
```

---

## Environment Variables

All environment variables are documented in [`.env.example`](.env.example).

**Key variables for quick start:**

| Variable | Default | Description |
|----------|---------|-------------|
| `TELEPHONY_PROVIDER` | `mock` | Use `mock` for development |
| `STT_PROVIDER` | `mock` | Use `mock` for development |
| `TTS_PROVIDER` | `mock` | Use `mock` for development |
| `LLM_PROVIDER` | `mock` | Use `mock` for development |
| `DATABASE_URL` | postgresql://... | PostgreSQL connection string |
| `SECRET_KEY` | (required) | JWT signing key — change this! |

> **Development mode:** Set all `*_PROVIDER` variables to `mock` — no paid API keys required.

---

## Running Locally

### Backend

```bash
# With virtual environment activated
uvicorn backend.main:app --reload --port 8000
```

Backend available at: http://localhost:8000  
API docs at: http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm run dev
```

Frontend available at: http://localhost:3000

### Simulate a Call (Mock Mode)

```bash
# POST a test call via the mock telephony endpoint
curl -X POST http://localhost:8000/api/v1/telephony/mock/inbound \
  -H "Content-Type: application/json" \
  -d '{
    "from_number": "+919876543210",
    "to_number": "+911234567890",
    "scenario": "recruitment_scam"
  }'
```

Available scenarios: `legitimate_recruiter`, `recruitment_scam`, `bank_fraud`, `legitimate_bank`, `insurance_fraud`, `appointment_reminder`, `robocall`, `unknown_caller`, `human_handoff`

---

## Running with Docker

```bash
# Build and start all services
docker compose up --build

# Run in background
docker compose up -d --build

# View logs
docker compose logs -f backend

# Stop
docker compose down

# Stop and remove volumes (WARNING: deletes database)
docker compose down -v
```

Services:
- Backend: http://localhost:8000
- Frontend: http://localhost:3000
- PostgreSQL: localhost:5432
- Redis: localhost:6379

---

## Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=backend --cov-report=html

# Run specific test category
pytest tests/unit/
pytest tests/integration/
pytest tests/api/

# Run with verbose output
pytest -v

# Run async tests
pytest --asyncio-mode=auto
```

Test report: `htmlcov/index.html`

---

## ML Evaluation

See [docs/ml-evaluation.md](docs/ml-evaluation.md) for the complete evaluation framework.

```bash
# Run ML evaluation suite (after training models)
python ml/evaluate.py --model intent_classifier --dataset clinc150
python ml/evaluate.py --model fraud_detector --dataset ftc_robocalls
python ml/evaluate.py --all
```

---

## Deployment

See [docs/deployment.md](docs/deployment.md) for full deployment guide.

**Quick summary:**

| Component | Platform | Notes |
|-----------|---------|-------|
| Frontend | Vercel | Automatic deploys from `main` branch |
| Backend | Render / Railway | Docker-based deployment |
| Database | Neon / Supabase | Managed PostgreSQL |

---

## Demo Scenarios

The system ships with 9 pre-built demo scenarios playable via mock telephony:

| # | Scenario | Expected Action |
|---|---------|----------------|
| 1 | Legitimate job recruiter | PASS |
| 2 | Recruitment advance-fee scam | BLOCK + ALERT |
| 3 | Bank fraud (OTP extraction) | BLOCK + ALERT |
| 4 | Legitimate bank (payment reminder) | PASS |
| 5 | Insurance fraud | BLOCK + ALERT |
| 6 | Appointment reminder | PASS |
| 7 | Robocall / IVR spam | BLOCK |
| 8 | Unknown caller (benign) | SCREEN |
| 9 | Call requiring human decision | HUMAN_HANDOFF |

See [docs/demo-script.md](docs/demo-script.md) for detailed scripts.

---

## Limitations

We believe in honest documentation:

1. **Mock STT is not real STT** — Mock mode uses pre-scripted text, not actual speech recognition. Real-world accuracy depends on STT provider quality.

2. **Training data bias** — Models trained primarily on English text. Indian accent, code-switching (Hinglish), and regional language mixing are not yet handled.

3. **Cold start for new fraud patterns** — New scam scripts not in training data will not be caught until models are retrained.

4. **Latency** — Full pipeline (STT + 5 models + TTS) targeting <2s but may exceed this on CPU-only systems.

5. **Not a legal substitute** — CallGuard AI does not provide legal protection. Blocking a call does not mean the caller is a criminal.

6. **Exotel dependency** — Production telephony requires an Exotel account (India-specific). Integration with other providers (Twilio, Vonage) not yet implemented.

7. **No voiceprint verification** — The system does not verify that a caller claiming to be from "HDFC Bank" is actually HDFC Bank.

---

## Future Improvements

- [ ] Multilingual support (Hindi, Tamil, Telugu, Bengali)
- [ ] Hinglish / code-switching NLP
- [ ] Voiceprint verification against known institutional numbers
- [ ] Integration with TRAI's Distributed Ledger Technology (DLT) registry
- [ ] Twilio / Vonage / AWS Connect adapters
- [ ] On-device inference for privacy (no audio leaves device)
- [ ] Federated learning from user feedback
- [ ] WhatsApp / SMS scam screening
- [ ] Proactive caller reputation API

---

## License

MIT License — see [LICENSE](LICENSE) for details.

Copyright (c) 2026 CallGuard AI

---

## Acknowledgements

- CLINC Inc. for the CLINC150 dataset
- PolyAI for the BANKING77 dataset
- FTC for public robocall complaint data
- HuggingFace for Transformers library
- The FastAPI and Pydantic teams

---

*Built with ❤️ to protect people from phone fraud.*
