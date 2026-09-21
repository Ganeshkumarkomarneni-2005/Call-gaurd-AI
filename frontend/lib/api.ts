/**
 * API client for CallGuard AI backend.
 * All functions use the NEXT_PUBLIC_API_URL environment variable.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// ─── Types ────────────────────────────────────────────────────────────────────

export interface Call {
  id: string;
  user_id: string;
  status: 'RINGING' | 'ACTIVE' | 'ENDED' | 'TRANSFERRED' | 'FAILED' | string;
  caller_number: string | null;
  caller_name: string | null;
  virtual_number: string;
  telephony_provider: string;
  started_at: string;
  ended_at: string | null;
  duration_seconds: number | null;
  created_at: string;
}

export interface CallAnalysis {
  id: string;
  call_id: string;
  caller_type: 'HUMAN' | 'AI' | 'ROBOCALL' | 'UNKNOWN';
  caller_type_confidence: number;
  intent: string;
  secondary_intent: string | null;
  intent_confidence: number;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  risk_confidence: number;
  risk_indicators: string[];
  decision: 'AI_HANDLE' | 'NOTIFY' | 'TRANSFER' | 'END' | 'FLAG_FOR_REVIEW';
  decision_reason: string;
  decision_confidence: number;
  analysis_latency_ms: number | null;
  created_at: string;
}

export interface RecruitmentDetails {
  id: string;
  call_id: string;
  company: string | null;
  recruiter_name: string | null;
  position: string | null;
  interview_stage: string | null;
  interview_date: string | null;
  interview_time: string | null;
  next_step: string | null;
  is_legitimate: boolean | null;
  legitimacy_reason: string | null;
  extracted_at: string;
}

export interface TranscriptSegment {
  id: string;
  speaker: 'CALLER' | 'AGENT';
  text: string;
  start_ms: number;
  end_ms: number | null;
  confidence: number | null;
}

export interface Transcript {
  id: string;
  call_id: string;
  full_text: string;
  summary: string | null;
  segments: TranscriptSegment[];
  word_count: number;
  created_at: string;
}

export interface CallDetail {
  call: Call;
  transcript: Transcript | null;
  analysis: CallAnalysis | null;
  recruitment_details: RecruitmentDetails | null;
  risk_events: unknown[];
  decisions: unknown[];
  actions: unknown[];
}

export interface DashboardStats {
  total_calls: number;
  today_calls: number;
  ai_callers: number;
  human_callers: number;
  robocalls: number;
  unknown_callers: number;
  recruitment_calls: number;
  promotional_calls: number;
  fraud_calls: number;
  transferred_calls: number;
  ai_handled_calls: number;
  risk_distribution: Record<string, number>;
  intent_distribution: Record<string, number>;
  caller_type_distribution: Record<string, number>;
}

export interface Notification {
  id: string;
  call_id: string | null;
  notification_type: string;
  title: string;
  body: string;
  read: boolean;
  read_at: string | null;
  created_at: string;
}

export interface CallListResponse {
  calls: Call[];
  total: number;
  page: number;
  page_size: number;
}

export interface NotificationListResponse {
  notifications: Notification[];
  unread_count: number;
  total: number;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
}

export interface User {
  id: string;
  email: string;
  full_name: string | null;
  phone_number: string | null;
  is_active: boolean;
  is_admin: boolean;
  created_at: string;
}

// ─── Token Storage ─────────────────────────────────────────────────────────────

export function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('callguard_token');
}

export function setToken(token: string): void {
  if (typeof window !== 'undefined') {
    localStorage.setItem('callguard_token', token);
  }
}

export function clearToken(): void {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('callguard_token');
  }
}

// ─── Base Fetch ─────────────────────────────────────────────────────────────────

async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  } catch (networkErr) {
    // Real connection failure (server down, CORS preflight blocked, etc.)
    throw new Error('NETWORK_ERROR: Cannot reach backend at ' + API_BASE);
  }

  if (response.status === 401) {
    throw new Error('AUTH_REQUIRED');
  }

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json() as Promise<T>;
}

// ─── Auth ───────────────────────────────────────────────────────────────────────

export const authApi = {
  login: async (email: string, password: string): Promise<AuthToken> => {
    const form = new URLSearchParams();
    form.append('username', email);
    form.append('password', password);
    const response = await fetch(`${API_BASE}/api/v1/auth/login`, {
      method: 'POST',
      body: form,
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: 'Login failed' }));
      throw new Error(err.detail || 'Login failed');
    }
    return response.json();
  },

  register: async (email: string, password: string, fullName?: string): Promise<AuthToken> =>
    apiFetch('/api/v1/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, full_name: fullName }),
    }),

  me: async (): Promise<User> => apiFetch('/api/v1/auth/me'),
};

// ─── Calls ──────────────────────────────────────────────────────────────────────

export const callsApi = {
  list: async (page = 1, pageSize = 20): Promise<CallListResponse> =>
    apiFetch(`/api/v1/calls?page=${page}&page_size=${pageSize}`),

  get: async (callId: string): Promise<CallDetail> =>
    apiFetch(`/api/v1/calls/${callId}`),

  getAnalysis: async (callId: string): Promise<CallAnalysis> =>
    apiFetch(`/api/v1/calls/${callId}/analysis`),

  getTranscript: async (callId: string): Promise<Transcript> =>
    apiFetch(`/api/v1/calls/${callId}/transcript`),

  getSummary: async (callId: string): Promise<{ call_id: string; summary: string; key_points: string[]; decision: string; risk_level: string }> =>
    apiFetch(`/api/v1/calls/${callId}/summary`),

  end: async (callId: string): Promise<{ call_id: string; status: string; duration_seconds: number }> =>
    apiFetch(`/api/v1/calls/${callId}/end`, { method: 'POST' }),

  transfer: async (callId: string, destination: string, notes?: string) =>
    apiFetch(`/api/v1/calls/${callId}/transfer`, {
      method: 'POST',
      body: JSON.stringify({ destination_number: destination, agent_notes: notes }),
    }),

  simulateIncoming: async (callerNumber: string): Promise<Call> =>
    apiFetch('/api/v1/calls/incoming', {
      method: 'POST',
      body: JSON.stringify({
        caller_number: callerNumber,
        virtual_number: '+919999999999',
        telephony_call_id: `demo-${Date.now()}`,
        telephony_provider: 'mock',
      }),
    }),
};

// ─── Dashboard ──────────────────────────────────────────────────────────────────

export const dashboardApi = {
  stats: async (): Promise<DashboardStats> =>
    apiFetch('/api/v1/dashboard/statistics'),

  recentCalls: async (): Promise<Call[]> =>
    apiFetch('/api/v1/dashboard/recent-calls'),
};

// ─── Notifications ───────────────────────────────────────────────────────────────

export const notificationsApi = {
  list: async (page = 1, pageSize = 20): Promise<NotificationListResponse> =>
    apiFetch(`/api/v1/notifications?page=${page}&page_size=${pageSize}`),

  markRead: async (id: string): Promise<{ success: boolean }> =>
    apiFetch(`/api/v1/notifications/${id}/read`, { method: 'POST' }),

  markAllRead: async (): Promise<{ marked_read: number }> =>
    apiFetch('/api/v1/notifications/read-all', { method: 'POST' }),
};

// ─── Health ─────────────────────────────────────────────────────────────────────

export const healthApi = {
  check: async (): Promise<{ status: string; timestamp: string; service: string }> =>
    apiFetch('/health'),
};
