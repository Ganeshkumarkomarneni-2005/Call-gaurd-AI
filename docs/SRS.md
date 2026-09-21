# CallGuard AI — Software Requirements Specification (SRS)

**Document ID:** SRS-001  
**Version:** 1.0  
**Date:** 2026-09-17  
**Status:** Draft  
**Author:** CallGuard AI Team  
**Reference:** CRS-001 v1.0

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [System Overview](#2-system-overview)
3. [Functional Requirements](#3-functional-requirements)
4. [Non-Functional Requirements](#4-non-functional-requirements)
5. [Interface Requirements](#5-interface-requirements)
6. [Constraints](#6-constraints)
7. [Assumptions](#7-assumptions)

---

## 1. Introduction

### 1.1 Purpose

This Software Requirements Specification (SRS) defines the complete set of functional and non-functional requirements for CallGuard AI version 1.0. It translates the concept requirements in CRS-001 into precise, implementable specifications.

This document is intended for:
- Software developers implementing the system
- QA engineers designing test cases
- Architects making technical decisions
- Stakeholders reviewing system scope

### 1.2 Scope

CallGuard AI is a real-time, AI-powered inbound call screening system. The system:
- Intercepts inbound calls via a telephony adapter (Exotel or Mock)
- Conducts a short automated conversation with the caller
- Classifies caller intent, type, fraud risk, and recruitment scam likelihood
- Computes a composite risk score
- Takes automatic protective action (PASS / SCREEN / BLOCK / HUMAN_HANDOFF)
- Delivers real-time notifications to the call recipient via WebSocket
- Presents a web dashboard for monitoring and manual override

### 1.3 Definitions

| Term | Definition |
|------|-----------|
| **Caller** | The person placing the inbound call |
| **Recipient** | The person who owns the CallGuard-protected number |
| **Intent** | The stated or inferred purpose of the caller |
| **Caller Type** | Category of the caller (RECRUITER, BANK, TELEMARKETER, HEALTHCARE, UNKNOWN) |
| **Risk Score** | A float in [0.0, 1.0] representing the probability that this call is harmful |
| **Risk Level** | Categorical: LOW, MEDIUM, HIGH, CRITICAL |
| **Action** | One of: PASS, SCREEN, BLOCK, HUMAN_HANDOFF |
| **Agent** | A software module that performs a specific AI classification task |
| **Mock Mode** | Operation mode where all external APIs are simulated locally |
| **Turn** | One exchange in the caller conversation (caller speaks + system responds) |
| **STT** | Speech-to-Text: converts audio to transcript |
| **TTS** | Text-to-Speech: converts text to audio |
| **LLM** | Large Language Model: used by Conversation Agent |
| **JWT** | JSON Web Token: used for authentication |

### 1.4 References

- CRS-001: Concept Requirements Specification
- docs/architecture.md: System Architecture Document
- docs/dataset-card.md: Dataset Documentation
- FastAPI Documentation: https://fastapi.tiangolo.com
- SQLAlchemy 2.0 Documentation: https://docs.sqlalchemy.org

---

## 2. System Overview

### 2.1 System Context

CallGuard AI sits between the telephony network and the call recipient. When an inbound call arrives at a CallGuard-protected number, the system intercepts it before the recipient's phone rings.

```
[Caller] → [Telephony Provider] → [CallGuard AI] → [Action] → [Recipient / Block]
```

### 2.2 Major Components

| Component | Technology | Role |
|-----------|-----------|------|
| API Server | FastAPI + Uvicorn | REST API + WebSocket |
| Database | PostgreSQL 16 + SQLAlchemy 2.0 | Persistent storage |
| Agent Orchestrator | Python asyncio | Coordinates 9 AI agents |
| Voice Pipeline | STT + TTS adapters | Audio processing |
| ML Models | PyTorch + scikit-learn | Classification models |
| Dashboard | Next.js 14 | Web UI |
| Telephony Adapter | Exotel / Mock | Call control |

### 2.3 Operational Modes

| Mode | Description |
|------|-------------|
| `production` | All providers are real (Exotel, Google Speech, etc.) |
| `development` | Mock providers for telephony, STT, TTS, LLM |
| `test` | Deterministic mock responses; in-memory database |

---

## 3. Functional Requirements

### 3.1 Call Interception (maps to CR-01)

**FR-01** The system SHALL intercept all inbound calls to a CallGuard-protected number before the recipient's phone rings.

**FR-02** The system SHALL acknowledge (answer) an intercepted call within **2 seconds** of it arriving at the telephony adapter.

**FR-03** If the system is unavailable (health check failing), the telephony adapter SHALL fall through to ring the recipient directly (fail-open for voice, fail-safe for risk).

**FR-04** The system SHALL create a `Call` database record at the moment of interception with status `INTERCEPTED`.

---

### 3.2 Automated Caller Conversation (maps to CR-02, CR-03)

**FR-05** The system SHALL greet the caller with a configurable greeting message synthesized via TTS.

**FR-06** The system SHALL ask the caller to state their name, organization, and purpose.

**FR-07** The Conversation Agent SHALL conduct a maximum of **3 turns** of dialogue with the caller.

**FR-08** Each turn SHALL complete within **10 seconds** (STT processing + LLM response + TTS synthesis).

**FR-09** If the caller does not respond within 8 seconds, the system SHALL prompt the caller once. If no response after second prompt, the system SHALL mark intent as `UNRESPONSIVE` and apply default risk handling.

**FR-10** The system SHALL store the full transcript of each turn in the `CallTranscript` database table.

**FR-11** After completing conversation turns, the system SHALL pass the full transcript to the Agent Orchestrator for classification.

---

### 3.3 Intent Classification (maps to CR-04)

**FR-12** The Intent Classification Agent SHALL classify caller intent into one of the following classes:

| Class | Description |
|-------|-------------|
| OFFER_JOB | Caller is offering or discussing employment |
| COLLECT_PAYMENT | Caller is requesting a payment |
| REQUEST_OTP | Caller is requesting a one-time password |
| VERIFY_IDENTITY | Caller is asking the recipient to verify personal info |
| SELL_PRODUCT | Caller is selling a product or service |
| INSURANCE_OFFER | Caller is offering insurance products |
| LOAN_OFFER | Caller is offering a loan |
| APPOINTMENT_REMINDER | Caller is reminding of a scheduled appointment |
| DELIVERY_NOTIFICATION | Caller is notifying about a package/delivery |
| SURVEY | Caller is conducting a survey |
| TECHNICAL_SUPPORT | Caller claims to offer technical support |
| ACCOUNT_ISSUE | Caller claims there is an account problem |
| LEGAL_THREAT | Caller makes legal or arrest threats |
| CHARITY_SOLICITATION | Caller is soliciting charitable donations |
| UNKNOWN | Intent cannot be determined |

**FR-13** The Intent Agent SHALL return confidence scores for the top-3 predicted classes.

**FR-14** If maximum confidence is < 0.5, the system SHALL treat intent as `UNKNOWN` for risk calculation.

---

### 3.4 Caller Type Detection (maps to CR-05)

**FR-15** The Caller Type Agent SHALL classify the caller into one of the following categories:

| Type | Description |
|------|-------------|
| RECRUITER | Employment / HR agency |
| BANK | Banking / financial institution |
| TELEMARKETER | Sales / marketing caller |
| HEALTHCARE | Medical / insurance caller |
| UNKNOWN | Cannot be determined |

**FR-16** Caller Type SHALL be determined from transcript content AND metadata (time of day, call duration patterns if available from telephony).

**FR-17** Caller Type SHALL be stored in the `Call` database record.

---

### 3.5 Fraud Detection (maps to CR-06)

**FR-18** The Fraud Detection Agent SHALL compute a `fraud_score` in [0.0, 1.0] representing the probability that this call is fraudulent.

**FR-19** The Fraud Detection Agent SHALL detect the following fraud pattern signals:
- OTP/PIN/password request
- Urgency language ("immediate action required", "account will be blocked")
- Impersonation signals ("I am calling from RBI/SBI/Police")
- Legal threat language ("you will be arrested", "warrant has been issued")
- Advance fee signals ("pay registration fee", "security deposit")
- Vague caller identification

**FR-20** If `fraud_score` > 0.85, the system SHALL apply a CRITICAL risk override regardless of other signals.

**FR-21** If the caller requests an OTP or PIN at any point in the transcript, `fraud_score` SHALL be set to minimum 0.90.

---

### 3.6 Recruitment Scam Detection (maps to CR-07, CR-08)

**FR-22** The Recruitment Detection Agent SHALL be invoked when `intent` is `OFFER_JOB` or `caller_type` is `RECRUITER`.

**FR-23** The Recruitment Detection Agent SHALL compute a `recruitment_scam_score` in [0.0, 1.0].

**FR-24** The following signals SHALL increase `recruitment_scam_score`:
- Request for advance fee / registration fee
- Guaranteed high salary without interview
- Request for personal documents (Aadhaar, bank details)
- No company name provided
- Unrealistic salary claims
- Request for immediate response

**FR-25** If the call is classified as a legitimate recruiter call (scam_score < 0.3), the Recruitment Info Extraction Agent SHALL extract:
- Company name (if mentioned)
- Job title / role
- Salary range (if mentioned)
- Location
- Contact person name
- Follow-up action requested

**FR-26** Extracted recruitment information SHALL be stored in the `RecruitmentInfo` database table.

---

### 3.7 Risk Score Computation (maps to CR-09)

**FR-27** The Risk Engine SHALL compute a composite `risk_score` in [0.0, 1.0] using the following formula:

```
base_score = (
    fraud_score * 0.50 +
    intent_risk_factor(intent) * 0.25 +
    recruitment_scam_score * 0.15 +
    caller_type_risk_factor(caller_type) * 0.10
)

# Hard overrides (applied AFTER weighted calculation)
if request_otp in transcript: risk_score = max(0.90, base_score)
if legal_threat in transcript: risk_score = max(0.85, base_score)
if advance_fee in transcript: risk_score = max(0.80, base_score)

final_risk_score = min(1.0, base_score)
```

**FR-28** Risk levels SHALL be derived from `risk_score`:

| Risk Level | Score Range |
|------------|------------|
| LOW | 0.00 – 0.24 |
| MEDIUM | 0.25 – 0.49 |
| HIGH | 0.50 – 0.74 |
| CRITICAL | 0.75 – 1.00 |

**FR-29** `risk_score` and `risk_level` SHALL be stored in the `Call` database record.

---

### 3.8 Decision and Action (maps to CR-10, CR-11)

**FR-30** The Decision Agent SHALL select one of 4 actions based on the decision matrix:

| Risk Level | Default Action | Override Conditions |
|------------|---------------|---------------------|
| LOW | PASS | None |
| MEDIUM | SCREEN | If `intent` is VERIFY_IDENTITY → HUMAN_HANDOFF |
| HIGH | HUMAN_HANDOFF | If `fraud_score` > 0.75 → BLOCK |
| CRITICAL | BLOCK | None |

**FR-31** The system SHALL execute the selected action within **500ms** of Decision Agent completing.

**FR-32** Action execution:
- **PASS**: Connect call to recipient via telephony adapter
- **SCREEN**: Present live transcript + options (Answer/Block/Continue) to recipient dashboard; hold call
- **BLOCK**: Terminate call from caller side; play optional "goodbye" message
- **HUMAN_HANDOFF**: Alert recipient via dashboard + push notification; ring recipient's phone

**FR-33** Action and timestamp SHALL be stored in the `Call` database record.

---

### 3.9 Real-Time Dashboard Notifications (maps to CR-12)

**FR-34** The system SHALL push WebSocket events to all connected dashboard clients within **500ms** of any call state change.

**FR-35** The following WebSocket events SHALL be implemented:

| Event | Trigger | Payload |
|-------|---------|---------|
| `call.started` | Call intercepted | call_id, from_number, timestamp |
| `call.transcript` | New turn completed | call_id, turn_number, text, speaker |
| `call.classified` | All agents complete | call_id, intent, caller_type, risk_score, risk_level |
| `call.action` | Action decided | call_id, action, reason |
| `call.ended` | Call terminated | call_id, duration, final_status |
| `system.health` | Health state change | component, status |

**FR-36** If the WebSocket connection is lost, the client SHALL be able to reconnect and receive the current state of active calls via a REST endpoint.

---

### 3.10 Call History and Audit (maps to CR-13)

**FR-37** The system SHALL store complete call records including: caller number, timestamp, duration, all transcript turns, all classification results, risk score, and final action.

**FR-38** The dashboard SHALL display a paginated call history list filterable by: date range, action, risk level, caller type, intent.

**FR-39** Each call record SHALL be immutable after the call ends (no modification, only soft delete).

**FR-40** The system SHALL retain call records for a configurable period (default: 90 days). See privacy.md.

---

### 3.11 Manual Override (maps to CR-14)

**FR-41** During SCREEN state, the recipient SHALL be able to manually select: ANSWER, BLOCK, or CONTINUE_SCREENING.

**FR-42** Manual override SHALL be executed within **3 seconds** of recipient selection.

**FR-43** If the recipient does not respond to a SCREEN state within **30 seconds**, the system SHALL default to BLOCK.

**FR-44** Manual override events SHALL be logged with user ID, timestamp, and original system recommendation.

---

### 3.12 Mock Mode (maps to CR-15, CR-16)

**FR-45** When `TELEPHONY_PROVIDER=mock`, the system SHALL accept mock inbound call requests via `POST /api/v1/telephony/mock/inbound`.

**FR-46** The mock system SHALL include 9 pre-built scenarios with scripted transcripts covering all risk levels and action types.

**FR-47** Mock scenarios SHALL execute the full pipeline (intent classification → risk score → action) using real ML models.

**FR-48** Each mock scenario SHALL be completable in under 60 seconds.

---

### 3.13 Authentication and Authorization (maps to CR-18)

**FR-49** All dashboard API endpoints SHALL require a valid JWT bearer token.

**FR-50** Tokens SHALL be signed with HS256 using the `SECRET_KEY` environment variable.

**FR-51** Token expiry SHALL be configurable via `ACCESS_TOKEN_EXPIRE_MINUTES` (default: 60).

**FR-52** Refresh tokens SHALL be supported to avoid forcing users to re-login.

---

### 3.14 Health Check (maps to CR-17)

**FR-53** `GET /health` SHALL return HTTP 200 with a JSON body containing the status of all components.

**FR-54** Health check SHALL verify: database connectivity, ML models loaded, telephony adapter ready.

**FR-55** If any critical component (database, telephony) is unhealthy, the endpoint SHALL return HTTP 503.

---

## 4. Non-Functional Requirements

### 4.1 Performance

| Requirement | Target | Measurement |
|-------------|--------|-------------|
| NFR-P01: Call answer latency | ≤ 2 seconds | Time from call received to first audio played to caller |
| NFR-P02: STT processing time | ≤ 1 second per turn | For real providers; mock is instant |
| NFR-P03: ML pipeline latency | ≤ 500ms | Time from transcript ready to risk score computed |
| NFR-P04: TTS synthesis time | ≤ 500ms | For real providers; mock is instant |
| NFR-P05: WebSocket push latency | ≤ 500ms | From event to client receipt |
| NFR-P06: API response time | ≤ 200ms (p95) | For REST endpoints excluding call operations |
| NFR-P07: Total pipeline latency | ≤ 2 seconds | End-to-end: transcript ready → action taken |

### 4.2 Security

| Requirement | Specification |
|-------------|--------------|
| NFR-S01: Transport encryption | All API and WebSocket traffic via HTTPS/WSS in production |
| NFR-S02: Secret management | No secrets in source code; all via environment variables |
| NFR-S03: Password hashing | bcrypt with cost factor ≥ 12 |
| NFR-S04: JWT security | HS256 minimum; RS256 preferred in production |
| NFR-S05: Input validation | All API inputs validated via Pydantic models |
| NFR-S06: SQL injection prevention | All DB queries via SQLAlchemy ORM only |
| NFR-S07: CORS | Restricted to configured origins via `CORS_ORIGINS` |
| NFR-S08: Rate limiting | Max 100 requests/minute per IP on auth endpoints |
| NFR-S09: PII in logs | PROHIBITED — no transcripts, phone numbers, or names in logs |
| NFR-S10: Dependency scanning | All Python deps must be pinned; no wildcard versions |

### 4.3 Reliability

| Requirement | Target |
|-------------|--------|
| NFR-R01: Availability | 99.5% uptime (excluding planned maintenance) |
| NFR-R02: Fail-safe defaults | System defaults to SCREEN on any component failure |
| NFR-R03: Database persistence | All call records persisted before action is executed |
| NFR-R04: Graceful shutdown | In-flight calls completed before process shutdown |
| NFR-R05: Error recovery | Retry logic for transient external API failures (max 2 retries, exponential backoff) |

### 4.4 Scalability

| Requirement | Target |
|-------------|--------|
| NFR-SC01: Concurrent calls | Support ≥ 50 simultaneous calls in v1 |
| NFR-SC02: Horizontal scaling | Backend stateless (session in JWT, no sticky sessions needed) |
| NFR-SC03: Database | Connection pooling via asyncpg (pool size configurable) |
| NFR-SC04: Call history | Efficient pagination; no full table scans |

### 4.5 Maintainability

| Requirement | Specification |
|-------------|--------------|
| NFR-M01: Code quality | Black + isort formatting enforced; mypy type checking |
| NFR-M02: Test coverage | ≥ 80% line coverage for backend code |
| NFR-M03: Documentation | All public functions/classes have docstrings |
| NFR-M04: Logging | Structured JSON logs via structlog |
| NFR-M05: DB migrations | All schema changes via Alembic migrations (never manual) |
| NFR-M06: API versioning | All API routes under `/api/v1/` prefix |
| NFR-M07: Adapter pattern | All external services behind interface; provider switchable via config |

---

## 5. Interface Requirements

### 5.1 REST API

Base URL: `http://localhost:8000/api/v1/` (development)

**Authentication:**
- `POST /auth/login` — Username/password → JWT tokens
- `POST /auth/refresh` — Refresh token → new access token
- `POST /auth/logout` — Invalidate refresh token

**Calls:**
- `GET /calls` — List call history (paginated, filterable)
- `GET /calls/{call_id}` — Get single call details + transcript
- `POST /calls/{call_id}/action` — Manual override action

**Telephony:**
- `POST /telephony/inbound` — Webhook from Exotel
- `POST /telephony/mock/inbound` — Mock call trigger

**Health:**
- `GET /health` — System health status

Full API reference: [docs/api.md](api.md)

### 5.2 WebSocket Interface

Endpoint: `ws://localhost:8000/ws`

Authentication: `?token=<JWT>` query parameter

Events: See FR-35 for full event catalog.

### 5.3 Telephony Interface

Exotel webhook format:
- `From` — Caller number
- `To` — Called number
- `CallSid` — Unique call identifier
- `Direction` — "inbound"
- `Status` — Call status

System responds with ExoML (XML) to control call flow.

### 5.4 Database Interface

All database access through SQLAlchemy 2.0 async ORM.

**Core tables:**
- `users` — Dashboard user accounts
- `calls` — Call records (one per call)
- `call_transcripts` — Turn-by-turn transcripts
- `call_classifications` — Agent outputs per call
- `recruitment_info` — Extracted recruitment data
- `audit_log` — System actions and overrides

---

## 6. Constraints

| Constraint | Description |
|------------|-------------|
| C-01 | Python 3.11 minimum (async, type hint support) |
| C-02 | PostgreSQL 16 minimum (JSONB, UUID support) |
| C-03 | Exotel as telephony provider (India-specific for production) |
| C-04 | All ML models must run inference on CPU (GPU optional) |
| C-05 | No paid API keys required for development mode |
| C-06 | English language only in v1 |
| C-07 | Docker Compose required for reproducible deployment |
| C-08 | MIT License — no GPL dependencies in production code |

---

## 7. Assumptions

| ID | Assumption |
|----|------------|
| A-01 | The telephony provider (Exotel) supports webhook-based call control |
| A-02 | The recipient has a modern browser (Chrome/Firefox/Edge 2023+) for dashboard |
| A-03 | Call audio quality is sufficient for STT accuracy (>8kHz sampling rate) |
| A-04 | The caller speaks in English (or primary language is English-dominant) |
| A-05 | The recipient has internet connectivity to receive dashboard notifications |
| A-06 | STT provider latency is ≤ 800ms per audio segment for real providers |
| A-07 | PostgreSQL is the only supported database in v1 |
| A-08 | Training datasets (CLINC150, BANKING77, FTC) are available and licensed appropriately |
| A-09 | The system operator has read and complied with applicable telecom regulations |
| A-10 | A single-tenant deployment model (one organization per installation) |
