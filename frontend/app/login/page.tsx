'use client';

import { useState } from 'react';
import { authApi, setToken } from '@/lib/api';
import { Shield, Mail, Lock, User, Eye, EyeOff, KeyRound, ArrowLeft, CheckCircle2 } from 'lucide-react';
import { useRouter } from 'next/navigation';

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
    <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md p-8">
        {/* Logo */}
        <div className="flex items-center gap-3 mb-8">
          <div className="p-2.5 bg-blue-600 rounded-xl">
            <Shield className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-900">CallGuard AI</h1>
            <p className="text-xs text-slate-400">Intelligent Call Screening</p>
          </div>
        </div>

        {/* Tabs (shown only for login and register) */}
        {mode !== 'forgot' ? (
          <div className="flex mb-6 bg-slate-100 rounded-lg p-1">
            <button
              className={`flex-1 py-2 text-sm font-medium rounded-md transition-colors ${
                mode === 'login' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-700'
              }`}
              onClick={() => {
                setMode('login');
                setError(null);
                setSuccessMsg(null);
              }}
            >
              Login
            </button>
            <button
              className={`flex-1 py-2 text-sm font-medium rounded-md transition-colors ${
                mode === 'register' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-700'
              }`}
              onClick={() => {
                setMode('register');
                setError(null);
                setSuccessMsg(null);
              }}
            >
              Register
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
              className="p-1 text-slate-400 hover:text-slate-600 rounded"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <h2 className="text-base font-semibold text-slate-800">Reset Password</h2>
          </div>
        )}

        {successMsg && (
          <div className="mb-4 bg-emerald-50 border border-emerald-200 rounded-lg p-3.5 text-sm text-emerald-800 space-y-2">
            <div className="flex items-start gap-2">
              <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
              <span>{successMsg}</span>
            </div>
            {devResetLink && (
              <div className="pt-2 border-t border-emerald-200">
                <p className="text-xs text-emerald-700 font-medium mb-1.5">Direct Reset Link (Local Dev):</p>
                <a
                  href={devResetLink}
                  className="inline-block bg-emerald-600 text-white text-xs font-semibold px-3 py-1.5 rounded hover:bg-emerald-700 transition-colors"
                >
                  Click Here to Set New Password →
                </a>
              </div>
            )}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {mode === 'register' && (
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Full Name</label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Jane Doe"
                  className="w-full pl-10 pr-4 py-2.5 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Email</label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="user@example.com"
                required
                className="w-full pl-10 pr-4 py-2.5 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>

          {mode !== 'forgot' && (
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="block text-sm font-medium text-slate-700">Password</label>
                {mode === 'login' && (
                  <button
                    type="button"
                    onClick={() => {
                      setMode('forgot');
                      setError(null);
                      setSuccessMsg(null);
                    }}
                    className="text-xs text-blue-600 hover:text-blue-800 hover:underline"
                  >
                    Forgot password?
                  </button>
                )}
              </div>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                  type={showPass ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  className="w-full pl-10 pr-10 py-2.5 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                <button
                  type="button"
                  onClick={() => setShowPass(!showPass)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                >
                  {showPass ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">
              {error}
            </div>
          )}

          <button type="submit" disabled={loading} className="btn-primary w-full py-3">
            {loading
              ? 'Please wait…'
              : mode === 'login'
              ? 'Sign In'
              : mode === 'register'
              ? 'Create Account'
              : 'Send Reset Link'}
          </button>
        </form>

        {mode === 'forgot' && (
          <div className="mt-4 text-center">
            <button
              type="button"
              onClick={() => {
                setMode('login');
                setError(null);
                setSuccessMsg(null);
              }}
              className="text-xs text-slate-500 hover:text-slate-800"
            >
              Remembered your password? <span className="text-blue-600 font-medium">Sign in</span>
            </button>
          </div>
        )}

        <div className="mt-6 pt-6 border-t border-slate-100">
          <p className="text-xs text-slate-400 text-center">
            Core principle:{' '}
            <span className="font-medium text-slate-600">
              CALLER TYPE ≠ INTENT ≠ RISK ≠ ACTION
            </span>
          </p>
        </div>
      </div>
    </div>
  );
}

