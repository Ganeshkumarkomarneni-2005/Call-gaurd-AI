'use client';

import { useState } from 'react';
import { authApi, setToken } from '@/lib/api';
import { Shield, Mail, Lock, User, Eye, EyeOff, ArrowLeft, CheckCircle2, Zap, Radio, Activity } from 'lucide-react';
import { useRouter } from 'next/navigation';
import CyberShield3D from '@/components/CyberShield3D';
import CyberBackground from '@/components/CyberBackground';

type Mode = 'login' | 'register' | 'forgot';

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<Mode>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [showPass, setShowPass] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [devResetLink, setDevResetLink] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccessMsg(null);
    setDevResetLink(null);

    try {
      if (mode === 'login') {
        const res = await authApi.login(email, password);
        setToken(res.access_token);
        router.push('/');
      } else if (mode === 'register') {
        const res = await authApi.register(email, password, fullName);
        setToken(res.access_token);
        router.push('/');
      } else if (mode === 'forgot') {
        const res = await authApi.forgotPassword(email);
        setSuccessMsg(res.message || 'Password reset link sent to your email.');
        if (res.reset_link) {
          setDevResetLink(res.reset_link);
        }
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Operation failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative min-h-screen flex items-center justify-center p-4 md:p-8 overflow-hidden bg-[#030712] text-slate-100">
      <CyberBackground />

      <div className="relative w-full max-w-5xl grid grid-cols-1 lg:grid-cols-12 gap-8 items-center z-10">
        
        {/* Left 3D Visual Hero */}
        <div className="lg:col-span-6 flex flex-col items-center lg:items-start text-center lg:text-left space-y-6">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 text-xs font-semibold tracking-wider uppercase shadow-[0_0_15px_rgba(6,182,212,0.2)]">
            <Radio className="w-3.5 h-3.5 animate-pulse text-cyan-400" />
            Zero-Trust Inbound Telephony
          </div>

          <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight text-white leading-tight">
            Autonomous <br />
            <span className="bg-gradient-to-r from-cyan-400 via-blue-500 to-purple-500 bg-clip-text text-transparent drop-shadow-[0_0_25px_rgba(6,182,212,0.4)]">
              Voice Defense
            </span>
          </h1>

          <p className="text-slate-400 text-sm md:text-base max-w-md leading-relaxed">
            Multi-factor screening pipeline verifying caller identity, intent, and fraud risk in real-time before human intervention.
          </p>

          {/* Interactive 3D Shield Orb */}
          <div className="w-full flex justify-center lg:justify-start py-2">
            <CyberShield3D size={320} />
          </div>

          {/* Live Telemetry Tickers */}
          <div className="grid grid-cols-3 gap-3 w-full max-w-md pt-2">
            <div className="bg-slate-900/60 border border-white/10 rounded-xl p-3 backdrop-blur-md">
              <p className="text-[10px] text-slate-400 uppercase font-mono">Defense Core</p>
              <p className="text-sm font-bold text-cyan-400 flex items-center gap-1 mt-0.5">
                <Zap className="w-3.5 h-3.5 text-cyan-400" /> ACTIVE
              </p>
            </div>
            <div className="bg-slate-900/60 border border-white/10 rounded-xl p-3 backdrop-blur-md">
              <p className="text-[10px] text-slate-400 uppercase font-mono">Latency</p>
              <p className="text-sm font-bold text-emerald-400 flex items-center gap-1 mt-0.5">
                <Activity className="w-3.5 h-3.5 text-emerald-400" /> &lt;110ms
              </p>
            </div>
            <div className="bg-slate-900/60 border border-white/10 rounded-xl p-3 backdrop-blur-md">
              <p className="text-[10px] text-slate-400 uppercase font-mono">Protection</p>
              <p className="text-sm font-bold text-purple-400 mt-0.5">9-Agent ML</p>
            </div>
          </div>
        </div>

        {/* Right Floating Glassmorphic Authentication Vault */}
        <div className="lg:col-span-6 flex justify-center">
          <div className="w-full max-w-md bg-slate-900/70 border border-cyan-500/20 rounded-3xl p-8 backdrop-blur-2xl shadow-[0_0_50px_rgba(0,0,0,0.8),0_0_30px_rgba(6,182,212,0.15)] relative">
            
            {/* Top Logo */}
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2.5 bg-gradient-to-tr from-cyan-500 to-blue-600 rounded-xl shadow-[0_0_15px_rgba(6,182,212,0.5)]">
                <Shield className="w-6 h-6 text-white" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-white tracking-wide">CallGuard AI</h2>
                <p className="text-xs text-cyan-400/80 font-mono">Cognitive Defense Terminal</p>
              </div>
            </div>

            {/* Tabs */}
            {mode !== 'forgot' ? (
              <div className="flex mb-6 bg-slate-950/80 border border-white/10 rounded-xl p-1">
                <button
                  type="button"
                  className={`flex-1 py-2 text-xs font-semibold rounded-lg transition-all ${
                    mode === 'login'
                      ? 'bg-gradient-to-r from-cyan-500 to-blue-600 text-white shadow-[0_0_15px_rgba(6,182,212,0.4)]'
                      : 'text-slate-400 hover:text-white'
                  }`}
                  onClick={() => {
                    setMode('login');
                    setError(null);
                    setSuccessMsg(null);
                  }}
                >
                  Sign In
                </button>
                <button
                  type="button"
                  className={`flex-1 py-2 text-xs font-semibold rounded-lg transition-all ${
                    mode === 'register'
                      ? 'bg-gradient-to-r from-cyan-500 to-blue-600 text-white shadow-[0_0_15px_rgba(6,182,212,0.4)]'
                      : 'text-slate-400 hover:text-white'
                  }`}
                  onClick={() => {
                    setMode('register');
                    setError(null);
                    setSuccessMsg(null);
                  }}
                >
                  Create Account
                </button>
              </div>
            ) : (
              <div className="mb-6 flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => {
                    setMode('login');
                    setError(null);
                    setSuccessMsg(null);
                  }}
                  className="p-1.5 text-slate-400 hover:text-white rounded-lg bg-slate-800/60"
                >
                  <ArrowLeft className="w-4 h-4" />
                </button>
                <h3 className="text-sm font-semibold text-white">Reset Access Key</h3>
              </div>
            )}

            {/* Feedback Alerts */}
            {successMsg && (
              <div className="mb-4 bg-emerald-500/10 border border-emerald-500/30 rounded-xl p-3.5 text-xs text-emerald-300 space-y-2">
                <div className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                  <span>{successMsg}</span>
                </div>
                {devResetLink && (
                  <div className="pt-2 border-t border-emerald-500/20">
                    <p className="text-[11px] text-emerald-400 mb-1">Direct Reset Link:</p>
                    <a
                      href={devResetLink}
                      className="inline-block bg-emerald-600 text-white text-xs font-semibold px-3 py-1.5 rounded-lg hover:bg-emerald-500 transition-colors"
                    >
                      Set New Password →
                    </a>
                  </div>
                )}
              </div>
            )}

            {error && (
              <div className="mb-4 bg-rose-500/10 border border-rose-500/30 rounded-xl p-3 text-xs text-rose-300">
                {error}
              </div>
            )}

            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-4">
              {mode === 'register' && (
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1.5">Operator Name</label>
                  <div className="relative">
                    <User className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                    <input
                      type="text"
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      placeholder="Ganesh Kumar"
                      className="w-full pl-10 pr-4 py-2.5 bg-slate-950/70 border border-slate-700/80 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400 transition-all"
                    />
                  </div>
                </div>
              )}

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">Email Address</label>
                <div className="relative">
                  <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="operator@callguard.ai"
                    required
                    className="w-full pl-10 pr-4 py-2.5 bg-slate-950/70 border border-slate-700/80 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400 transition-all"
                  />
                </div>
              </div>

              {mode !== 'forgot' && (
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <label className="block text-xs font-medium text-slate-300">Password</label>
                    {mode === 'login' && (
                      <button
                        type="button"
                        onClick={() => {
                          setMode('forgot');
                          setError(null);
                          setSuccessMsg(null);
                        }}
                        className="text-[11px] text-cyan-400 hover:text-cyan-300"
                      >
                        Forgot password?
                      </button>
                    )}
                  </div>
                  <div className="relative">
                    <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                    <input
                      type={showPass ? 'text' : 'password'}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="••••••••••••"
                      required
                      className="w-full pl-10 pr-10 py-2.5 bg-slate-950/70 border border-slate-700/80 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400 transition-all"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPass(!showPass)}
                      className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300"
                    >
                      {showPass ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                className="btn-primary w-full py-3 mt-2 flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Authenticating…
                  </>
                ) : mode === 'login' ? (
                  'Authenticate & Enter Command Center'
                ) : mode === 'register' ? (
                  'Deploy Access & Create Account'
                ) : (
                  'Dispatch Reset Vector'
                )}
              </button>
            </form>

            <div className="mt-6 pt-5 border-t border-white/5 text-center">
              <p className="text-[11px] text-slate-500 font-mono">
                CALLER TYPE ≠ INTENT ≠ RISK ≠ ACTION
              </p>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
