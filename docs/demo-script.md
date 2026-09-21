# CallGuard AI — Demo Script

**Version:** 1.0  
**Last Updated:** 2026-09-21

---

## Setup Before Demo

```bash
# Start the backend
cd "d:\Call gaurd AI"
python -m uvicorn backend.main:app --reload --port 8000

# In a second terminal — start the frontend (once built)
cd frontend
npm run dev

# Open browser
# http://localhost:3000  — Dashboard
# http://localhost:8000/docs  — API docs
```

---

## Demo 1: Human Recruiter Call (Legitimate)

**Scenario:** A human HR manager calls about a software engineering position.

**Expected outcome:** NOTIFY — call flagged as legitimate recruitment, low risk.

### Step 1 — Simulate Incoming Call

```bash
curl -X POST http://localhost:8000/api/v1/calls/incoming \
  -H "Content-Type: application/json" \
  -d '{
    "caller_number": "+911234567890",
    "virtual_number": "+919999999999",
    "telephony_call_id": "demo-001",
    "telephony_provider": "mock"
  }'
```

### Step 2 — Simulate Conversation

Use the demo conversation injection endpoint (mock mode):

```json
{
  "conversation": [
    {"speaker": "CALLER", "text": "Hi, this is Priya from TechCorp HR. I am calling about your application for the Senior Software Engineer role."},
    {"speaker": "AGENT", "text": "Thank you for calling. Could you confirm the company and position?"},
    {"speaker": "CALLER", "text": "Yes, TechCorp. The position is Senior Software Engineer in our Bangalore office. We would like to schedule an interview for next Wednesday at 11 AM."},
    {"speaker": "AGENT", "text": "Is there anything else I should note?"},
    {"speaker": "CALLER", "text": "Just bring your portfolio. The interview is with our CTO. No charges of any kind."}
  ]
}
```

### Expected Analysis
```
Caller Type:    HUMAN (confidence: ~0.65)
Intent:         RECRUITMENT (confidence: ~0.88)
Risk Level:     LOW
Risk Indicators: []
Company:        TechCorp
Position:       Senior Software Engineer
Interview:      Wednesday, 11 AM
Decision:       NOTIFY
Reason:         Legitimate recruitment call. No suspicious indicators.
```

### Dashboard
- Shows green LOW risk badge
- Notification: "Recruitment call — TechCorp, Senior Software Engineer"
- Full transcript visible

---

## Demo 2: AI Recruiter Call (Legitimate)

**Scenario:** A company's AI recruitment assistant calls regarding a Data Analyst application.

**Key point:** This must NOT be classified as fraud. AI caller ≠ dangerous.

**Expected outcome:** NOTIFY — AI recruitment, low risk.

### Conversation
```
CALLER: "Hello, I am an automated recruitment assistant from ABC Technologies. 
         I am calling regarding your application for the Data Analyst position."
AGENT:  "Could you share more details about the role?"
CALLER: "The position is in our analytics team in Mumbai. We would like to schedule a 
         technical screening next Friday between 2 and 5 PM. There are no charges of 
         any kind for this process."
```

### Expected Analysis
```
Caller Type:    AI (confidence: ~0.82)
Intent:         RECRUITMENT (confidence: ~0.91)
Risk Level:     LOW
Risk Indicators: []
Company:        ABC Technologies
Position:       Data Analyst
Decision:       NOTIFY
Reason:         AI recruitment assistant identified. No suspicious requests.
                NOTE: AI caller type alone does not indicate fraud.
```

---

## Demo 3: AI Interview Scheduler

**Scenario:** An AI assistant calls specifically to schedule an interview.

**Expected outcome:** NOTIFY — AI, recruitment, low risk, interview details extracted.

### Conversation
```
CALLER: "Good afternoon. This is the automated scheduling assistant from XYZ Corp. 
         You have been shortlisted for the Product Manager position. I am calling 
         to schedule your HR interview."
AGENT:  "What date and time is available?"
CALLER: "We have slots available on Monday September 28th at 10 AM, 2 PM, or 4 PM. 
         The interview will be conducted via video call."
```

### Expected Analysis
```
Caller Type:    AI (confidence: ~0.79)
Intent:         RECRUITMENT
Risk Level:     LOW
Company:        XYZ Corp
Position:       Product Manager
Interview Stage: HR
Interview Date: Monday, September 28
Decision:       NOTIFY
```

---

## Demo 4: AI Promotional Caller

**Scenario:** A company's AI system calls with a promotional offer.

**Expected outcome:** AI_HANDLE or END — promotional, low-medium risk, no fraud indicators.

### Conversation
```
CALLER: "Hello! This is an automated message from QuickInsure. As a valued customer, 
         you qualify for a 30% discount on our premium health insurance plan. 
         This offer is valid only until end of month."
AGENT:  "What is required to avail this offer?"
CALLER: "Simply call our customer care at 1800-XXX-XXXX to update your plan."
```

### Expected Analysis
```
Caller Type:    AI (confidence: ~0.84)
Intent:         PROMOTIONAL (confidence: ~0.87)
Risk Level:     LOW-MEDIUM
Risk Indicators: [URGENCY — "valid only until end of month"]
Decision:       AI_HANDLE or END
```

---

## Demo 5: Human Scammer

**Scenario:** A human scammer impersonates a bank's fraud prevention team.

**Expected outcome:** END or FLAG_FOR_REVIEW — HIGH/CRITICAL risk.

### Conversation
```
CALLER: "This is the fraud prevention department of HDFC Bank. We have detected 
         suspicious activity on your account ending in 4521. Your account will be 
         blocked within 30 minutes unless verified."
AGENT:  "How can I verify?"
CALLER: "Please share the OTP that has just been sent to your registered mobile number. 
         This is urgent. Do not delay."
```

### Expected Analysis
```
Caller Type:    HUMAN (confidence: ~0.61)
Intent:         FRAUD (confidence: ~0.93)
Risk Level:     CRITICAL
Risk Indicators: 
  - OTP_REQUEST (CRITICAL)
  - URGENCY (HIGH)
  - IMPERSONATION — claims to be bank (HIGH)
  - THREAT — account will be blocked (HIGH)
Decision:       END
Reason:         Critical risk: OTP request detected. Impersonation of bank. 
                Urgency tactics used. Call terminated to protect user.
```

### Dashboard
- Shows RED CRITICAL risk badge
- Notification: "⚠️ HIGH RISK FRAUD CALL DETECTED — OTP request blocked"

---

## Demo 6: AI Scammer

**Scenario:** A sophisticated AI system attempts to extract sensitive information.

**Expected outcome:** END or FLAG_FOR_REVIEW.

### Conversation
```
CALLER: "Hello. I am calling from the Income Tax Department's automated verification 
         system. Your PAN card has been flagged for suspicious transactions. 
         To avoid legal action, verify your Aadhaar number immediately."
AGENT:  "Which department?"
CALLER: "Income Tax Department. This is time-sensitive. Provide your Aadhaar within 
         the next 10 minutes to avoid account freezing and legal proceedings."
```

### Expected Analysis
```
Caller Type:    AI (confidence: ~0.78)
Intent:         FRAUD (confidence: ~0.91)
Risk Level:     CRITICAL
Risk Indicators:
  - SENSITIVE_PII (Aadhaar request) — CRITICAL
  - THREAT (legal action) — CRITICAL
  - URGENCY — HIGH
  - IMPERSONATION (government) — HIGH
Decision:       END
```

---

## Demo 7: Fake Recruiter Requesting Payment

**Scenario:** Caller impersonates a recruiter but asks for money.

**Expected outcome:** END or FLAG_FOR_REVIEW — RECRUITMENT + FRAUD.

### Conversation
```
CALLER: "Congratulations! Your profile was selected by our MNC client for an urgent 
         opening. To confirm your interview slot at our Pune office, you need to 
         pay a refundable processing fee of ₹3,500 via UPI before 6 PM today."
AGENT:  "Is this fee standard for all candidates?"
CALLER: "Yes, it is fully refundable after joining. Your slot is very competitive. 
         Please pay now to avoid cancellation."
```

### Expected Analysis
```
Caller Type:    HUMAN or AI (confidence: ~0.55)
Intent:         RECRUITMENT + FRAUD
Risk Level:     HIGH-CRITICAL
Risk Indicators:
  - PAYMENT_REQUEST (₹3,500) — HIGH
  - JOB_REGISTRATION_FEE — CRITICAL
  - URGENCY ("before 6 PM today") — HIGH
is_legitimate_recruitment: FALSE
legitimacy_reason: "Legitimate recruiters do not charge candidates"
Decision:       END or FLAG_FOR_REVIEW
```

---

## Demo 8: OTP Fraud

**Scenario:** Caller urgently demands OTP for "account security."

**Expected outcome:** END — CRITICAL risk.

### Conversation
```
CALLER: "This is an urgent automated alert from SBI. Your account has been 
         temporarily suspended due to suspicious login activity. To restore 
         access, please share the 6-digit OTP that has been sent to your number."
```

### Expected Analysis
```
Caller Type:    AI or ROBOCALL (confidence: ~0.81)
Intent:         FRAUD
Risk Level:     CRITICAL
Risk Indicators:
  - OTP_REQUEST — CRITICAL
  - URGENCY — HIGH
  - IMPERSONATION (SBI) — HIGH
Decision:       END
```

---

## Demo 9: Unknown Caller

**Scenario:** Caller gives vague information, intent unclear.

**Expected outcome:** FLAG_FOR_REVIEW — unknown, low confidence.

### Conversation
```
CALLER: "Hello... uh... I am calling for... regarding a matter. It's about... 
         some personal thing. Is this the right number?"
AGENT:  "Could you explain the purpose of your call?"
CALLER: "It's... it's something important. I just need to talk to someone."
```

### Expected Analysis
```
Caller Type:    UNKNOWN (confidence: ~0.41)
Intent:         UNKNOWN (confidence: ~0.38)
Risk Level:     MEDIUM
Decision:       FLAG_FOR_REVIEW
Reason:         Low confidence classification. Intent unclear. 
                Flagged for human review.
```

---

## Demo Notes

### What to Show on Dashboard

1. **Live call feed** — call coming in
2. **Real-time analysis** — watch risk level and intent update as conversation progresses
3. **Final decision** — color-coded risk badge
4. **Notification** — toaster notification
5. **Call details page** — full transcript + analysis breakdown
6. **Human transfer** — for Demo 1/2/3 (low risk), show transfer button
7. **Call history** — all 9 demos visible in call list

### Key Talking Points

- "Notice that Demo 2 is an AI caller but classified as LOW risk — because intent and behavior matter, not just caller type"
- "Demo 7 shows a HUMAN (or AI) caller pretending to be a recruiter — classified HIGH risk because of the payment request"
- "Demo 9 shows uncertain classification routed to FLAG_FOR_REVIEW — the system doesn't make irreversible decisions when confidence is low"
- "All decisions include an explanation — see the 'Decision Reason' field"

---

## STATUS: MOCK_IMPLEMENTATION

All demos above run using MockTelephonyProvider and rule-based agents.  
No real phone calls, no paid API required.  
Full AI agent pipeline runs locally.
