# CallGuard AI — Test Plan

**Version:** 1.0  
**Status:** IN_PROGRESS  
**Last Updated:** 2026-09-21

---

## 1. Overview

This test plan covers all testing requirements for CallGuard AI across:
- Unit tests
- Integration tests
- API tests
- Agent/ML tests
- Performance tests
- Security tests
- Frontend tests
- End-to-end call simulation tests

---

## 2. Test Environment

### Local (Development)
- Python 3.11+
- PostgreSQL via Docker (or SQLite for unit tests)
- Mock telephony provider
- Mock STT/TTS/LLM providers

### CI/CD
- GitHub Actions
- In-memory SQLite database
- All external services mocked

---

## 3. Functional Test Cases

### 3.1 Call Simulation Tests (TC001–TC025)

| ID | Name | Type | Priority | Status |
|----|------|------|----------|--------|
| TC001 | Human recruiter call | E2E | HIGH | NOT_RUN |
| TC002 | AI recruiter call | E2E | HIGH | NOT_RUN |
| TC003 | AI interview scheduler call | E2E | HIGH | NOT_RUN |
| TC004 | AI promotional caller | E2E | MEDIUM | NOT_RUN |
| TC005 | Human promotional caller | E2E | MEDIUM | NOT_RUN |
| TC006 | Human fraud caller | E2E | CRITICAL | NOT_RUN |
| TC007 | AI fraud caller | E2E | CRITICAL | NOT_RUN |
| TC008 | Fake recruiter requesting payment | E2E | CRITICAL | NOT_RUN |
| TC009 | OTP fraud call | E2E | CRITICAL | NOT_RUN |
| TC010 | Unknown caller | E2E | HIGH | NOT_RUN |
| TC011 | Low-confidence classification | E2E | HIGH | NOT_RUN |
| TC012 | Successful human transfer | E2E | HIGH | NOT_RUN |
| TC013 | Failed human transfer | E2E | HIGH | NOT_RUN |
| TC014 | Background noise simulation | Unit | MEDIUM | NOT_RUN |
| TC015 | User interruption / barge-in | E2E | MEDIUM | NOT_RUN |
| TC016 | Multiple concurrent calls | Load | HIGH | NOT_RUN |
| TC017 | Network interruption recovery | Integration | HIGH | NOT_RUN |
| TC018 | STT failure fallback | Integration | HIGH | NOT_RUN |
| TC019 | TTS failure fallback | Integration | HIGH | NOT_RUN |
| TC020 | LLM failure fallback | Integration | HIGH | NOT_RUN |
| TC021 | Telephony failure fallback | Integration | HIGH | NOT_RUN |
| TC022 | Database failure handling | Integration | HIGH | NOT_RUN |
| TC023 | Unauthorized dashboard access | Security | CRITICAL | NOT_RUN |
| TC024 | Unauthorized API access | Security | CRITICAL | NOT_RUN |
| TC025 | Sensitive data leakage check | Security | CRITICAL | NOT_RUN |

---

### 3.2 TC Specifications

#### TC001 — Human Recruiter Call

**Scenario:**
A human HR professional calls to discuss a job opening.

**Input conversation:**
```
CALLER: "Hi, this is Sarah from HR at TechCorp. I'm calling to discuss your recent application for the Software Engineer position."
AGENT: "Thank you for calling. Could you confirm the company name and the role?"
CALLER: "Sure, TechCorp, and it's for our backend engineering team. The interview would be next Tuesday at 10 AM."
```

**Expected results:**
- caller_type: HUMAN
- intent: RECRUITMENT
- risk_level: LOW
- company: TechCorp
- position: Software Engineer
- decision: NOTIFY or TRANSFER

**Pass criteria:** Correct classification with confidence ≥ 0.6, no false fraud flags.

---

#### TC002 — AI Recruiter Call

**Scenario:**
A legitimate company uses an AI recruitment assistant.

**Input conversation:**
```
CALLER: "Hello, I am an automated recruitment assistant from ABC Technologies. I am calling regarding your application for the Data Analyst position submitted on our careers portal."
AGENT: "Thank you. What is the next step in the process?"
CALLER: "We would like to schedule a technical interview. Would you be available next Thursday between 2 and 4 PM?"
```

**Expected results:**
- caller_type: AI
- intent: RECRUITMENT
- risk_level: LOW
- company: ABC Technologies
- position: Data Analyst
- decision: NOTIFY

**Pass criteria:** Must NOT classify as fraud simply because caller is AI.

---

#### TC006 — Human Fraud Caller

**Scenario:**
A human caller impersonates a bank and requests OTP.

**Input conversation:**
```
CALLER: "Hello, this is the fraud prevention team at HDFC Bank. We've detected suspicious activity on your account. For your security, please verify your OTP which has been sent to your registered number."
AGENT: "Which bank did you say you are from?"
CALLER: "HDFC Bank. This is urgent — your account will be blocked in the next 30 minutes unless you verify."
```

**Expected results:**
- caller_type: HUMAN
- intent: FRAUD
- risk_level: HIGH or CRITICAL
- risk_indicators: [OTP_REQUEST, URGENCY, IMPERSONATION, THREAT]
- decision: END or FLAG_FOR_REVIEW

---

#### TC008 — Fake Recruiter Requesting Payment

**Input conversation:**
```
CALLER: "Congratulations! Your resume has been shortlisted for a Senior Developer role at a leading MNC. To confirm your slot, please pay a registration fee of ₹5,000."
AGENT: "Why is there a registration fee for an interview?"
CALLER: "This is standard process. Payment secures your interview slot. Please pay via UPI immediately."
```

**Expected results:**
- intent: RECRUITMENT + FRAUD
- risk_level: HIGH or CRITICAL
- risk_indicators: [PAYMENT_REQUEST, JOB_REGISTRATION_FEE, URGENCY]
- decision: END or FLAG_FOR_REVIEW

**Pass criteria:** Must NOT classify as LOW risk. Must NOT allow payment.

---

#### TC009 — OTP Fraud

**Input conversation:**
```
CALLER: "This is an automated message from SBI. Your account has been suspended. To reactivate, enter OTP 482931 on our verification portal or share it with us now."
```

**Expected results:**
- risk_level: CRITICAL
- risk_indicators: [OTP_REQUEST, IMPERSONATION, URGENCY]
- decision: END

---

### 3.3 API Tests

| Test | Method | Endpoint | Expected |
|------|--------|----------|----------|
| Health check | GET | /health | 200, status=ok |
| Register user | POST | /api/v1/auth/register | 201, token |
| Duplicate register | POST | /api/v1/auth/register | 400 |
| Login valid | POST | /api/v1/auth/login | 200, token |
| Login invalid | POST | /api/v1/auth/login | 401 |
| Get me (auth) | GET | /api/v1/auth/me | 200, user |
| Get me (no token) | GET | /api/v1/auth/me | 401 |
| Get me (bad token) | GET | /api/v1/auth/me | 401 |
| Create call | POST | /api/v1/calls/incoming | 201, call |
| List calls (auth) | GET | /api/v1/calls | 200, list |
| List calls (no auth) | GET | /api/v1/calls | 401 |
| Get call valid | GET | /api/v1/calls/{id} | 200, detail |
| Get call missing | GET | /api/v1/calls/nonexistent | 404 |
| End call | POST | /api/v1/calls/{id}/end | 200 |
| Transfer call | POST | /api/v1/calls/{id}/transfer | 200 |
| Dashboard stats | GET | /api/v1/dashboard/statistics | 200, stats |
| Recent calls | GET | /api/v1/dashboard/recent-calls | 200, list |
| List notifications | GET | /api/v1/notifications | 200, list |
| Mark read | POST | /api/v1/notifications/{id}/read | 200 |
| Mark all read | POST | /api/v1/notifications/read-all | 200 |

---

### 3.4 Agent / ML Unit Tests

| Test | Agent | Input | Expected |
|------|-------|-------|----------|
| AI recruiter detection | CallerClassificationAgent | "I am an automated recruitment assistant" | AI, confidence > 0.7 |
| Human recruiter detection | CallerClassificationAgent | Natural conversational speech | HUMAN or UNKNOWN |
| Recruitment intent | IntentDetectionAgent | Interview/job conversation | RECRUITMENT |
| Fraud intent | IntentDetectionAgent | OTP request | FRAUD |
| Payment fraud indicator | FraudDetectionAgent | "Please pay ₹5,000" | PAYMENT_REQUEST, HIGH |
| OTP fraud indicator | FraudDetectionAgent | "Share your OTP" | OTP_REQUEST, CRITICAL |
| Low risk assessment | RiskAssessmentAgent | No fraud indicators, low confidence | LOW |
| High risk assessment | RiskAssessmentAgent | CRITICAL indicator | HIGH or CRITICAL |
| Recruitment + fraud decision | DecisionAgent | HIGH risk + FRAUD | END or FLAG |
| AI + recruitment + low risk | DecisionAgent | LOW risk + RECRUITMENT | NOTIFY |
| Low confidence unknown | DecisionAgent | UNKNOWN + low confidence | FLAG_FOR_REVIEW |

---

### 3.5 Performance Tests

| Metric | Target | Method | Status |
|--------|--------|--------|--------|
| API response time (p95) | < 200ms | Load test | NOT_MEASURED |
| Agent pipeline latency | < 500ms | Timer in pipeline | NOT_MEASURED |
| STT latency (mock) | < 50ms | Timer | NOT_MEASURED |
| LLM latency (mock) | < 100ms | Timer | NOT_MEASURED |
| TTS latency (mock) | < 50ms | Timer | NOT_MEASURED |
| DB write latency (p95) | < 50ms | Timer | NOT_MEASURED |
| WebSocket event latency | < 100ms | E2E timer | NOT_MEASURED |
| Concurrent calls | 10 simultaneous | Load test | NOT_MEASURED |

> [!IMPORTANT]
> All performance values above are TARGETS, not measured results.
> Mark as NOT_MEASURED until actual testing is completed.

---

### 3.6 Security Tests

| Test | Method | Status |
|------|--------|--------|
| JWT token expiry | Send expired token | NOT_RUN |
| SQL injection in call fields | Malicious input | NOT_RUN |
| XSS in caller name field | Script injection | NOT_RUN |
| Rate limit enforcement | Burst requests | NOT_RUN |
| CORS header validation | Cross-origin request | NOT_RUN |
| Secret in logs check | Log grep | NOT_RUN |
| Password hashing check | DB inspection | NOT_RUN |
| No .env in Git | git ls-files | NOT_RUN |

---

## 4. Test Commands

```bash
# Run all backend tests
cd "d:\Call gaurd AI"
pip install -r requirements.txt
pytest backend/tests/ -v --cov=backend --cov-report=term-missing

# Run specific test file
pytest backend/tests/test_calls.py -v

# Run with output
pytest backend/tests/ -v -s

# Run ML script syntax check
python -m py_compile ml/scripts/*.py
```

---

## 5. Test Report

See `docs/test-report.md` (to be created after test execution).

All results must be actual — not fabricated. If tests have not been run, status must be `NOT_RUN`.
