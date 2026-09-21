'use client';

import { useEffect, useState } from 'react';
import { dashboardApi, callsApi, notificationsApi, getToken, type DashboardStats, type Call, type Notification } from '@/lib/api';
import { formatRelativeTime, formatDuration, riskBadgeClass, callerTypeBadgeClass, intentLabel, decisionLabel, type RiskLevel, type CallerType } from '@/lib/utils';
import {
  BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis,
  CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts';
import { Phone, Shield, AlertTriangle, Users, Bot, Megaphone, Briefcase, Bell, Activity, RefreshCw } from 'lucide-react';

// ─── Stat Card ────────────────────────────────────────────────────────────────

function StatCard({
  label, value, icon: Icon, color = 'text-slate-700', bgColor = 'bg-slate-50',
}: {
  label: string; value: number | string; icon: React.ElementType;
  color?: string; bgColor?: string;
}) {
  return (
    <div className="card flex items-center gap-4">
      <div className={`p-3 rounded-lg ${bgColor}`}>
        <Icon className={`w-6 h-6 ${color}`} />
      </div>
      <div>
        <p className="text-2xl font-bold text-slate-900">{value}</p>
        <p className="text-sm text-slate-500">{label}</p>
      </div>
    </div>
  );
}

// ─── Risk Badge ───────────────────────────────────────────────────────────────

function RiskBadge({ risk }: { risk: string }) {
  return <span className={riskBadgeClass(risk as RiskLevel)}>{risk}</span>;
}

function CallerTypeBadge({ type }: { type: string }) {
  return <span className={callerTypeBadgeClass(type as CallerType)}>{type}</span>;
}

// ─── Recent Calls Table ───────────────────────────────────────────────────────

function RecentCallsTable({ calls }: { calls: Call[] }) {
  if (calls.length === 0) {
    return (
      <div className="text-center py-12 text-slate-400">
        <Phone className="w-12 h-12 mx-auto mb-3 opacity-30" />
        <p>No calls yet. Start the backend and simulate a call.</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-slate-100">
            <th className="text-left py-3 px-2 text-slate-500 font-medium">Caller</th>
            <th className="text-left py-3 px-2 text-slate-500 font-medium">Status</th>
            <th className="text-left py-3 px-2 text-slate-500 font-medium">Duration</th>
            <th className="text-left py-3 px-2 text-slate-500 font-medium">Time</th>
          </tr>
        </thead>
        <tbody>
          {calls.map((call) => (
            <tr key={call.id} className="border-b border-slate-50 hover:bg-slate-50 transition-colors">
              <td className="py-3 px-2">
                <div className="font-medium text-slate-800">
                  {call.caller_number || 'Unknown'}
                </div>
                <div className="text-xs text-slate-400">{call.telephony_provider}</div>
              </td>
              <td className="py-3 px-2">
                <span className={`badge ${
                  call.status === 'ENDED' ? 'bg-slate-100 text-slate-600'
                  : call.status === 'ACTIVE' ? 'bg-green-100 text-green-700'
                  : call.status === 'TRANSFERRED' ? 'bg-blue-100 text-blue-700'
                  : call.status === 'FAILED' ? 'bg-red-100 text-red-700'
                  : 'bg-amber-100 text-amber-700'
                }`}>{call.status}</span>
              </td>
              <td className="py-3 px-2 text-slate-600">
                {formatDuration(call.duration_seconds)}
              </td>
              <td className="py-3 px-2 text-slate-400 text-xs">
                {formatRelativeTime(call.created_at)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ─── Distribution Charts ──────────────────────────────────────────────────────

const RISK_COLORS: Record<string, string> = {
  LOW: '#22c55e', MEDIUM: '#f59e0b', HIGH: '#ef4444', CRITICAL: '#7c3aed',
};

const CALLER_COLORS: Record<string, string> = {
  HUMAN: '#10b981', AI: '#3b82f6', ROBOCALL: '#f97316', UNKNOWN: '#94a3b8',
};

function DistributionPie({
  data, colors, title,
}: {
  data: Record<string, number>;
  colors: Record<string, string>;
  title: string;
}) {
  const chartData = Object.entries(data).map(([name, value]) => ({ name, value }));
  const total = chartData.reduce((s, d) => s + d.value, 0);

  if (total === 0) {
    return (
      <div>
        <h3 className="text-sm font-semibold text-slate-700 mb-4">{title}</h3>
        <div className="h-48 flex items-center justify-center text-slate-300 text-sm">No data yet</div>
      </div>
    );
  }

  return (
    <div>
      <h3 className="text-sm font-semibold text-slate-700 mb-4">{title}</h3>
      <ResponsiveContainer width="100%" height={200}>
        <PieChart>
          <Pie data={chartData} cx="50%" cy="50%" innerRadius={50} outerRadius={80} dataKey="value">
            {chartData.map((entry) => (
              <Cell key={entry.name} fill={colors[entry.name] || '#94a3b8'} />
            ))}
          </Pie>
          <Tooltip formatter={(v: number) => [`${v} calls`, '']} />
          <Legend iconSize={10} />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}

function IntentBarChart({ data }: { data: Record<string, number> }) {
  const chartData = Object.entries(data)
    .filter(([, v]) => v > 0)
    .map(([name, value]) => ({ name: name.substring(0, 8), value, fullName: name }));

  if (chartData.length === 0) {
    return (
      <div>
        <h3 className="text-sm font-semibold text-slate-700 mb-4">Intent Distribution</h3>
        <div className="h-48 flex items-center justify-center text-slate-300 text-sm">No data yet</div>
      </div>
    );
  }

  return (
    <div>
      <h3 className="text-sm font-semibold text-slate-700 mb-4">Intent Distribution</h3>
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={chartData} margin={{ top: 0, right: 0, bottom: 0, left: -20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
          <XAxis dataKey="name" tick={{ fontSize: 10 }} />
          <YAxis tick={{ fontSize: 10 }} />
          <Tooltip labelFormatter={(l) => chartData.find(d => d.name === l)?.fullName || l} />
          <Bar dataKey="value" fill="#3b82f6" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

// ─── Notifications Panel ──────────────────────────────────────────────────────

function NotificationsPanel({ notifications }: { notifications: Notification[] }) {
  const typeIcon: Record<string, string> = {
    RECRUITMENT_DETECTED: '💼',
    FRAUD_DETECTED: '⚠️',
    HIGH_RISK: '🚨',
    TRANSFER_REQUESTED: '↗️',
    UNKNOWN_CALLER: '🔍',
    CALL_ENDED: '📵',
    CALL_STARTED: '📞',
  };

  if (notifications.length === 0) {
    return (
      <div className="text-center py-8 text-slate-400">
        <Bell className="w-8 h-8 mx-auto mb-2 opacity-30" />
        <p className="text-sm">No notifications</p>
      </div>
    );
  }

  return (
    <ul className="space-y-2">
      {notifications.slice(0, 5).map((n) => (
        <li
          key={n.id}
          className={`flex gap-3 p-3 rounded-lg text-sm ${n.read ? 'bg-slate-50' : 'bg-blue-50 border border-blue-100'}`}
        >
          <span className="text-lg">{typeIcon[n.notification_type] || '🔔'}</span>
          <div className="flex-1 min-w-0">
            <p className={`font-medium ${n.read ? 'text-slate-600' : 'text-slate-900'}`}>{n.title}</p>
            <p className="text-slate-400 text-xs truncate">{n.body}</p>
            <p className="text-slate-300 text-xs mt-0.5">{formatRelativeTime(n.created_at)}</p>
          </div>
        </li>
      ))}
    </ul>
  );
}

// ─── Demo Simulator ───────────────────────────────────────────────────────────

const DEMO_NUMBERS = [
  { label: 'Simulate incoming call', number: '+911234567890' },
];

function DemoSimulator({ onSimulate }: { onSimulate: () => void }) {
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  const simulate = async () => {
    setLoading(true);
    setMessage('');
    try {
      await callsApi.simulateIncoming('+911234567890');
      setMessage('✅ Mock call created! Refresh to see it in the list.');
      onSimulate();
    } catch (e) {
      setMessage(`❌ ${e instanceof Error ? e.message : 'Failed'} — is the backend running?`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card border-dashed border-brand-500 bg-brand-50">
      <h3 className="font-semibold text-brand-900 mb-2 flex items-center gap-2">
        <Activity className="w-4 h-4" /> Simulate Incoming Call
      </h3>
      <p className="text-sm text-brand-700 mb-4">
        Create a mock incoming call to test the pipeline. Requires backend running at{' '}
        <code className="bg-brand-100 px-1 rounded text-xs">localhost:8000</code>.
      </p>
      <button onClick={simulate} disabled={loading} className="btn-primary">
        {loading ? 'Creating call…' : '📞 Simulate Call'}
      </button>
      {message && <p className="mt-2 text-sm">{message}</p>}
    </div>
  );
}

// ─── Main Dashboard ───────────────────────────────────────────────────────────

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [calls, setCalls] = useState<Call[]>([]);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefreshed, setLastRefreshed] = useState<Date>(new Date());

  // Redirect to /login if not authenticated
  const redirectToLogin = () => {
    if (typeof window !== 'undefined') {
      window.location.href = '/login';
    }
  };

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [statsData, callsData, notifData] = await Promise.allSettled([
        dashboardApi.stats(),
        dashboardApi.recentCalls(),
        notificationsApi.list(1, 10),
      ]);

      // Check for auth errors first — any 401 means redirect to login
      const authError = [statsData, callsData, notifData].find(
        (r) => r.status === 'rejected' && r.reason?.message === 'AUTH_REQUIRED'
      );
      if (authError) {
        redirectToLogin();
        return;
      }

      if (statsData.status === 'fulfilled') setStats(statsData.value);
      if (callsData.status === 'fulfilled') setCalls(callsData.value);
      if (notifData.status === 'fulfilled') setNotifications(notifData.value.notifications);

      // Show connection error only for genuine network failures
      if (statsData.status === 'rejected') {
        const msg = statsData.reason?.message || '';
        if (msg.startsWith('NETWORK_ERROR')) {
          setError('Cannot reach backend at http://localhost:8000 — is it running?');
        } else {
          setError(`API error: ${msg}`);
        }
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load data');
    } finally {
      setLoading(false);
      setLastRefreshed(new Date());
    }
  };

  useEffect(() => {
    // Redirect immediately if no token is stored (user not logged in)
    if (!getToken()) {
      redirectToLogin();
      return;
    }
    loadData();
    // Auto-refresh every 30 seconds
    const interval = setInterval(loadData, 30_000);
    return () => clearInterval(interval);
  }, []);

  if (loading && !stats) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-brand-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-slate-500">Connecting to CallGuard AI…</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Shield className="w-8 h-8 text-brand-600" />
            <div>
              <h1 className="text-xl font-bold text-slate-900">CallGuard AI</h1>
              <p className="text-xs text-slate-400">Intelligent Call Screening Dashboard</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {notifications.filter(n => !n.read).length > 0 && (
              <span className="flex items-center gap-1.5 text-sm text-slate-600">
                <Bell className="w-4 h-4" />
                <span className="bg-red-500 text-white text-xs rounded-full px-1.5 py-0.5">
                  {notifications.filter(n => !n.read).length}
                </span>
              </span>
            )}
            <button
              onClick={loadData}
              className="btn-secondary flex items-center gap-2 text-xs"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
            <span className="text-xs text-slate-400">
              Updated {formatRelativeTime(lastRefreshed.toISOString())}
            </span>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8 space-y-8">
        {/* Error Banner */}
        {error && (
          <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-medium text-amber-800">Backend not connected</p>
              <p className="text-sm text-amber-600 mt-1">{error}</p>
              <code className="text-xs bg-amber-100 px-2 py-1 rounded mt-2 block w-fit">
                python -m uvicorn backend.main:app --reload
              </code>
            </div>
          </div>
        )}

        {/* Core Principle Banner */}
        <div className="bg-gradient-to-r from-brand-900 to-brand-600 text-white rounded-xl p-5">
          <p className="text-sm font-medium opacity-75 mb-1">Core Intelligence Principle</p>
          <p className="text-lg font-bold">
            CALLER TYPE ≠ INTENT ≠ RISK ≠ ACTION
          </p>
          <p className="text-sm opacity-75 mt-1">
            A legitimate AI caller is not dangerous. A human caller can be a scammer. Every dimension is assessed independently.
          </p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard label="Total Calls" value={stats?.total_calls ?? 0} icon={Phone} bgColor="bg-blue-50" color="text-blue-600" />
          <StatCard label="Today's Calls" value={stats?.today_calls ?? 0} icon={Activity} bgColor="bg-emerald-50" color="text-emerald-600" />
          <StatCard label="Fraud Calls" value={stats?.fraud_calls ?? 0} icon={AlertTriangle} bgColor="bg-red-50" color="text-red-600" />
          <StatCard label="Recruitment" value={stats?.recruitment_calls ?? 0} icon={Briefcase} bgColor="bg-purple-50" color="text-purple-600" />
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard label="AI Callers" value={stats?.ai_callers ?? 0} icon={Bot} bgColor="bg-blue-50" color="text-blue-500" />
          <StatCard label="Human Callers" value={stats?.human_callers ?? 0} icon={Users} bgColor="bg-green-50" color="text-green-600" />
          <StatCard label="Transferred" value={stats?.transferred_calls ?? 0} icon={Phone} bgColor="bg-amber-50" color="text-amber-600" />
          <StatCard label="Promotional" value={stats?.promotional_calls ?? 0} icon={Megaphone} bgColor="bg-orange-50" color="text-orange-600" />
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="card">
            <DistributionPie
              title="Risk Distribution"
              data={stats?.risk_distribution ?? {}}
              colors={RISK_COLORS}
            />
          </div>
          <div className="card">
            <DistributionPie
              title="Caller Type"
              data={stats?.caller_type_distribution ?? {}}
              colors={CALLER_COLORS}
            />
          </div>
          <div className="card">
            <IntentBarChart data={stats?.intent_distribution ?? {}} />
          </div>
        </div>

        {/* Recent Calls + Notifications */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="card md:col-span-2">
            <h2 className="text-base font-semibold text-slate-800 mb-4 flex items-center gap-2">
              <Phone className="w-4 h-4 text-slate-400" />
              Recent Calls
            </h2>
            <RecentCallsTable calls={calls} />
          </div>

          <div className="space-y-6">
            <div className="card">
              <h2 className="text-base font-semibold text-slate-800 mb-4 flex items-center gap-2">
                <Bell className="w-4 h-4 text-slate-400" />
                Notifications
                {notifications.filter(n => !n.read).length > 0 && (
                  <span className="ml-auto text-xs bg-red-500 text-white px-1.5 py-0.5 rounded-full">
                    {notifications.filter(n => !n.read).length} new
                  </span>
                )}
              </h2>
              <NotificationsPanel notifications={notifications} />
            </div>

            <DemoSimulator onSimulate={loadData} />
          </div>
        </div>
      </main>
    </div>
  );
}
