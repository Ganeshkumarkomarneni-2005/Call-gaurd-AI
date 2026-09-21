# CallGuard AI — Architecture Document

**Document ID:** ARCH-001  
**Version:** 1.0  
**Date:** 2026-09-17  
**Status:** Draft  

---

## Table of Contents

1. [System Architecture Overview](#1-system-architecture-overview)
2. [Component Diagram](#2-component-diagram)
3. [Data Flow Diagram](#3-data-flow-diagram)
4. [Agent Architecture](#4-agent-architecture)
5. [Voice Pipeline](#5-voice-pipeline)
6. [WebSocket Event Catalog](#6-websocket-event-catalog)
7. [Database ER Overview](#7-database-er-overview)
8. [ML Pipeline](#8-ml-pipeline)
9. [Decision Engine](#9-decision-engine)
10. [Deployment Architecture](#10-deployment-architecture)
11. [Security Architecture](#11-security-architecture)

---

## 1. System Architecture Overview

CallGuard AI follows a **layered, agent-based architecture** with clean separation between:
- Infrastructure layer (telephony, STT, TTS, LLM adapters)
- Core business logic (agent orchestrator, risk engine, decision engine)
- Persistence layer (PostgreSQL via SQLAlchemy)
- Presentation layer (FastAPI REST + WebSocket, Next.js dashboard)

### Architectural Patterns Used

| Pattern | Application |
|---------|-------------|
| **Adapter** | All external services (telephony, STT, TTS, LLM) behind interface |
| **Agent** | Specialized agents for each classification task |
| **Repository** | Data access abstracted from business logic |
| **Event-Driven** | WebSocket events for real-time dashboard updates |
| **CQRS lite** | Read models (list/detail) separate from write operations (call processing) |
| **Strategy** | Risk score computation strategies per caller type |
| **Factory** | Provider factories for creating the correct adapter at runtime |

---

## 2. Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         CALLGUARD AI SYSTEM                                     │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                        PRESENTATION LAYER                               │   │
│  │                                                                         │   │
│  │   ┌─────────────────┐           ┌──────────────────────────────────┐   │   │
│  │   │   Next.js 14    │           │         FastAPI Server           │   │   │
│  │   │   Dashboard     │◄──────────│  REST API    │   WebSocket       │   │   │
│  │   │   (Port 3000)   │  WS/HTTP  │  /api/v1/*   │   /ws             │   │   │
│  │   └─────────────────┘           └──────────────┴───────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                         │                                       │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                         BUSINESS LOGIC LAYER                            │   │
│  │                                                                         │   │
│  │   ┌─────────────────────────────────────────────────────────────────┐  │   │
│  │   │                    AGENT ORCHESTRATOR                           │  │   │
│  │   │                                                                 │  │   │
│  │   │  ┌──────────────────┐  ┌──────────────────────────────────┐   │  │   │
│  │   │  │  Call Router     │  │    Conversation Agent            │   │  │   │
│  │   │  │  Agent           │  │    (LLM-powered dialog)          │   │  │   │
│  │   │  └──────────────────┘  └──────────────────────────────────┘   │  │   │
│  │   │                                                                 │  │   │
│  │   │  ┌───────────────┐ ┌─────────────────┐ ┌──────────────────┐  │  │   │
│  │   │  │ Intent Agent  │ │ Caller Type     │ │ Fraud Detection  │  │  │   │
│  │   │  │ (15 classes)  │ │ Agent (5 types) │ │ Agent            │  │  │   │
│  │   │  └───────────────┘ └─────────────────┘ └──────────────────┘  │  │   │
│  │   │                                                                 │  │   │
│  │   │  ┌───────────────┐ ┌─────────────────┐ ┌──────────────────┐  │  │   │
│  │   │  │ Recruitment   │ │ Recruitment Info │ │ Handoff Agent    │  │  │   │
│  │   │  │ Detect. Agent │ │ Extraction Agent │ │                  │  │  │   │
│  │   │  └───────────────┘ └─────────────────┘ └──────────────────┘  │  │   │
│  │   │                                                                 │  │   │
│  │   │  ┌──────────────────────────────────────────────────────────┐ │  │   │
│  │   │  │               Decision Agent                             │ │  │   │
│  │   │  │  Risk Engine ──► Decision Matrix ──► Action Dispatcher   │ │  │   │
│  │   │  └──────────────────────────────────────────────────────────┘ │  │   │
│  │   └─────────────────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                         │                                       │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                         INFRASTRUCTURE LAYER                            │   │
│  │                                                                         │   │
│  │  ┌────────────────┐ ┌──────────────┐ ┌──────────────┐ ┌─────────────┐ │   │
│  │  │ Telephony      │ │ STT Adapter  │ │ TTS Adapter  │ │ LLM Adapter │ │   │
│  │  │ Adapter        │ │              │ │              │ │             │ │   │
│  │  │ Exotel / Mock  │ │ Google /     │ │ Google /     │ │ OpenAI /    │ │   │
│  │  │                │ │ Deepgram /   │ │ ElevenLabs / │ │ Gemini /    │ │   │
│  │  │                │ │ Mock         │ │ Mock         │ │ Mock        │ │   │
│  │  └────────────────┘ └──────────────┘ └──────────────┘ └─────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                         │                                       │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                          PERSISTENCE LAYER                              │   │
│  │                                                                         │   │
│  │          PostgreSQL 16                    SQLAlchemy 2.0 ORM            │   │
│  │          (tables: calls, transcripts,     (async with asyncpg)          │   │
│  │           classifications, users,                                        │   │
│  │           recruitment_info, audit_log)                                   │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Data Flow Diagram

### 3.1 Inbound Call Flow

```
                    ┌──────────────────────────────────────────────────────┐
                    │                 INBOUND CALL FLOW                    │
                    └──────────────────────────────────────────────────────┘

[Caller dials]
      │
      ▼
[Exotel/Mock receives call]
      │  (webhook POST /telephony/inbound)
      ▼
[Call Router Agent]
      │  Creates Call record (status=INTERCEPTED)
      │  Pushes WebSocket: call.started
      ▼
[Telephony Adapter answers call]
      │  Plays TTS greeting
      ▼
[Conversation Agent — Turn 1]
      │  Plays: "Please state your name, organization, and purpose"
      │  Records caller audio
      │  STT → Transcript Turn 1
      │  LLM generates follow-up question
      │  TTS → audio response
      ▼
[Conversation Agent — Turn 2]
      │  Records caller audio
      │  STT → Transcript Turn 2
      │  LLM assesses if sufficient info collected
      │  If sufficient: proceed to classification
      │  If not: Turn 3
      ▼
[Conversation Agent — Turn 3 (max)]
      │  Final audio, STT → Transcript Turn 3
      │
      │  WebSocket push: call.transcript (per turn)
      ▼
[Agent Orchestrator — Parallel Classification]
      │
      ├── [Intent Agent] ──────────────────► intent, top3_scores
      ├── [Caller Type Agent] ──────────────► caller_type, confidence
      ├── [Fraud Detection Agent] ──────────► fraud_score
      └── [Recruitment Detection Agent] ────► recruitment_scam_score
                                              (if applicable)
      │
      │  (await all parallel tasks)
      ▼
[Risk Engine]
      │  Computes composite risk_score
      │  Applies hard overrides
      │  → risk_level (LOW/MEDIUM/HIGH/CRITICAL)
      ▼
[Decision Agent]
      │  Applies decision matrix
      │  → action (PASS/SCREEN/BLOCK/HUMAN_HANDOFF)
      │  WebSocket push: call.classified + call.action
      ▼
[Action Dispatcher]
      │
      ├── PASS ────────► Connect call to recipient
      ├── SCREEN ──────► Hold call, push live transcript to dashboard
      │                  Await manual override (30s timeout → BLOCK)
      ├── BLOCK ───────► Terminate call from caller side
      │                  Play: "This number is not available"
      └── HUMAN_HANDOFF► Ring recipient phone + dashboard notification
                         Recipient decides

      │
      ▼
[Call ends]
      │  Update Call record (status=ENDED, duration, final_action)
      │  WebSocket push: call.ended
      ▼
[Database]
      Complete record stored:
      - Call metadata
      - Full transcript (all turns)
      - All classification results
      - Risk score + level
      - Action taken
      - Any manual override
```

---

## 4. Agent Architecture

The system uses **9 specialized agents**, each with a single, well-defined responsibility.

### Agent 1: Call Router Agent

**File:** `backend/agents/call_router.py`  
**Responsibility:** Entry point for all calls. Creates DB record, routes to conversation.  
**Inputs:** Telephony webhook payload  
**Outputs:** `Call` DB record; triggers `Conversation Agent`  
**Async:** Yes  

```python
class CallRouterAgent:
    async def handle_inbound(self, payload: TelephonyPayload) -> Call:
        """Create call record, initialize pipeline, start conversation."""
```

---

### Agent 2: Conversation Agent

**File:** `backend/agents/conversation.py`  
**Responsibility:** Conduct scripted + LLM-guided conversation with caller (max 3 turns).  
**Inputs:** `Call` object, telephony adapter, STT adapter, TTS adapter, LLM adapter  
**Outputs:** `List[ConversationTurn]` stored in `call_transcripts` table  
**Async:** Yes (each turn is async I/O)  

**Dialog Strategy:**
- Turn 1: Greeting + open-ended "state your purpose"
- Turn 2: Targeted follow-up based on Turn 1 content (LLM-generated)
- Turn 3: Final clarification if ambiguous

---

### Agent 3: Intent Classification Agent

**File:** `backend/agents/intent_classifier.py`  
**Responsibility:** Classify caller intent into 15 categories.  
**Model:** DistilBERT fine-tuned on CLINC150 + BANKING77 + custom data  
**Inputs:** Full transcript string  
**Outputs:** `IntentResult(intent: str, confidence: float, top3: List[Tuple[str, float]])`  
**Latency target:** < 200ms  

---

### Agent 4: Caller Type Detection Agent

**File:** `backend/agents/caller_type.py`  
**Responsibility:** Identify what type of entity is calling.  
**Model:** Logistic Regression / SVM on TF-IDF features + keywords  
**Inputs:** Full transcript string + metadata  
**Outputs:** `CallerTypeResult(caller_type: str, confidence: float)`  
**Latency target:** < 100ms  

---

### Agent 5: Fraud Detection Agent

**File:** `backend/agents/fraud_detector.py`  
**Responsibility:** Detect fraud signals and compute fraud probability.  
**Model:** XGBoost / DistilBERT on FTC data + custom patterns  
**Inputs:** Full transcript string  
**Outputs:** `FraudResult(fraud_score: float, signals: List[str])`  
**Latency target:** < 200ms  
**Hard rules:** OTP request → minimum 0.90 score  

---

### Agent 6: Recruitment Detection Agent

**File:** `backend/agents/recruitment_detector.py`  
**Responsibility:** Detect if a recruitment call is legitimate or a scam.  
**Model:** DistilBERT fine-tuned on custom recruitment scam corpus  
**Inputs:** Full transcript string (invoked only if intent=OFFER_JOB or caller_type=RECRUITER)  
**Outputs:** `RecruitmentResult(scam_score: float, is_scam: bool, signals: List[str])`  
**Latency target:** < 200ms  

---

### Agent 7: Recruitment Info Extraction Agent

**File:** `backend/agents/recruitment_extractor.py`  
**Responsibility:** Extract structured information from legitimate recruiter calls.  
**Model:** spaCy NER + rule-based extraction  
**Inputs:** Full transcript string (invoked only if `scam_score < 0.3`)  
**Outputs:** `RecruitmentInfo(company, role, salary_range, location, contact_name)`  
**Latency target:** < 100ms  

---

### Agent 8: Risk Engine

**File:** `backend/agents/risk_engine.py`  
**Responsibility:** Fuse all agent outputs into a single risk score.  
**Type:** Rule-based (no ML model — pure computation)  
**Inputs:** `IntentResult`, `CallerTypeResult`, `FraudResult`, `RecruitmentResult`  
**Outputs:** `RiskResult(risk_score: float, risk_level: RiskLevel, explanation: str)`  
**Latency target:** < 10ms (no I/O)  

---

### Agent 9: Decision Agent

**File:** `backend/agents/decision_agent.py`  
**Responsibility:** Translate risk score into a discrete action.  
**Type:** Rule-based decision matrix  
**Inputs:** `RiskResult`, `IntentResult`, call metadata  
**Outputs:** `Decision(action: Action, reason: str, confidence: float)`  
**Latency target:** < 10ms (no I/O)  

---

### Agent Orchestrator

**File:** `backend/agents/orchestrator.py`  
**Responsibility:** Coordinate agents, manage parallel execution, handle failures.  

```python
async def run_pipeline(call: Call, transcript: str) -> PipelineResult:
    # Run classification agents in parallel
    intent_task = asyncio.create_task(intent_agent.classify(transcript))
    caller_type_task = asyncio.create_task(caller_type_agent.classify(transcript))
    fraud_task = asyncio.create_task(fraud_agent.classify(transcript))
    
    intent_result, caller_type_result, fraud_result = await asyncio.gather(
        intent_task, caller_type_task, fraud_task,
        return_exceptions=True  # Never let one failure crash everything
    )
    
    # Conditional: recruitment agents
    if should_run_recruitment(intent_result, caller_type_result):
        recruitment_result = await recruitment_agent.classify(transcript)
        if not recruitment_result.is_scam:
            extraction_result = await extractor_agent.extract(transcript)
    
    # Sequential: risk + decision
    risk_result = risk_engine.compute(intent_result, caller_type_result, fraud_result, ...)
    decision = decision_agent.decide(risk_result, intent_result)
    
    return PipelineResult(...)
```

---

## 5. Voice Pipeline

```
CALLER AUDIO
     │
     ▼ (binary audio stream via telephony adapter)
┌─────────────────────┐
│  STT Adapter        │
│  ─────────────────  │
│  Provider:          │
│  • Google Speech    │
│  • Deepgram         │
│  • Mock (returns    │
│    scripted text)   │
└────────┬────────────┘
         │ transcript: str
         ▼
┌─────────────────────┐
│  Text Processing    │
│  ─────────────────  │
│  • Normalize        │
│  • Remove filler    │
│  • Lowercase        │
└────────┬────────────┘
         │ clean_transcript: str
         ▼
     [Agent Pipeline]
         │
         │ response_text: str
         ▼
┌─────────────────────┐
│  TTS Adapter        │
│  ─────────────────  │
│  Provider:          │
│  • Google TTS       │
│  • ElevenLabs       │
│  • Mock (logs text) │
└────────┬────────────┘
         │ audio_bytes
         ▼
CALLER HEARS RESPONSE
```

**Latency Budget (per turn):**
```
STT processing:     ≤ 1000ms
Text processing:    ≤   50ms
LLM response gen:   ≤  500ms (or mock: 0ms)
TTS synthesis:      ≤  500ms (or mock: 0ms)
─────────────────────────────
Total per turn:     ≤ 2050ms (~2 seconds)
```

---

## 6. WebSocket Event Catalog

All events are JSON objects sent from server to connected dashboard clients.

### `call.started`
```json
{
  "event": "call.started",
  "call_id": "01J8XXXXXXXXXX",
  "from_number": "+91XXXXXXXXXX",
  "to_number": "+91XXXXXXXXXX",
  "timestamp": "2026-09-17T10:30:00Z",
  "telephony_provider": "mock"
}
```

### `call.transcript`
```json
{
  "event": "call.transcript",
  "call_id": "01J8XXXXXXXXXX",
  "turn_number": 1,
  "speaker": "CALLER",
  "text": "Hi, I am calling from Infosys HR department...",
  "timestamp": "2026-09-17T10:30:05Z"
}
```

### `call.classified`
```json
{
  "event": "call.classified",
  "call_id": "01J8XXXXXXXXXX",
  "intent": "OFFER_JOB",
  "intent_confidence": 0.87,
  "caller_type": "RECRUITER",
  "caller_type_confidence": 0.79,
  "fraud_score": 0.12,
  "recruitment_scam_score": 0.08,
  "risk_score": 0.14,
  "risk_level": "LOW",
  "timestamp": "2026-09-17T10:30:15Z"
}
```

### `call.action`
```json
{
  "event": "call.action",
  "call_id": "01J8XXXXXXXXXX",
  "action": "PASS",
  "reason": "Risk level LOW with high-confidence recruiter intent",
  "timestamp": "2026-09-17T10:30:16Z"
}
```

### `call.screen`
```json
{
  "event": "call.screen",
  "call_id": "01J8XXXXXXXXXX",
  "risk_score": 0.45,
  "risk_level": "MEDIUM",
  "summary": "Caller from unknown number requesting payment discussion",
  "timeout_seconds": 30,
  "timestamp": "2026-09-17T10:30:16Z"
}
```

### `call.ended`
```json
{
  "event": "call.ended",
  "call_id": "01J8XXXXXXXXXX",
  "final_status": "BLOCKED",
  "duration_seconds": 23,
  "timestamp": "2026-09-17T10:30:30Z"
}
```

### `system.health`
```json
{
  "event": "system.health",
  "component": "database",
  "status": "healthy",
  "timestamp": "2026-09-17T10:30:00Z"
}
```

---

## 7. Database ER Overview

```
┌──────────────────┐         ┌──────────────────────┐
│      users       │         │        calls          │
│──────────────────│         │──────────────────────│
│ id (UUID, PK)    │         │ id (ULID, PK)         │
│ email            │         │ from_number           │
│ password_hash    │         │ to_number             │
│ name             │         │ status                │
│ role             │         │ created_at            │
│ created_at       │         │ answered_at           │
│ last_login       │         │ ended_at              │
└──────────────────┘         │ duration_seconds      │
                             │ telephony_provider    │
                             │ telephony_call_id     │
                             │ caller_type           │
                             │ intent                │
                             │ fraud_score           │
                             │ risk_score            │
                             │ risk_level            │
                             │ action_taken          │
                             │ action_reason         │
                             │ override_by (FK→users)│
                             └──────────┬───────────┘
                                        │ 1
                              ┌─────────┴──────────┐
                              │                    │
                    ┌─────────▼─────────┐ ┌────────▼──────────────┐
                    │  call_transcripts  │ │  call_classifications  │
                    │───────────────────│ │───────────────────────│
                    │ id (UUID, PK)      │ │ id (UUID, PK)          │
                    │ call_id (FK)       │ │ call_id (FK)           │
                    │ turn_number        │ │ agent_name             │
                    │ speaker (CALLER/   │ │ result_json (JSONB)    │
                    │   SYSTEM)          │ │ confidence             │
                    │ text               │ │ latency_ms             │
                    │ timestamp          │ │ error (nullable)       │
                    │ stt_confidence     │ │ created_at             │
                    └────────────────────┘ └────────────────────────┘

                    ┌────────────────────┐ ┌────────────────────────┐
                    │  recruitment_info  │ │      audit_log          │
                    │───────────────────│ │───────────────────────│
                    │ id (UUID, PK)      │ │ id (UUID, PK)           │
                    │ call_id (FK)       │ │ timestamp               │
                    │ company_name       │ │ user_id (FK, nullable)  │
                    │ job_title          │ │ action_type             │
                    │ salary_range       │ │ resource_type           │
                    │ location           │ │ resource_id             │
                    │ contact_person     │ │ details (JSONB)         │
                    │ follow_up_action   │ └────────────────────────┘
                    │ extracted_at       │
                    └────────────────────┘
```

---

## 8. ML Pipeline

### 8.1 Training Pipeline

```
Raw Dataset
    │
    ▼
[Data Loading]        ml/data_loaders/
    │  CLINC150, BANKING77, FTC, Custom CSV
    ▼
[Data Cleaning]       ml/preprocessing/
    │  Remove duplicates, fix encoding, normalize text
    ▼
[Preprocessing]       ml/preprocessing/
    │  Tokenize, lowercase, remove stopwords
    │  Augmentation: synonym replacement, back-translation
    ▼
[Train/Val/Test Split]
    │  80/10/10 stratified by class
    ▼
[Model Training]      ml/models/
    │  DistilBERT fine-tuning (intent, fraud, recruitment)
    │  Logistic Regression / SVM (caller type)
    │  XGBoost (fraud secondary model)
    ▼
[Evaluation]          ml/evaluate.py
    │  Accuracy, F1 (macro + weighted), Precision, Recall
    │  Confusion matrix
    │  Per-class metrics
    ▼
[Model Serialization]
    │  .pt files (PyTorch), .pkl files (sklearn)
    │  Saved to ml/models/
    ▼
[Integration]
    │  Loaded by agents at startup
    │  Inference in forward pass
```

### 8.2 Inference Pipeline (per call)

```python
# Simplified inference flow
transcript = " ".join(turn.text for turn in call.transcript_turns)

# Parallel inference
intent_result = intent_model.predict(transcript)        # DistilBERT
caller_type_result = caller_type_model.predict(transcript)  # sklearn
fraud_result = fraud_model.predict(transcript)          # XGBoost / DistilBERT

# Risk fusion
risk_score = risk_engine.compute(intent_result, caller_type_result, fraud_result)
```

---

## 9. Decision Engine

### 9.1 Risk Score Formula

```
risk_score = clamp(
    fraud_score * 0.50
    + intent_risk_weight(intent) * 0.25
    + recruitment_scam_score * 0.15
    + caller_type_risk_weight(caller_type) * 0.10,
    0.0, 1.0
)
```

**Intent risk weights:**

| Intent | Risk Weight |
|--------|------------|
| REQUEST_OTP | 1.0 |
| LEGAL_THREAT | 0.9 |
| VERIFY_IDENTITY | 0.7 |
| COLLECT_PAYMENT | 0.5 |
| LOAN_OFFER | 0.4 |
| TECHNICAL_SUPPORT | 0.4 |
| SELL_PRODUCT | 0.2 |
| OFFER_JOB | 0.2 |
| APPOINTMENT_REMINDER | 0.05 |
| DELIVERY_NOTIFICATION | 0.05 |
| UNKNOWN | 0.5 |

**Caller type risk weights:**

| Caller Type | Risk Weight |
|------------|------------|
| UNKNOWN | 0.6 |
| TELEMARKETER | 0.4 |
| RECRUITER | 0.2 |
| BANK | 0.2 |
| HEALTHCARE | 0.2 |

**Hard override rules (applied after weighted score):**

```python
if "OTP" in signals or "PIN" in signals:
    risk_score = max(0.90, risk_score)
if "arrest" in signals or "warrant" in signals:
    risk_score = max(0.85, risk_score)
if "advance fee" in signals or "registration fee" in signals:
    risk_score = max(0.80, risk_score)
if "Aadhaar" in signals and "share" in signals:
    risk_score = max(0.80, risk_score)
```

### 9.2 Decision Matrix

| Risk Level | Intent | Caller Type | Action |
|------------|--------|-------------|--------|
| LOW | Any | Any | PASS |
| MEDIUM | VERIFY_IDENTITY | Any | HUMAN_HANDOFF |
| MEDIUM | COLLECT_PAYMENT | UNKNOWN | HUMAN_HANDOFF |
| MEDIUM | Other | Any | SCREEN |
| HIGH | Any | Any | HUMAN_HANDOFF |
| HIGH | fraud_score > 0.75 | Any | BLOCK |
| CRITICAL | Any | Any | BLOCK |

---

## 10. Deployment Architecture

### 10.1 Development

```
[Developer Machine]
│
├── Python venv
│   └── uvicorn backend.main:app --reload
│
├── PostgreSQL (local or Docker)
│
└── Next.js (npm run dev)
```

### 10.2 Docker Compose (Staging)

```
Docker Host
│
├── callguard_backend (Port 8000)
├── callguard_frontend (Port 3000)
├── callguard_postgres (Port 5432, volume: postgres_data)
└── callguard_redis (Port 6379, volume: redis_data)
```

### 10.3 Production Cloud

```
Internet
    │
    ├── Vercel (CDN Edge)
    │   └── Next.js frontend (global edge network)
    │
    └── Railway / Render
        └── FastAPI backend (Docker container)
            └── Neon / Supabase (managed PostgreSQL)
```

---

## 11. Security Architecture

### 11.1 Authentication Flow

```
[User] POST /auth/login (email + password)
         │
         ▼
[Backend] Verify password (bcrypt)
         │
         ├── Issue JWT access token (15 min)
         └── Issue JWT refresh token (7 days)
         │
         ▼
[User] All requests: Authorization: Bearer <access_token>
         │
         ▼
[Backend] Verify JWT signature + expiry
         │
         └── Extract user_id → load user from DB
```

### 11.2 API Security Layers

```
[Request]
    │
    ▼ Rate Limiter (100 req/min per IP on /auth/*)
    │
    ▼ CORS Check (only CORS_ORIGINS allowed)
    │
    ▼ JWT Verification (all /api/v1/* except /health)
    │
    ▼ Pydantic Validation (all request bodies)
    │
    ▼ SQLAlchemy ORM (no raw SQL, no injection possible)
    │
    ▼ Business Logic
```

### 11.3 Data Security

| Data | Storage | Encryption | Retention |
|------|---------|-----------|-----------|
| Transcripts | PostgreSQL | DB-level encryption | 90 days |
| Risk scores | PostgreSQL | DB-level encryption | Indefinite |
| Passwords | PostgreSQL | bcrypt hash only | Indefinite |
| JWT keys | Environment variable | Never stored in DB | N/A |
| API keys (external) | Environment variable | Never in code/DB | N/A |
| Audio | NOT stored | N/A | Never persisted |

> **Audio is never persisted.** Only the text transcript is stored. Audio is processed in-memory and discarded.

### 11.4 Safe Logging Policy

```python
# ✅ ALLOWED in logs
logger.info("call_processed", call_id=call.id, risk_level="HIGH", action="BLOCK")

# ❌ NEVER IN LOGS
logger.info("call_processed", phone_number=call.from_number)  # PII
logger.info("transcript", text=turn.text)                      # PII
logger.info("user_login", email=user.email)                    # PII
```
