# CallGuard AI — API Reference

**Version:** 0.1.0  
**Base URL (local):** `http://localhost:8000`  
**API Prefix:** `/api/v1`  
**WebSocket Base:** `ws://localhost:8000`

---

## Authentication

All protected endpoints require a JWT Bearer token.

```
Authorization: Bearer <access_token>
```

Obtain a token via `POST /api/v1/auth/login`.

---

## Endpoints

---

### Health

#### `GET /health`

Check service health. No authentication required.

**Response 200:**
```json
{
  "status": "ok",
  "timestamp": "2026-09-21T06:00:00.000000",
  "service": "CallGuard AI",
  "version": "0.1.0"
}
```

---

### Authentication

#### `POST /api/v1/auth/register`

Register a new user.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword",
  "full_name": "Jane Doe",
  "phone_number": "+919876543210"
}
```

**Response 201:**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

**Errors:**
- `400` — Email already registered

---

#### `POST /api/v1/auth/login`

Login with credentials (OAuth2 form).

**Request Form:**
```
username=user@example.com&password=securepassword
```

**Response 200:**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

**Errors:**
- `401` — Incorrect email or password

---

#### `GET /api/v1/auth/me`

Get current authenticated user. **Requires auth.**

**Response 200:**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "Jane Doe",
  "phone_number": "+919876543210",
  "is_active": true,
  "is_admin": false,
  "created_at": "2026-09-21T06:00:00"
}
```

---

### Calls

#### `POST /api/v1/calls/incoming`

Register an incoming call. Called by telephony provider webhook.

**Request Body:**
```json
{
  "caller_number": "+911234567890",
  "virtual_number": "+919999999999",
  "telephony_call_id": "exotel-call-id-123",
  "telephony_provider": "mock"
}
```

**Response 201:**
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "status": "RINGING",
  "caller_number": "+911234567890",
  "caller_name": null,
  "virtual_number": "+919999999999",
  "telephony_provider": "mock",
  "started_at": "2026-09-21T06:00:00",
  "ended_at": null,
  "duration_seconds": null,
  "created_at": "2026-09-21T06:00:00"
}
```

**Behavior:**
- Creates call record in database
- Triggers background AI analysis pipeline
- Sends `call.started` WebSocket event

---

#### `GET /api/v1/calls`

List calls for the authenticated user. **Requires auth.**

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | int | 1 | Page number |
| `page_size` | int | 20 | Results per page (max 100) |

**Response 200:**
```json
{
  "calls": [...],
  "total": 42,
  "page": 1,
  "page_size": 20
}
```

---

#### `GET /api/v1/calls/{call_id}`

Get full call details. **Requires auth.**

**Response 200:**
```json
{
  "call": { ... },
  "transcript": { ... },
  "analysis": { ... },
  "recruitment_details": { ... },
  "risk_events": [...],
  "decisions": [...],
  "actions": [...]
}
```

**Errors:**
- `404` — Call not found

---

#### `GET /api/v1/calls/{call_id}/transcript`

Get call transcript. **Requires auth.**

**Response 200:**
```json
{
  "id": "uuid",
  "call_id": "uuid",
  "full_text": "Hello, this is an automated...",
  "summary": "AI recruitment call from ABC Technologies...",
  "segments": [
    {
      "id": "uuid",
      "speaker": "CALLER",
      "text": "Hello, this is an automated recruitment assistant...",
      "start_ms": 1200,
      "end_ms": 4800,
      "confidence": 0.94
    }
  ],
  "word_count": 87,
  "created_at": "2026-09-21T06:00:00"
}
```

---

#### `GET /api/v1/calls/{call_id}/summary`

Get AI-generated call summary. **Requires auth.**

**Response 200:**
```json
{
  "call_id": "uuid",
  "summary": "This was an AI recruitment call from ABC Technologies...",
  "key_points": ["AI caller identified", "Recruitment intent", "No fraud indicators"],
  "decision": "NOTIFY",
  "risk_level": "LOW"
}
```

---

#### `GET /api/v1/calls/{call_id}/analysis`

Get detailed call analysis. **Requires auth.**

**Response 200:**
```json
{
  "id": "uuid",
  "call_id": "uuid",
  "caller_type": "AI",
  "caller_type_confidence": 0.87,
  "intent": "RECRUITMENT",
  "secondary_intent": null,
  "intent_confidence": 0.91,
  "risk_level": "LOW",
  "risk_confidence": 0.89,
  "risk_indicators": [],
  "decision": "NOTIFY",
  "decision_reason": "AI caller identified as recruitment-related. No suspicious requests detected.",
  "decision_confidence": 0.88,
  "analysis_latency_ms": 142,
  "created_at": "2026-09-21T06:00:00"
}
```

---

#### `POST /api/v1/calls/{call_id}/transfer`

Initiate human transfer. **Requires auth.**

**Request Body:**
```json
{
  "destination_number": "+911234567890",
  "agent_notes": "Recruitment call, low risk"
}
```

**Response 200:**
```json
{
  "call_id": "uuid",
  "status": "TRANSFERRED",
  "transfer_initiated_at": "2026-09-21T06:00:00"
}
```

---

#### `POST /api/v1/calls/{call_id}/continue`

Continue AI handling of a call.

**Response 200:**
```json
{
  "call_id": "uuid",
  "status": "ACTIVE"
}
```

---

#### `POST /api/v1/calls/{call_id}/end`

End a call. **Requires auth.**

**Response 200:**
```json
{
  "call_id": "uuid",
  "status": "ENDED",
  "duration_seconds": 127
}
```

---

### Dashboard

#### `GET /api/v1/dashboard/statistics`

Get dashboard statistics. **Requires auth.**

**Response 200:**
```json
{
  "total_calls": 142,
  "today_calls": 8,
  "ai_callers": 67,
  "human_callers": 54,
  "robocalls": 12,
  "unknown_callers": 9,
  "recruitment_calls": 23,
  "promotional_calls": 41,
  "fraud_calls": 7,
  "transferred_calls": 19,
  "ai_handled_calls": 98,
  "risk_distribution": {
    "LOW": 89,
    "MEDIUM": 34,
    "HIGH": 14,
    "CRITICAL": 5
  },
  "intent_distribution": {
    "RECRUITMENT": 23,
    "PROMOTIONAL": 41,
    "FRAUD": 7,
    "CUSTOMER_SERVICE": 28,
    "DELIVERY": 15,
    "PERSONAL": 12,
    "OTHER": 11,
    "UNKNOWN": 5
  },
  "caller_type_distribution": {
    "HUMAN": 54,
    "AI": 67,
    "ROBOCALL": 12,
    "UNKNOWN": 9
  }
}
```

---

#### `GET /api/v1/dashboard/recent-calls`

Get the 10 most recent calls. **Requires auth.**

---

#### `GET /api/v1/dashboard/risk-summary`

Get risk level breakdown. **Requires auth.**

---

### Notifications

#### `GET /api/v1/notifications`

List notifications. **Requires auth.**

**Query Parameters:**
| Parameter | Type | Default |
|-----------|------|---------|
| `page` | int | 1 |
| `page_size` | int | 20 |
| `unread_only` | bool | false |

**Response 200:**
```json
{
  "notifications": [...],
  "unread_count": 3,
  "total": 17
}
```

---

#### `POST /api/v1/notifications/{notification_id}/read`

Mark a notification as read. **Requires auth.**

**Response 200:** `{"success": true}`

---

#### `POST /api/v1/notifications/read-all`

Mark all notifications as read. **Requires auth.**

**Response 200:** `{"marked_read": 3}`

---

## WebSocket Events

### Call Events: `ws://localhost:8000/ws/{call_id}`

After connecting, send a JSON message to subscribe:
```json
{"action": "subscribe", "call_id": "uuid"}
```

#### Received Events

| Event | Description |
|-------|-------------|
| `call.started` | Call answered by AI |
| `call.audio` | Audio chunk received |
| `transcript.updated` | New transcript segment |
| `caller.type.detected` | Caller classification result |
| `intent.detected` | Intent classification result |
| `risk.updated` | Risk level changed |
| `recruitment.detected` | Recruitment details extracted |
| `notification.created` | New notification |
| `transfer.requested` | Human transfer initiated |
| `transfer.completed` | Transfer successful |
| `call.ended` | Call terminated |

#### Event Payload Example

```json
{
  "event": "caller.type.detected",
  "call_id": "uuid",
  "timestamp": "2026-09-21T06:00:00",
  "data": {
    "caller_type": "AI",
    "confidence": 0.87,
    "evidence": ["Self-identified as automated assistant", "Scripted speech patterns"]
  }
}
```

### Notification Events: `ws://localhost:8000/ws/notifications/{user_id}`

Real-time notification stream for a user.

---

## Error Codes

| Status | Meaning |
|--------|---------|
| `400` | Bad request — validation error |
| `401` | Unauthorized — missing or invalid token |
| `403` | Forbidden — insufficient permissions |
| `404` | Not found |
| `409` | Conflict — duplicate resource |
| `422` | Unprocessable entity — schema validation failed |
| `429` | Too many requests — rate limit exceeded |
| `500` | Internal server error |
| `503` | Service unavailable — external provider down |

---

## Rate Limits

| Endpoint Group | Limit |
|---------------|-------|
| `/auth/*` | 10 requests/minute per IP |
| `/calls/incoming` | 60 requests/minute |
| `/api/v1/*` | 200 requests/minute per user |
| WebSocket connections | 5 per user |
