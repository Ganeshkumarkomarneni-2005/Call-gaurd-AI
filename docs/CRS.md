# CallGuard AI — Concept Requirements Specification (CRS)

**Document ID:** CRS-001  
**Version:** 1.0  
**Date:** 2026-09-17  
**Status:** Draft  
**Author:** CallGuard AI Team  

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Statement](#2-problem-statement)
3. [System Vision](#3-system-vision)
4. [Core Intelligence Principle](#4-core-intelligence-principle)
5. [User Personas](#5-user-personas)
6. [Use Cases](#6-use-cases)
7. [System Boundary](#7-system-boundary)
8. [Key Design Decisions](#8-key-design-decisions)
9. [Concept Requirements](#9-concept-requirements)
10. [Out of Scope](#10-out-of-scope)

---

## 1. Executive Summary

CallGuard AI is a real-time AI-powered call screening system designed to protect individuals from phone-based fraud, scams, and unwanted calls. Unlike traditional spam call detection based on number blacklists, CallGuard AI intercepts incoming calls, conducts an automated conversation with the caller, and uses multi-model machine learning to classify caller intent, detect fraud patterns, and compute a risk score — all before the call recipient decides whether to answer.

The system is designed for the Indian telephony context (Exotel integration) but is architected to support multiple telephony providers through an adapter pattern.

---

## 2. Problem Statement

### 2.1 Scale of the Problem

- India receives an estimated 1.5+ billion spam/scam calls per month (TRAI data, 2024)
- Phone-based financial fraud losses exceed ₹10,000 crore annually (Ministry of Home Affairs)
- Robocall/IVR fraud continues to grow 25% year-over-year
- 78% of reported job scams in India originate via phone calls (Consumer complaint data)

### 2.2 Current Failures

**Blacklist-based solutions (Truecaller, DND registry):**
- Numbers rotate faster than blacklists can update (spammers buy new SIMs daily)
- False positives cause legitimate callers to be blocked
- Cannot detect intent — only identity

**Carrier-level filtering:**
- Pattern-based (call frequency, duration) — misses scripted social engineering
- Cannot analyze call content
- High latency (takes days/weeks to flag a number)

**Passive voicemail screening:**
- Recipient must still listen to voicemail
- No real-time action possible
- Cannot block ongoing scam call

### 2.3 Core Gap

**No existing solution understands what a caller is saying or what they intend to do.**

A phone number on the Truecaller whitelist can still be used to conduct fraud. A registered telemarketer can pivot to requesting OTPs. A spoofed bank number can claim anything. The only way to accurately assess risk is to engage with the caller's actual words and stated purpose.

---

## 3. System Vision

CallGuard AI's vision: **Every person should have an AI guardian that screens their calls, understands the caller's intent, and takes protective action — automatically and in real-time.**

### 3.1 The Ideal Experience

**Scenario A — Scam blocked:**
> Priya's phone rings. A caller claims to be from SBI and says her account will be suspended unless she provides her OTP. Before Priya's phone even rings in her ear, CallGuard AI has intercepted the call, asked the caller their purpose, detected the OTP extraction pattern, assigned risk score 0.98, and blocked the call. Priya gets a push notification: "Blocked call: OTP fraud attempt from +91-XXXXXXXXXX."

**Scenario B — Legitimate call passed:**
> Rahul is waiting for a callback from an interview. An unknown number calls. CallGuard intercepts, asks the caller's purpose, detects "job interview follow-up" intent, assigns risk score 0.08, and connects Rahul immediately. Rahul's phone rings with a "Verified: Recruiter call" banner.

**Scenario C — Uncertain call screened:**
> An unknown caller says they are from a medical supplier. CallGuard cannot confidently classify (risk 0.45). It presents Rahul with a real-time transcription and "Answer / Block / Let AI continue screening" choice on his dashboard.

---

## 4. Core Intelligence Principle

> **CALLER TYPE ≠ INTENT ≠ RISK ≠ ACTION**

This principle mandates that each of the four dimensions be assessed independently:

| Dimension | Question | Example Values |
|-----------|---------|----------------|
| **Caller Type** | WHO is calling? | RECRUITER, BANK, TELEMARKETER, HEALTHCARE, UNKNOWN |
| **Intent** | WHAT do they want? | VERIFY_IDENTITY, OFFER_JOB, COLLECT_PAYMENT, REQUEST_OTP, SELL_PRODUCT |
| **Risk Level** | HOW dangerous? | LOW (0.0–0.25), MEDIUM (0.25–0.5), HIGH (0.5–0.75), CRITICAL (0.75–1.0) |
| **Action** | WHAT should happen? | PASS, SCREEN, BLOCK, HUMAN_HANDOFF |

**Critical implication:** A BANK caller type does not mean low risk. A RECRUITER intent does not mean the call is safe. Risk must be derived from the combination of all signals.

---

## 5. User Personas

### 5.1 Persona A — Priya (Primary User: Call Recipient)

- **Age:** 32, software engineer in Bangalore
- **Phone usage:** High — receives 10–20 unknown calls per week
- **Pain points:** 
  - Cannot distinguish legitimate bank calls from fraud
  - Job hunting — misses real recruiter calls while blocking spam
  - Time-poor — cannot manually screen every call
- **Goals:**
  - Never miss a legitimate important call
  - Never be defrauded by a phone call
  - Minimal cognitive overhead

### 5.2 Persona B — Arjun (Secondary User: Dashboard Admin)

- **Age:** 45, small business owner / family admin
- **Phone usage:** Moderate — manages calls for himself and family members
- **Pain points:**
  - Family members (elderly parents) vulnerable to scam calls
  - Needs visibility into call history and blocked calls
  - Wants to configure custom rules
- **Goals:**
  - Protect family members who are less tech-savvy
  - Audit blocked calls to ensure nothing legitimate was missed
  - Understand why calls were blocked

### 5.3 Persona C — Dev (System Administrator)

- **Role:** Technical operator deploying CallGuard AI
- **Goals:**
  - Monitor system health
  - Configure telephony integration
  - Review ML model performance
  - Manage user accounts

---

## 6. Use Cases

### UC-01: Inbound Call Interception
**Actor:** Caller, System  
**Trigger:** Incoming call to a CallGuard-protected number  
**Flow:**
1. Telephony provider (Exotel/Mock) receives inbound call
2. System intercepts call before it reaches recipient
3. System answers call with greeting
4. System begins conversation with caller

**Success:** Call is intercepted and conversation begins within 2 seconds  
**Failure:** System unavailable — fallback to direct ring-through

---

### UC-02: Automated Conversation with Caller
**Actor:** Caller, Conversation Agent  
**Trigger:** UC-01 success  
**Flow:**
1. System greets caller
2. Caller states their purpose
3. System asks follow-up questions based on stated purpose
4. System collects sufficient information to classify intent (max 3 turns)

**Success:** Intent information collected within 30 seconds  
**Failure:** Caller hangs up or refuses to state purpose

---

### UC-03: Intent Classification
**Actor:** Intent Agent  
**Trigger:** Transcript available from UC-02  
**Flow:**
1. Transcript is passed to Intent Classifier
2. Classifier returns top-3 intent classes with confidence scores
3. Result stored in call record

**Success:** Intent classified with confidence > 0.6  
**Failure:** Low confidence — escalate to SCREEN action

---

### UC-04: Caller Type Detection
**Actor:** Caller Type Agent  
**Trigger:** Transcript available from UC-02  
**Flow:**
1. Transcript and metadata (number, time) passed to Caller Type Detector
2. Returns caller type with confidence
3. Result stored in call record

**Success:** Caller type identified  
**Failure:** UNKNOWN — included in risk calculation

---

### UC-05: Fraud Detection
**Actor:** Fraud Detection Agent  
**Trigger:** Transcript available from UC-02  
**Flow:**
1. Transcript scanned for fraud signal patterns
2. ML model returns fraud probability score
3. High fraud probability triggers CRITICAL risk classification

**Success:** Fraud signals identified or absence confirmed  
**Failure:** Model error — default to conservative HIGH risk

---

### UC-06: Recruitment Scam Detection
**Actor:** Recruitment Detection Agent  
**Trigger:** Intent ≈ OFFER_JOB or caller type ≈ RECRUITER  
**Flow:**
1. Transcript analyzed for recruitment scam patterns (advance fee, urgency, vagueness)
2. If legitimate recruiter: extract company, role, salary, location
3. Recruitment scam score returned

**Success:** Clear classification (legitimate or scam)  
**Failure:** Ambiguous — elevate to SCREEN

---

### UC-07: Risk Score Computation
**Actor:** Risk Engine  
**Trigger:** All agent outputs available  
**Flow:**
1. Collect: intent score, fraud score, recruitment score, caller type
2. Apply weighted fusion formula
3. Apply hard rules (OTP request → CRITICAL override)
4. Return final risk score [0.0–1.0] and risk level

**Success:** Risk score computed  
**Failure:** N/A — risk engine always returns a result

---

### UC-08: Decision and Action
**Actor:** Decision Agent  
**Trigger:** Risk score from UC-07  
**Flow:**
1. Apply decision matrix (risk level × intent → action)
2. Select action: PASS, SCREEN, BLOCK, HUMAN_HANDOFF
3. Execute action via telephony adapter

**Actions:**
- PASS: Connect call to recipient
- SCREEN: Present real-time transcript + choice to recipient
- BLOCK: Terminate call, notify recipient
- HUMAN_HANDOFF: Alert recipient, allow them to decide

---

### UC-09: Real-time Dashboard Notification
**Actor:** Notification Agent, Recipient  
**Trigger:** Any action taken  
**Flow:**
1. WebSocket event pushed to all connected dashboard clients
2. Dashboard displays call status, caller info, risk score, transcript
3. Recipient can take manual action (override block/pass)

**Success:** Dashboard updated within 500ms of action  
**Failure:** WebSocket disconnected — fall back to HTTP polling

---

### UC-10: Call History and Audit Log
**Actor:** Recipient / Admin  
**Trigger:** User opens call history page  
**Flow:**
1. System retrieves call records from database
2. Each record includes: caller, time, duration, intent, risk, action, transcript
3. User can filter, search, export

**Success:** Complete call history displayed  
**Failure:** N/A

---

### UC-11: Manual Override
**Actor:** Recipient  
**Trigger:** User receives SCREEN notification  
**Flow:**
1. Dashboard shows live transcript and risk information
2. Recipient selects: "Answer", "Block", or "Continue screening"
3. System executes selected action via telephony adapter

**Success:** Action executed within 3 seconds of user selection  
**Failure:** Timeout — apply default action (SCREEN → BLOCK after 30s)

---

### UC-12: Mock Call Simulation
**Actor:** Developer / Tester  
**Trigger:** POST request to `/api/v1/telephony/mock/inbound`  
**Flow:**
1. Developer selects a pre-built scenario (e.g., "recruitment_scam")
2. System simulates call using scripted transcript
3. Full pipeline executes
4. Result visible on dashboard

**Success:** Full pipeline executed without real telephony  
**Failure:** N/A

---

### UC-13: System Health Check
**Actor:** Admin / Monitoring System  
**Trigger:** GET /health  
**Flow:**
1. Health endpoint checks: database connectivity, ML models loaded, telephony adapter
2. Returns status for each component

**Success:** HTTP 200 with component status  
**Failure:** HTTP 503 if any critical component is down

---

### UC-14: User Authentication
**Actor:** Dashboard User  
**Trigger:** User navigates to dashboard  
**Flow:**
1. User provides credentials (email + password)
2. System verifies, issues JWT access token
3. Token used for all subsequent API calls

**Success:** Dashboard accessible  
**Failure:** 401 Unauthorized

---

### UC-15: Configuration Management
**Actor:** Admin  
**Trigger:** Admin accesses settings page  
**Flow:**
1. Admin can configure: risk thresholds, custom block rules, notification preferences
2. Changes applied without system restart
3. Changes logged in audit trail

**Success:** Configuration saved and active  
**Failure:** Validation error — reject invalid values

---

## 7. System Boundary

### Inside the System
- Inbound call interception (via telephony adapter)
- AI conversation with caller
- Intent, caller type, fraud classification
- Risk scoring
- Decision and action execution
- Dashboard and notifications
- Call history and audit log

### At the Boundary (Integrations)
- Telephony provider (Exotel API / Mock)
- STT provider (Google Speech / Deepgram / Mock)
- TTS provider (Google TTS / ElevenLabs / Mock)
- LLM provider (OpenAI / Gemini / Mock)
- PostgreSQL database
- Browser push notification service

### Outside the System
- The caller's phone or network
- Recipient's actual phone (device)
- Third-party fraud databases (not integrated, planned)
- Legal / law enforcement systems

---

## 8. Key Design Decisions

### KD-01: Mock-First Development
All external integrations (telephony, STT, TTS, LLM) have mock implementations that fully simulate the integration without requiring credentials. This enables full development and testing without paid services.

### KD-02: Adapter Pattern for All External Services
Each external service is accessed through an interface/adapter. Switching providers (e.g., from Google Speech to Deepgram) requires only changing the adapter, not the core business logic.

### KD-03: Independent ML Models, Not One Giant Model
Each classification task (intent, fraud, caller type, recruitment) has a dedicated model. This enables independent training, evaluation, and updating of each model without affecting others.

### KD-04: Non-Blocking Pipeline
The caller conversation and ML classification pipeline must not block the recipient's user experience. All heavy processing runs asynchronously; the dashboard receives WebSocket updates.

### KD-05: Fail-Safe Defaults
If any component fails (model error, API timeout, database error), the system defaults to a conservative action (SCREEN or HUMAN_HANDOFF), never blindly PASS. Safety is prioritized over convenience.

### KD-06: No PII in Logs
Call transcripts and personally identifiable information are never written to application logs. Only metadata (call ID, risk score, action) appears in logs. Full transcripts are in the encrypted database only.

---

## 9. Concept Requirements

| ID | Requirement | Priority | Source |
|----|-------------|----------|--------|
| CR-01 | System shall intercept inbound calls within 2 seconds | MUST | UC-01 |
| CR-02 | System shall conduct automated conversation with caller | MUST | UC-02 |
| CR-03 | Conversation shall not exceed 3 exchange turns | MUST | UC-02 |
| CR-04 | System shall classify caller intent into 15+ classes | MUST | UC-03 |
| CR-05 | System shall detect caller type (5 categories) | MUST | UC-04 |
| CR-06 | System shall detect fraud call patterns | MUST | UC-05 |
| CR-07 | System shall detect recruitment scam patterns | MUST | UC-06 |
| CR-08 | System shall extract structured info from recruitment calls | SHOULD | UC-06 |
| CR-09 | System shall compute a composite risk score [0.0–1.0] | MUST | UC-07 |
| CR-10 | System shall select from 4 action tiers | MUST | UC-08 |
| CR-11 | System shall block calls identified as CRITICAL risk | MUST | UC-08 |
| CR-12 | System shall notify recipient within 500ms via WebSocket | MUST | UC-09 |
| CR-13 | System shall maintain complete call history | MUST | UC-10 |
| CR-14 | System shall support manual override by recipient | MUST | UC-11 |
| CR-15 | System shall include a full mock mode | MUST | KD-01 |
| CR-16 | System shall provide 9 demo scenarios | SHOULD | UC-12 |
| CR-17 | System shall expose a health check endpoint | MUST | UC-13 |
| CR-18 | System shall implement JWT authentication | MUST | UC-14 |
| CR-19 | System shall never log PII or transcripts | MUST | KD-06 |
| CR-20 | System shall default to SCREEN on model failure | MUST | KD-05 |
| CR-21 | STT processing shall complete within 1 second | SHOULD | Performance |
| CR-22 | End-to-end pipeline latency shall be <2 seconds | SHOULD | Performance |
| CR-23 | System shall support at least 50 concurrent calls | SHOULD | Scalability |

---

## 10. Out of Scope

The following items are explicitly **out of scope** for version 1.0:

1. **Outbound call management** — System only handles inbound calls
2. **SMS / WhatsApp screening** — Only voice calls
3. **Voiceprint verification** — No biometric caller verification
4. **Real-time transcription of recipient** — Only the caller is transcribed
5. **Legal/compliance enforcement** — System recommends actions; does not enforce legal obligations
6. **Multi-tenant SaaS** — Single-tenant deployment only
7. **Mobile app** — Web dashboard only (browser push notifications)
8. **TRAI DLT integration** — Planned, not implemented in v1
9. **Non-Indian telephony** — No Twilio, Vonage, or AWS Connect adapters in v1
10. **Multilingual support** — English only in v1 (Hindi/Hinglish planned)
