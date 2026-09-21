'use client';

import { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import { useRouter } from 'next/navigation';
import { dashboardApi, callsApi, notificationsApi, getToken, clearToken, type DashboardStats, type Call, type Notification } from '@/lib/api';
import { formatRelativeTime, formatDuration } from '@/lib/utils';
import { Phone, Shield, AlertTriangle, Users, Bot, Megaphone, Briefcase, Bell, Activity, RefreshCw, LogOut } from 'lucide-react';
import Link from 'next/link';

// Dynamically import charts with SSR disabled to prevent hydration exceptions
const DashboardCharts = dynamic(() => import('@/components/DashboardCharts'), {
  ssr: false,
  loading: () => (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      <div className="card h-64 flex items-center justify-center text-slate-300 text-sm">Loading charts…</div>
      <div className="card h-64 flex items-center justify-center text-slate-300 text-sm">Loading charts…</div>
      <div className="card h-64 flex items-center justify-center text-slate-300 text-sm">Loading charts…</div>
    </div>
  ),
});

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

// ─── Recent Calls Table ───────────────────────────────────────────────────────

function RecentCallsTable({ calls }: { calls: Call[] }) {
  const callList = Array.isArray(calls) ? calls : [];
  if (callList.length === 0) {
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
          {callList.map((call) => (
            <tr key={call.id} className="border-b border-slate-50 hover:bg-slate-50 transition-colors">
              <td className="py-3 px-2">
                <div className="font-medium text-slate-800">
                  {call.caller_number || 'Unknown'}
                </div>
                <div className="text-xs text-slate-400">{call.telephony_provider}</div>
              </td>
              <td className="py-3 px-2">
                <span className={`badge ${
                  call.status?.toUpperCase() === 'ENDED' ? 'bg-slate-100 text-slate-600'
                  : call.status?.toUpperCase() === 'ACTIVE' ? 'bg-green-100 text-green-700'
                  : call.status?.toUpperCase() === 'TRANSFERRED' ? 'bg-blue-100 text-blue-700'
                  : call.status?.toUpperCase() === 'FAILED' ? 'bg-red-100 text-red-700'
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

  const notifList = Array.isArray(notifications) ? notifications : [];
  if (notifList.length === 0) {
    return (
      <div className="text-center py-8 text-slate-400">
        <Bell className="w-8 h-8 mx-auto mb-2 opacity-30" />
        <p className="text-sm">No notifications</p>
      </div>
    );
  }

  return (
    <ul className="space-y-2">
      {notifList.slice(0, 5).map((n) => (
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

function DemoSimulator({ onSimulate }: { onSimulate: () => void }) {
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  const simulate = async () => {
    setLoading(true);
    setMessage('');
    try {
      await callsApi.simulateIncoming('+911234567890');
      setMessage('✅ Call simulated successfully!');
      onSimulate();
    } catch (e) {
      setMessage(`❌ Failed: ${e instanceof Error ? e.message : 'Error'}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card bg-gradient-to-br from-slate-900 to-slate-800 text-white">
      <h3 className="text-sm font-semibold mb-2 flex items-center gap-2">
        <Activity className="w-4 h-4 text-blue-400" />
        Demo Call Simulator
      </h3>
      <p className="text-xs text-slate-400 mb-4">
        Inject a simulated incoming call to trigger real-time AI classification & analysis.
      </p>
      <button
        onClick={simulate}
        disabled={loading}
        className="btn-primary w-full py-2 text-xs"
      >
        {loading ? 'Creating call…' : '📞 Simulate Call'}
      </button>
      {message && <p className="mt-2 text-xs text-slate-300">{message}</p>}
    </div>
  );
}

// ─── Main Dashboard ───────────────────────────────────────────────────────────

export default function DashboardPage() {
  const router = useRouter();
  const [mounted, setMounted] = useState(false);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [calls, setCalls] = useState<Call[]>([]);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [statsData, callsData, notifData] = await Promise.allSettled([
        dashboardApi.stats(),
        dashboardApi.recentCalls(),
        notificationsApi.list(1, 10),
      ]);

      const authError = [statsData, callsData, notifData].find(
        (r) => r.status === 'rejected' && r.reason?.message === 'AUTH_REQUIRED'
      );
      if (authError) {
        clearToken();
        router.push('/login');
        return;
      }

      if (statsData.status === 'fulfilled') {
        setStats(statsData.value);
      }
      if (callsData.status === 'fulfilled') {
        const cVal = callsData.value as any;
        setCalls(Array.isArray(cVal) ? cVal : (cVal?.calls || []));
      }
      if (notifData.status === 'fulfilled') {
        const nVal = notifData.value as any;
        setNotifications(Array.isArray(nVal) ? nVal : (nVal?.notifications || []));
      }

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
    }
  };

  useEffect(() => {
    setMounted(true);
    if (!getToken()) {
      router.push('/login');
      return;
    }
    loadData();
    const interval = setInterval(loadData, 30_000);
    return () => clearInterval(interval);
  }, []);

  const handleLogout = () => {
    clearToken();
    router.push('/login');
  };

  if (!mounted) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-slate-500 text-sm">Loading CallGuard AI…</p>
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
            <div className="p-2 bg-blue-600 rounded-lg text-white">
              <Shield className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-900">CallGuard AI</h1>
              <p className="text-xs text-slate-400">Intelligent Call Screening Dashboard</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Link href="/calls" className="btn-secondary text-xs">
              All Calls
            </Link>
            {notifications.filter(n => !n.read).length > 0 && (
              <span className="flex items-center gap-1.5 text-sm text-slate-600">
                <Bell className="w-4 h-4 text-slate-500" />
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
            <button
              onClick={handleLogout}
              className="p-2 text-slate-400 hover:text-slate-600 transition-colors"
              title="Log out"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8 space-y-8">
        {/* Error Banner */}
        {error && (
          <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-medium text-amber-800">Connection Notice</p>
              <p className="text-sm text-amber-600 mt-1">{error}</p>
            </div>
          </div>
        )}

        {/* Core Principle Banner */}
        <div className="bg-gradient-to-r from-slate-900 via-blue-950 to-slate-900 text-white rounded-xl p-5 shadow-sm">
          <p className="text-xs font-semibold tracking-wider uppercase text-blue-400 mb-1">Core Intelligence Principle</p>
          <p className="text-lg font-bold">
            CALLER TYPE ≠ INTENT ≠ RISK ≠ ACTION
          </p>
          <p className="text-sm text-slate-300 mt-1">
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

        {/* Charts Row (Dynamically loaded on client) */}
        <DashboardCharts stats={stats} />

        {/* Recent Calls + Notifications */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="card md:col-span-2">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-semibold text-slate-800 flex items-center gap-2">
                <Phone className="w-4 h-4 text-slate-400" />
                Recent Calls
              </h2>
              <Link href="/calls" className="text-xs text-blue-600 hover:text-blue-800 font-medium">
                View all →
              </Link>
            </div>
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
