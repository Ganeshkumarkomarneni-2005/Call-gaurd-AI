# CallGuard AI — Final Project Report

**Version:** Draft 1.0  
**Status:** IN_PROGRESS — to be completed after ML training and final evaluation  
**Last Updated:** 2026-09-21

---

> [!IMPORTANT]
> This document is a template. Sections marked `[TO BE FILLED]` must be completed after:
> - Colab notebook execution
> - Backend integration testing
> - Frontend completion
> - Final evaluation

---

## 1. Executive Summary

CallGuard AI is a production-oriented prototype for intelligent incoming call screening. Unlike simplistic call blockers, CallGuard AI applies multi-dimensional reasoning:

**Core Principle: CALLER TYPE ≠ INTENT ≠ RISK ≠ ACTION**

The system independently assesses:
- **Who is calling** (Human / AI / Robocall / Unknown)
- **Why they are calling** (Recruitment / Fraud / Promotional / etc.)
- **How risky the call is** (Low / Medium / High / Critical)
- **What to do about it** (Handle / Notify / Transfer / End / Flag)

This prevents both false positives (blocking legitimate AI recruitment assistants) and false negatives (missing human scammers).

---

## 2. Problem Statement

### 2.1 The Inadequacy of Existing Solutions

Current call screening approaches suffer from a fundamental flaw: they classify calls into binary categories (spam/not-spam) based on number reputation databases or simple keyword matching.

This fails because:

1. **AI recruitment assistants are increasingly common** — A call from an AI is not inherently dangerous. Companies legitimately use automated systems for scheduling interviews.

2. **Human scammers bypass AI detection** — A sophisticated human caller making a recruitment fraud call will pass "AI caller = block" filters.

3. **Intent and risk are independent dimensions** — A PROMOTIONAL call can be LOW risk. A RECRUITMENT call can be HIGH risk. Simple category-based blocking is wrong.

### 2.2 The Specific Problem CallGuard AI Solves

- Intelligent screening that understands *why* someone is calling
- Extraction of actionable information from legitimate recruitment calls
- Detection of fraud indicators regardless of caller type (human or AI)
- Explainable decisions — the system can justify every action
- Human fallback — uncertain or important calls are routed to the user

---

## 3. System Architecture

### 3.1 High-Level Architecture

```
Incoming Call
     ↓
Virtual Number (Exotel / Mock)
     ↓
Voice AI Gateway (WebSocket / Audio)
     ↓
Speech-to-Text (Google / Deepgram / Mock)
     ↓
Conversation Manager
     ↓
┌────────────────────────────────────┐
│       CallAnalysisPipeline         │
│                                    │
│  CallerClassificationAgent         │
│  IntentDetectionAgent              │
│  RecruitmentAgent                  │
│  FraudDetectionAgent               │
│  RiskAssessmentAgent               │
│  DecisionAgent                     │
│  CallSummaryAgent                  │
│  NotificationAgent                 │
│  HumanHandoffAgent                 │
└────────────┬───────────────────────┘
             ↓
     Decision Output
     ↓
AI_HANDLE / NOTIFY / TRANSFER / END / FLAG_FOR_REVIEW
     ↓
PostgreSQL Database
     ↓
WebSocket Events → React Dashboard
```

### 3.2 Technology Stack

| Layer | Technology | Status |
|-------|-----------|--------|
| Backend | FastAPI + Python 3.11 | IMPLEMENTED |
| Database | PostgreSQL (SQLAlchemy 2.0) | IMPLEMENTED |
| Real-time | WebSocket (FastAPI) | IMPLEMENTED |
| Auth | JWT (python-jose) | IMPLEMENTED |
| Telephony | Exotel (stub) + Mock (full) | IMPLEMENTED |
| STT | Google/Deepgram (stub) + Mock | IMPLEMENTED |
| TTS | Google/ElevenLabs (stub) + Mock | IMPLEMENTED |
| LLM | OpenAI/Gemini (stub) + Mock | IMPLEMENTED |
| ML | scikit-learn, PyTorch | NOTEBOOKS_READY |
| Frontend | Next.js + React + TypeScript | NOT_STARTED |
| Deployment | Docker + docker-compose | IMPLEMENTED |

---

## 4. Implementation Details

### 4.1 Database Layer

**11 ORM models** implemented in SQLAlchemy 2.0 (async):

- `users` — user accounts
- `calls` — call records
- `call_participants` — participant tracking
- `transcripts` — full call transcripts
- `transcript_segments` — per-turn transcript with timestamps
- `call_analysis` — classification results per call
- `recruitment_details` — extracted recruitment information
- `risk_events` — individual risk indicator events
- `decisions` — decision audit trail
- `notifications` — user notifications
- `call_actions` — actions taken per call

### 4.2 Agent Architecture

| Agent | Method | Status |
|-------|--------|--------|
| CallerClassificationAgent | Rule-based keyword + pattern scoring | IMPLEMENTED |
| IntentDetectionAgent | Keyword set scoring, multi-intent capable | IMPLEMENTED |
| RecruitmentAgent | Regex extraction + legitimacy assessment | IMPLEMENTED |
| FraudDetectionAgent | 9 fraud indicator types, context-aware | IMPLEMENTED |
| RiskAssessmentAgent | Multi-signal aggregation, explainable | IMPLEMENTED |
| DecisionAgent | Configurable policy rules, 5 actions | IMPLEMENTED |
| CallSummaryAgent | Template-based summary generation | IMPLEMENTED |
| NotificationAgent | Event-driven, filters low-priority events | IMPLEMENTED |
| HumanHandoffAgent | Context-preserving handoff summary | IMPLEMENTED |

### 4.3 ML Pipeline

| Notebook | Purpose | Status |
|----------|---------|--------|
| 01_data_understanding.ipynb | Dataset exploration | READY_FOR_COLAB |
| 02_data_cleaning.ipynb | Text cleaning, splitting | READY_FOR_COLAB |
| 03_intent_classification.ipynb | TF-IDF + LR/SVM/DistilBERT | READY_FOR_COLAB |
| 04_recruitment_detection.ipynb | 2-stage recruitment classifier | READY_FOR_COLAB |
| 05_fraud_risk_model.ipynb | Fraud detection, risk scoring | READY_FOR_COLAB |
| 06_caller_type_experiment.ipynb | AI/Human/Robocall detection | READY_FOR_COLAB |
| 07_model_comparison.ipynb | Model comparison and selection | READY_FOR_COLAB |
| 08_error_analysis.ipynb | Error analysis, failure patterns | READY_FOR_COLAB |
| 09_final_evaluation.ipynb | Held-out test evaluation | READY_FOR_COLAB |
| 10_model_export.ipynb | Model export for backend integration | READY_FOR_COLAB |

---

## 5. ML Results

> [!IMPORTANT]
> **NOT_YET_EVALUATED** — all ML models pending Colab execution.
> This section will be completed with actual results after training.

### 5.1 Intent Classification

| Model | Accuracy | Macro F1 |
|-------|----------|----------|
| TF-IDF + LR | [TO BE FILLED] | [TO BE FILLED] |
| TF-IDF + SVM | [TO BE FILLED] | [TO BE FILLED] |
| DistilBERT | [TO BE FILLED] | [TO BE FILLED] |

### 5.2 Fraud Detection

| Metric | Value |
|--------|-------|
| Fraud Recall | [TO BE FILLED] |
| False Positive Rate | [TO BE FILLED] |
| AUC-ROC | [TO BE FILLED] |

### 5.3 Caller Type Detection

| Class | Precision | Recall | F1 |
|-------|-----------|--------|-----|
| HUMAN | [TO BE FILLED] | [TO BE FILLED] | [TO BE FILLED] |
| AI | [TO BE FILLED] | [TO BE FILLED] | [TO BE FILLED] |
| ROBOCALL | [TO BE FILLED] | [TO BE FILLED] | [TO BE FILLED] |
| UNKNOWN | [TO BE FILLED] | [TO BE FILLED] | [TO BE FILLED] |

---

## 6. API Surface

Total endpoints implemented: **20+**

| Category | Count |
|----------|-------|
| Auth endpoints | 3 |
| Call management | 9 |
| Dashboard | 3 |
| Notifications | 3 |
| Health | 1 |
| WebSocket | 2 |

See `docs/api.md` for full reference.

---

## 7. Testing Status

| Test Category | Tests Written | Tests Passing |
|--------------|--------------|---------------|
| API health | 1 | [TO BE RUN] |
| Authentication | 5 | [TO BE RUN] |
| Call management | 5 | [TO BE RUN] |
| Dashboard | 2 | [TO BE RUN] |
| Agent unit tests | 11 | [TO BE WRITTEN] |
| E2E call simulation | 9 | [TO BE WRITTEN] |
| Security tests | 8 | [TO BE WRITTEN] |
| Performance tests | 8 | [TO BE MEASURED] |

---

## 8. Demo Scenarios

9 demo scenarios prepared (see `docs/demo-script.md`):

1. Human recruiter (legitimate) — NOTIFY
2. AI recruiter (legitimate) — NOTIFY
3. AI interview scheduler — NOTIFY
4. AI promotional caller — AI_HANDLE/END
5. Human scammer — END/FLAG
6. AI scammer — END/FLAG
7. Fake recruiter requesting payment — END/FLAG
8. OTP fraud — END
9. Unknown caller — FLAG_FOR_REVIEW

---

## 9. Limitations and Honest Disclaimers

### 9.1 AI vs Human Detection Limitations
- Detection is probabilistic and based on linguistic patterns
- Sophisticated actors can defeat text-based detection
- Audio features (prosody, timing) would significantly improve accuracy
- New TTS/voice cloning systems may appear human
- **Never treat AI caller type alone as a safety signal**

### 9.2 Fraud Detection Limitations
- Trained on synthetic data — may not generalize to real calls
- Context understanding is limited in rule-based mode
- LLM-based agents would improve contextual understanding
- Adversarial callers may rephrase to avoid keyword detection

### 9.3 Dataset Limitations
- 1,100 synthetic examples — small for production
- English only
- No real call recordings used
- Distribution may not match real-world call mix

### 9.4 Deployment Limitations
- Exotel integration is a stub — requires live credentials and testing
- STT/TTS providers not tested with real audio
- Frontend not yet built
- No load testing performed

---

## 10. Future Improvements

1. **Audio feature extraction** — prosody, speech timing, spectral features for caller type detection
2. **Multilingual support** — Hindi, regional Indian languages
3. **Real training data** — collect and label real call transcripts (with consent)
4. **LLM integration** — replace rule-based agents with GPT/Gemini reasoning
5. **Continuous learning** — retrain models on flagged/reviewed calls
6. **Adversarial robustness testing** — test against deliberately crafted evasion attempts
7. **Mobile app** — receive real-time notifications on phone
8. **Multiple user accounts** — shared number with multiple users
9. **Call recording** — store and replay calls (with consent)
10. **Analytics dashboard** — trends, patterns, threat intelligence

---

## 11. Compliance and Privacy Notes

> [!CAUTION]
> This prototype has not been reviewed for legal compliance.
> Before production deployment in India, verify:
> - TRAI regulations on call recording and AI-answered calls
> - IT Act 2000 / DPDP Act 2023 requirements
> - Consent requirements for recording/transcription
> - Data localization requirements
>
> This system should NOT be used in production without legal review.

---

## 12. Project Timeline

| Milestone | Date | Status |
|-----------|------|--------|
| Architecture design | 2026-09-17 | COMPLETED |
| Backend foundation | 2026-09-17 | COMPLETED |
| Agent implementation | 2026-09-17 | COMPLETED |
| ML notebooks | 2026-09-17 | COMPLETED |
| Documentation | 2026-09-21 | IN_PROGRESS |
| Frontend dashboard | TBD | NOT_STARTED |
| ML model training (Colab) | TBD | NOT_STARTED |
| Integration testing | TBD | NOT_STARTED |
| Final evaluation | TBD | NOT_STARTED |
| Production deployment | TBD | NOT_STARTED |
