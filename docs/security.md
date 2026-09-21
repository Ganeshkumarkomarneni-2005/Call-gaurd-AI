# CallGuard AI — Security Architecture

**Document ID:** SEC-001  
**Version:** 1.0  
**Date:** 2026-09-17  
**Status:** Draft  

---

## 1. Authentication

### 1.1 JWT-Based Authentication

CallGuard AI uses JSON Web Tokens (JWT) for stateless authentication.

**Token specifications:**
- **Algorithm:** HS256 (HMAC-SHA256) in development; RS256 recommended for production
- **Access token lifetime:** Configurable via `ACCESS_TOKEN_EXPIRE_MINUTES` (default: 60 minutes)
- **Refresh token lifetime:** 7 days
- **Signing key:** `SECRET_KEY` environment variable — minimum 32 characters

**Token structure:**
```json
{
  "sub": "user_id_here",
  "email": "user@example.com",
  "role": "user",
  "exp": 1726555200,
  "iat": 1726551600
}
```

**Token flow:**
```
POST /api/v1/auth/login
  → Verify credentials (bcrypt)
  → Issue access_token (60min) + refresh_token (7d)
  → Client stores tokens (httpOnly cookies recommended)

All subsequent requests:
  Authorization: Bearer <access_token>

POST /api/v1/auth/refresh
  → Verify refresh_token
  → Issue new access_token
```

### 1.2 Password Security

- **Hashing:** bcrypt with work factor 12 (configurable)
- **Never stored in plaintext**
- **Minimum requirements:** 8 characters, mixed case, at least one digit
- **No password reset via email** in v1 (admin manual reset only)

### 1.3 WebSocket Authentication

WebSocket connections authenticate via JWT in the query string:
```
ws://host/ws?token=<access_token>
```

Token is validated on connection establishment. If invalid, the connection is rejected immediately (HTTP 401 before upgrade).

---

## 2. Authorization

### 2.1 Role-Based Access Control (RBAC)

| Role | Capabilities |
|------|-------------|
| `user` | Access own call history, manage own account, receive notifications |
| `admin` | All user capabilities + view all call records + manage users + system config |

### 2.2 Endpoint Authorization Matrix

| Endpoint | Method | Required Role |
|----------|--------|--------------|
| `/api/v1/auth/login` | POST | Public |
| `/api/v1/auth/refresh` | POST | Public (refresh token required) |
| `/health` | GET | Public |
| `/api/v1/calls` | GET | user, admin |
| `/api/v1/calls/{id}` | GET | user (own), admin (any) |
| `/api/v1/calls/{id}/action` | POST | user (own), admin (any) |
| `/api/v1/telephony/mock/inbound` | POST | admin (or disabled in production) |
| `/api/v1/admin/*` | ALL | admin only |

### 2.3 Resource Ownership

Users can only access their own resources. The backend enforces this by:
```python
# All queries scoped to current user
call = db.query(Call).filter(
    Call.id == call_id,
    Call.user_id == current_user.id  # Ownership enforcement
).first()
```

Admins bypass the ownership filter with an explicit role check.

---

## 3. Input Validation

### 3.1 Pydantic Validation

All API request bodies are validated with Pydantic v2 models before reaching business logic:

```python
class LoginRequest(BaseModel):
    email: EmailStr                          # Validates email format
    password: str = Field(min_length=8,      # Minimum length
                         max_length=128)     # Maximum length

class MockCallRequest(BaseModel):
    from_number: str = Field(pattern=r'^\+?[0-9]{10,15}$')  # Phone pattern
    scenario: Literal[                        # Only allowed values
        "legitimate_recruiter",
        "recruitment_scam",
        "bank_fraud",
        ...
    ]
```

### 3.2 SQL Injection Prevention

All database queries use SQLAlchemy ORM exclusively. Raw SQL is prohibited:

```python
# ✅ Safe: ORM with parameterized queries
calls = await db.execute(
    select(Call).where(Call.from_number == phone_number)
)

# ❌ PROHIBITED: Raw SQL
calls = await db.execute(f"SELECT * FROM calls WHERE from_number = '{phone_number}'")
```

### 3.3 Path Traversal Prevention

File paths from user input are never used directly. All file access uses predefined base directories.

---

## 4. Rate Limiting

| Endpoint Group | Limit | Window |
|---------------|-------|--------|
| `/api/v1/auth/login` | 10 requests | per minute per IP |
| `/api/v1/auth/refresh` | 30 requests | per minute per IP |
| `/api/v1/telephony/mock/inbound` | 5 requests | per minute per IP |
| All other `/api/v1/*` | 100 requests | per minute per IP |
| WebSocket connections | 5 connections | per user |

Rate limit responses return HTTP 429 with a `Retry-After` header.

**Implementation:** FastAPI middleware using in-memory sliding window (Redis recommended for multi-instance production deployments).

---

## 5. Secret Management

### 5.1 Policy

**No secrets in source code. Ever.**

- All secrets are environment variables
- `.env` file is in `.gitignore`
- Only `.env.example` (with empty/placeholder values) is committed
- CI/CD secrets managed via platform secret store (GitHub Actions secrets, Railway environment)

### 5.2 Required Secrets

| Variable | Required | Default Behavior if Empty |
|----------|----------|--------------------------|
| `SECRET_KEY` | ALWAYS | System fails to start |
| `DATABASE_URL` | ALWAYS | System fails to start |
| `EXOTEL_SID` | Production only | Falls back to mock |
| `GOOGLE_SPEECH_API_KEY` | Production only | Falls back to mock |
| `OPENAI_API_KEY` | Production only | Falls back to mock |

### 5.3 Secret Rotation

- `SECRET_KEY` rotation invalidates all existing JWTs — plan maintenance window
- Database password rotation requires connection string update + restart
- External API keys can be rotated without downtime if the adapter is stateless

---

## 6. HTTPS Requirements

### 6.1 Development

HTTP is acceptable in local development. TLS is not required for `localhost`.

### 6.2 Production (MANDATORY)

- **All HTTP traffic → redirect to HTTPS** (enforced at reverse proxy level)
- **All WebSocket traffic → WSS only** (enforced at application level in production)
- **TLS minimum version:** TLS 1.2; TLS 1.3 recommended
- **Certificate:** Let's Encrypt or platform-managed certificate
- **HSTS header:** `Strict-Transport-Security: max-age=31536000; includeSubDomains`

---

## 7. Safe Logging Policy

### 7.1 What Is Logged

```python
# Call processing — OK
logger.info("call_processed",
    call_id=call.id,           # ✅ Non-PII identifier
    risk_level="HIGH",         # ✅ Non-PII classification
    action="BLOCK",            # ✅ Non-PII action
    duration_ms=450            # ✅ Non-PII metric
)

# Error — OK
logger.error("model_inference_failed",
    call_id=call.id,           # ✅ Non-PII identifier
    agent="intent_classifier", # ✅ Non-PII component
    error_type="TimeoutError"  # ✅ Non-PII error type
)
```

### 7.2 What Is NEVER Logged

```python
# ❌ PII — PROHIBITED
logger.info("call", phone=call.from_number)       # Phone number
logger.info("transcript", text=turn.text)          # Call content
logger.info("auth", email=user.email)              # User email
logger.info("user", name=user.name)                # User name
logger.info("extraction", company=info.company)    # Caller info
```

### 7.3 Log Levels

| Level | Usage |
|-------|-------|
| DEBUG | Development only — verbose internal state |
| INFO | Normal operation events (call_started, action_taken) |
| WARNING | Non-critical issues (model confidence below threshold, retrying) |
| ERROR | Errors that need investigation but call can continue |
| CRITICAL | Errors that prevent system operation |

---

## 8. Database Security

### 8.1 Connection Security

- Database credentials in environment variables only
- Connection over SSL in production (`sslmode=require`)
- Connection pooling with limits (asyncpg pool: min=2, max=10)
- Database port NOT exposed publicly in production

### 8.2 Data at Rest

- Use managed PostgreSQL (Neon/Supabase) which provides encryption at rest
- For self-hosted: enable PostgreSQL TDE or disk-level encryption
- Database backups encrypted before storage

### 8.3 Least Privilege

The application database user has only:
- `SELECT`, `INSERT`, `UPDATE`, `DELETE` on application tables
- `EXECUTE` on needed stored procedures
- No `DROP`, `CREATE`, `ALTER` privileges (Alembic uses separate migration user)

---

## 9. WebSocket Security

### 9.1 Connection Authentication

- JWT validated on WebSocket upgrade (before connection established)
- Invalid token → HTTP 401 → connection refused (no WebSocket upgrade)

### 9.2 Message Validation

- Server only sends to authenticated clients
- Server ignores any message from client that doesn't match expected format
- Clients cannot subscribe to other users' events

### 9.3 Denial of Service Protection

- Maximum WebSocket connections per user: 5
- Message size limit: 64KB
- Idle connection timeout: 5 minutes

---

## 10. Threat Model

### 10.1 Threat Actors

| Actor | Capability | Motivation |
|-------|-----------|-----------|
| **Spammer/Scammer** | Can call any number, change caller ID | Bypass screening to reach victim |
| **External attacker** | Internet access to API | Steal call data, bypass auth |
| **Insider** | System access (developer, admin) | Data theft, service disruption |
| **Automated bot** | High-volume API calls | DoS, credential stuffing |

### 10.2 Key Threats and Mitigations

| Threat | Likelihood | Impact | Mitigation |
|--------|-----------|--------|-----------|
| **Credential stuffing** on login | HIGH | HIGH | Rate limiting (10 req/min), bcrypt (slow hashing) |
| **JWT token theft** | MEDIUM | HIGH | Short expiry (60min), HTTPS-only, httpOnly cookies |
| **SQL injection** | LOW | CRITICAL | SQLAlchemy ORM exclusively, no raw SQL |
| **Transcript data breach** | LOW | HIGH | DB encryption, no PII in logs, access controls |
| **DoS on telephony endpoint** | MEDIUM | HIGH | Rate limiting, auth required for mock endpoint |
| **Fraudulent call bypass via adversarial input** | MEDIUM | MEDIUM | Fail-safe defaults (SCREEN on low confidence) |
| **Admin account compromise** | LOW | CRITICAL | Strong password policy, 2FA recommended |
| **ML model poisoning** (if retraining from user data) | LOW | MEDIUM | User opt-in required; data review before retraining |

### 10.3 Security Assumptions (Trust Boundaries)

- The telephony provider (Exotel) is trusted
- Caller Telephony IDs (phone numbers) are NOT trusted — spoofing is assumed possible
- The database server is in a trusted network (not publicly accessible)
- Application server is trusted within the Docker network
- Client browsers are NOT trusted — all authorization enforced server-side
