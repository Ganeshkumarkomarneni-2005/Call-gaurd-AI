'use client';

import { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import { useRouter } from 'next/navigation';
import { dashboardApi, callsApi, notificationsApi, getToken, clearToken, type DashboardStats, type Call, type Notification } from '@/lib/api';
import { formatRelativeTime, formatDuration } from '@/lib/utils';
import {
  Phone, Shield, AlertTriangle, Users, Bot, Megaphone, Briefcase,
  Bell, Activity, RefreshCw, LogOut, Radio, Zap, ChevronRight, Lock
} from 'lucide-react';
import Link from 'next/link';
import CyberShield3D from '@/components/CyberShield3D';
import CyberBackground from '@/components/CyberBackground';

// Dynamically import charts with SSR disabled
const DashboardCharts = dynamic(() => import('@/components/DashboardCharts'), {
  ssr: false,
  loading: () => (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      <div className="card-glow h-64 flex items-center justify-center text-slate-500 text-xs font-mono">LOADING TELEMETRY…</div>
      <div className="card-glow h-64 flex items-center justify-center text-slate-500 text-xs font-mono">LOADING ACOUSTICS…</div>
      <div className="card-glow h-64 flex items-center justify-center text-slate-500 text-xs font-mono">LOADING VECTORS…</div>
    </div>
  ),
});

// ─── 3D Glowing Stat Card ──────────────────────────────────────────────────────

function StatCard({
  label, value, icon: Icon, color = 'text-cyan-400', glowColor = 'shadow-[0_0_20px_rgba(6,182,212,0.15)]',
}: {
  label: string; value: number | string; icon: React.ElementType;
  color?: string; glowColor?: string;
}) {
  return (
    <div className={`card-3d bg-slate-900/60 border border-white/10 rounded-2xl p-5 backdrop-blur-xl ${glowColor} hover:border-cyan-500/40 transition-all`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-medium text-slate-400 tracking-wide uppercase">{label}</span>
        <div className="p-2 rounded-xl bg-white/5 border border-white/5">
          <Icon className={`w-4 h-4 ${color}`} />
        </div>
      </div>
      <p className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">{value}</p>
    </div>
  );
}

// ─── Recent Calls Table ───────────────────────────────────────────────────────

function RecentCallsTable({ calls }: { calls: Call[] }) {
  const callList = Array.isArray(calls) ? calls : [];
  if (callList.length === 0) {
    return (
      <div className="text-center py-12 text-slate-500">
        <Phone className="w-10 h-10 mx-auto mb-3 opacity-30 text-cyan-400" />
        <p className="text-sm">No incoming calls screened yet.</p>
        <p className="text-xs text-slate-600 mt-1">Dial your virtual number or run a simulation to begin.</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b border-white/10 text-slate-400">
            <th className="text-left py-3 px-3 font-semibold uppercase tracking-wider">Caller Target</th>
            <th className="text-left py-3 px-3 font-semibold uppercase tracking-wider">Defense State</th>
            <th className="text-left py-3 px-3 font-semibold uppercase tracking-wider">Duration</th>
            <th className="text-left py-3 px-3 font-semibold uppercase tracking-wider">Intercept Time</th>
            <th className="text-right py-3 px-3 font-semibold uppercase tracking-wider">Intelligence</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-white/5">
          {callList.map((call) => (
            <tr key={call.id} className="hover:bg-white/[0.03] transition-colors group">
              <td className="py-3.5 px-3">
                <div className="font-semibold text-white group-hover:text-cyan-400 transition-colors">
                  {call.caller_number || 'Anonymous Number'}
                </div>
                <div className="text-[11px] text-slate-500 font-mono">{call.telephony_provider.toUpperCase()}</div>
              </td>
              <td className="py-3.5 px-3">
                <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-bold tracking-wider uppercase ${
                  call.status?.toUpperCase() === 'ENDED' ? 'bg-slate-500/10 text-slate-300 border border-slate-500/20'
                  : call.status?.toUpperCase() === 'ACTIVE' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 animate-pulse'
                  : call.status?.toUpperCase() === 'TRANSFERRED' ? 'bg-cyan-500/10 text-cyan-300 border border-cyan-500/30'
                  : 'bg-amber-500/10 text-amber-300 border border-amber-500/30'
                }`}>
                  <span className={`w-1.5 h-1.5 rounded-full ${
                    call.status?.toUpperCase() === 'ACTIVE' ? 'bg-emerald-400 animate-ping' : 'bg-slate-400'
                  }`} />
                  {call.status}
                </span>
              </td>
              <td className="py-3.5 px-3 text-slate-300 font-mono">
                {formatDuration(call.duration_seconds)}
              </td>
              <td className="py-3.5 px-3 text-slate-400">
                {formatRelativeTime(call.created_at)}
              </td>
              <td className="py-3.5 px-3 text-right">
                <Link
                  href={`/calls/${call.id}`}
                  className="inline-flex items-center gap-1 text-cyan-400 hover:text-cyan-300 font-semibold text-xs py-1 px-2.5 rounded-lg bg-cyan-500/10 border border-cyan-500/20 hover:border-cyan-400/40 transition-all"
                >
                  View Details <ChevronRight className="w-3.5 h-3.5" />
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ─── Cyber Notifications Panel ────────────────────────────────────────────────

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
      <div className="text-center py-8 text-slate-500 text-xs">
        <Bell className="w-6 h-6 mx-auto mb-2 opacity-30 text-slate-400" />
        <p>No active security alerts</p>
      </div>
    );
  }

  return (
    <ul className="space-y-2.5 max-h-72 overflow-y-auto pr-1">
      {notifList.slice(0, 5).map((n) => (
        <li
          key={n.id}
          className={`flex gap-3 p-3 rounded-xl border text-xs transition-all ${
            n.read
              ? 'bg-slate-950/40 border-white/5 text-slate-400'
              : 'bg-cyan-950/30 border-cyan-500/30 text-slate-200 shadow-[0_0_15px_rgba(6,182,212,0.1)]'
          }`}
        >
          <span className="text-base">{typeIcon[n.notification_type] || '🔔'}</span>
          <div className="flex-1 min-w-0">
            <p className="font-semibold text-white truncate">{n.title}</p>
            <p className="text-slate-400 text-[11px] truncate mt-0.5">{n.body}</p>
            <p className="text-slate-500 text-[10px] mt-1 font-mono">{formatRelativeTime(n.created_at)}</p>
          </div>
        </li>
      ))}
    </ul>
  );
}

// ─── Demo Simulator ───────────────────────────────────────────────────────────

const SIMULATION_SCENARIOS = [
  { id: 'ai_recruiter', label: '🤖 AI Recruiter (ABC Tech - Data Analyst)', caller: '+919876543210' },
  { id: 'human_recruiter', label: '👤 Human Recruiter (Acme HR - Cloud Eng)', caller: '+919812345678' },
  { id: 'recruitment_fraud', label: '⚠️ Job Scam (Demand ₹5,000 Upfront)', caller: '+919100012345' },
  { id: 'otp_fraud', label: '🚨 Bank Scam (Threat & OTP Phishing)', caller: '+919000099999' },
  { id: 'promotional', label: '📣 Promotional Robocall (Loan Offer)', caller: '+919777788888' },
];

function DemoSimulator({ onSimulate }: { onSimulate: () => void }) {
  const [scenario, setScenario] = useState('ai_recruiter');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  const simulate = async () => {
    setLoading(true);
    setMessage('');
    try {
      const selected = SIMULATION_SCENARIOS.find(s => s.id === scenario);
      await callsApi.simulate(scenario, selected?.caller);
      setMessage('✅ 9-Agent AI Pipeline Executed!');
      onSimulate();
    } catch (e) {
      setMessage(`❌ Error: ${e instanceof Error ? e.message : 'Simulation failed'}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card-glow">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
          <Radio className="w-4 h-4 text-cyan-400 animate-pulse" />
          Attack Vector Simulation
        </h3>
        <span className="text-[10px] font-mono text-purple-400 bg-purple-500/10 px-2 py-0.5 rounded-full border border-purple-500/20">
          DEMO ENGINE
        </span>
      </div>

      <p className="text-xs text-slate-400 mb-3 leading-relaxed">
        Trigger synthetic calls to observe real-time multi-agent classification, threat extraction, and risk assessment.
      </p>

      <div className="mb-4">
        <label className="block text-[11px] font-mono text-slate-400 mb-1.5 uppercase">Select Call Scenario</label>
        <select
          value={scenario}
          onChange={(e) => setScenario(e.target.value)}
          className="w-full bg-slate-950 border border-slate-700/80 text-white text-xs rounded-xl px-3 py-2.5 focus:outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400 transition-all"
        >
          {SIMULATION_SCENARIOS.map((s) => (
            <option key={s.id} value={s.id} className="bg-slate-900 text-white">
              {s.label}
            </option>
          ))}
        </select>
      </div>

      <button
        onClick={simulate}
        disabled={loading}
        className="btn-primary w-full py-2.5 text-xs flex items-center justify-center gap-2"
      >
        {loading ? (
          <>
            <span className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
            Analyzing Audio Stream…
          </>
        ) : (
          '⚡ Trigger Scenario & Analyze'
        )}
      </button>
      {message && <p className="mt-2.5 text-xs text-cyan-300 font-medium text-center">{message}</p>}
    </div>
  );
}

// ─── Main Dashboard Page ──────────────────────────────────────────────────────

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
        setError(`API notice: ${msg}`);
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
    const interval = setInterval(loadData, 20_000);
    return () => clearInterval(interval);
  }, []);

  const handleLogout = () => {
    clearToken();
    router.push('/login');
  };

  if (!mounted) {
    return (
      <div className="min-h-screen bg-[#030712] flex items-center justify-center">
        <div className="text-center">
          <div className="w-10 h-10 border-4 border-cyan-500 border-t-transparent rounded-full animate-spin mx-auto mb-4 shadow-[0_0_20px_rgba(6,182,212,0.5)]" />
          <p className="text-cyan-400 text-xs font-mono tracking-widest uppercase">Initializing 3D Defense Core…</p>
        </div>
      </div>
    );
  }

  return (
    <div className="relative min-h-screen bg-[#030712] text-slate-100 selection:bg-cyan-500/30">
      <CyberBackground />

      {/* Cyberpunk Top Bar */}
      <header className="sticky top-0 z-40 bg-slate-950/70 border-b border-white/10 backdrop-blur-2xl px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-gradient-to-tr from-cyan-500 to-blue-600 rounded-xl shadow-[0_0_20px_rgba(6,182,212,0.5)]">
              <Shield className="w-6 h-6 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-lg font-bold text-white tracking-wide">CallGuard AI</h1>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
                  v2.0 3D DEFENSE
                </span>
              </div>
              <p className="text-xs text-slate-400 font-mono">Autonomous Inbound Telephony Command Center</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Link href="/calls" className="btn-secondary text-xs flex items-center gap-1.5">
              <Phone className="w-3.5 h-3.5 text-cyan-400" />
              All Screened Calls
            </Link>

            {notifications.filter(n => !n.read).length > 0 && (
              <span className="flex items-center gap-1 text-xs text-rose-400 bg-rose-500/10 border border-rose-500/30 px-2.5 py-1 rounded-full">
                <Bell className="w-3.5 h-3.5 animate-bounce" />
                <span>{notifications.filter(n => !n.read).length} Alerts</span>
              </span>
            )}

            <button
              onClick={loadData}
              className="btn-secondary flex items-center gap-2 text-xs"
            >
              <RefreshCw className={`w-3.5 h-3.5 text-cyan-400 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </button>

            <button
              onClick={handleLogout}
              className="p-2 text-slate-400 hover:text-rose-400 transition-colors bg-white/5 hover:bg-rose-500/10 rounded-xl border border-white/5"
              title="Log out"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8 space-y-8 relative z-10">
        
        {/* 3D Cyber Shield Hero Banner */}
        <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-slate-950 via-slate-900 to-slate-950 border border-cyan-500/30 p-8 shadow-[0_0_50px_rgba(6,182,212,0.15)]">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-center">
            
            <div className="lg:col-span-8 space-y-4">
              <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 text-xs font-semibold uppercase tracking-wider font-mono shadow-[0_0_15px_rgba(6,182,212,0.2)]">
                <Radio className="w-3.5 h-3.5 animate-pulse text-cyan-400" />
                Active Protection Perimeter · 04045902896
              </div>

              <div>
                <h2 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight leading-snug">
                  Autonomous Cognitive Call Screening &amp; <br />
                  <span className="bg-gradient-to-r from-cyan-400 via-blue-500 to-purple-400 bg-clip-text text-transparent">
                    Real-Time Threat Intelligence
                  </span>
                </h2>
                <p className="text-slate-300 text-xs md:text-sm mt-2 max-w-2xl leading-relaxed">
                  CallGuard AI is a zero-trust inbound telephony defense platform. It autonomously intercepts calls in real time, converts live speech to text, verifies caller legitimacy, extracts interview schedules, and neutralizes financial scams before your phone even rings.
                </p>
              </div>

              {/* 4-Pillar AI Defense Architecture Grid */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2.5 pt-2">
                <div className="bg-slate-950/60 border border-white/10 rounded-xl p-2.5 backdrop-blur-md">
                  <p className="text-[10px] text-cyan-400 font-mono font-bold">01 / ACOUSTICS</p>
                  <p className="text-xs font-semibold text-white mt-0.5">Voice Profiling</p>
                  <p className="text-[11px] text-slate-400 mt-0.5 leading-tight">Human vs AI vs Robocall</p>
                </div>

                <div className="bg-slate-950/60 border border-white/10 rounded-xl p-2.5 backdrop-blur-md">
                  <p className="text-[10px] text-blue-400 font-mono font-bold">02 / NLU ENGINE</p>
                  <p className="text-xs font-semibold text-white mt-0.5">Intent Detection</p>
                  <p className="text-[11px] text-slate-400 mt-0.5 leading-tight">Recruitment vs Phishing</p>
                </div>

                <div className="bg-slate-950/60 border border-white/10 rounded-xl p-2.5 backdrop-blur-md">
                  <p className="text-[10px] text-purple-400 font-mono font-bold">03 / RISK ENGINE</p>
                  <p className="text-xs font-semibold text-white mt-0.5">Threat Matrix</p>
                  <p className="text-[11px] text-slate-400 mt-0.5 leading-tight">OTP / Upfront Fee Extortion</p>
                </div>

                <div className="bg-slate-950/60 border border-white/10 rounded-xl p-2.5 backdrop-blur-md">
                  <p className="text-[10px] text-emerald-400 font-mono font-bold">04 / ARBITRATION</p>
                  <p className="text-xs font-semibold text-white mt-0.5">Smart Action</p>
                  <p className="text-[11px] text-slate-400 mt-0.5 leading-tight">Screen, Transfer, or Deflect</p>
                </div>
              </div>
            </div>


            {/* 3D Interactive Shield Visual */}
            <div className="lg:col-span-4 flex justify-center">
              <CyberShield3D size={260} />
            </div>

          </div>
        </div>

        {/* 3D Telemetry Stat Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard label="Total Intercepts" value={stats?.total_calls ?? 0} icon={Phone} color="text-cyan-400" />
          <StatCard label="Today's Calls" value={stats?.today_calls ?? 0} icon={Activity} color="text-emerald-400" />
          <StatCard label="Threats Deflected" value={stats?.fraud_calls ?? 0} icon={AlertTriangle} color="text-rose-400" glowColor="shadow-[0_0_20px_rgba(244,63,94,0.15)]" />
          <StatCard label="Recruitment Leads" value={stats?.recruitment_calls ?? 0} icon={Briefcase} color="text-purple-400" />
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard label="AI Voice Assistants" value={stats?.ai_callers ?? 0} icon={Bot} color="text-cyan-300" />
          <StatCard label="Human Callers" value={stats?.human_callers ?? 0} icon={Users} color="text-indigo-400" />
          <StatCard label="Human Handoffs" value={stats?.transferred_calls ?? 0} icon={Phone} color="text-amber-400" />
          <StatCard label="Promotional / Robocalls" value={stats?.promotional_calls ?? 0} icon={Megaphone} color="text-orange-400" />
        </div>

        {/* 3D Holographic Telemetry Charts */}
        <DashboardCharts stats={stats} />

        {/* Recent Calls & Notifications Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          
          {/* Recent Calls Table (Span 8) */}
          <div className="lg:col-span-8 card-glow">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <Phone className="w-4 h-4 text-cyan-400" />
                Live Inbound Call Stream
              </h2>
              <Link href="/calls" className="text-xs text-cyan-400 hover:text-cyan-300 font-semibold flex items-center gap-1">
                View All Archives →
              </Link>
            </div>
            <RecentCallsTable calls={calls} />
          </div>

          {/* Right Column: Alerts & Demo Simulator (Span 4) */}
          <div className="lg:col-span-4 space-y-6">
            
            {/* Notifications Card */}
            <div className="card-glow">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                  <Bell className="w-4 h-4 text-rose-400" />
                  Security Telemetry Alerts
                </h3>
                {notifications.filter(n => !n.read).length > 0 && (
                  <span className="text-[10px] font-bold bg-rose-500 text-white px-2 py-0.5 rounded-full">
                    {notifications.filter(n => !n.read).length} NEW
                  </span>
                )}
              </div>
              <NotificationsPanel notifications={notifications} />
            </div>

            {/* Attack Vector Demo Simulator */}
            <DemoSimulator onSimulate={loadData} />

          </div>

        </div>

      </main>
    </div>
  );
}
