'use client';

import { useEffect, useState } from 'react';
import { callsApi, type Call, type CallListResponse } from '@/lib/api';
import { formatRelativeTime, formatDuration } from '@/lib/utils';
import { Phone, ArrowLeft, ChevronLeft, ChevronRight, Shield, ChevronRight as ArrowRight } from 'lucide-react';
import Link from 'next/link';
import CyberBackground from '@/components/CyberBackground';

export default function CallsListPage() {
  const [data, setData] = useState<CallListResponse | null>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadPage = async (p: number) => {
    setLoading(true);
    setError(null);
    try {
      const result = await callsApi.list(p, 20);
      setData(result);
      setPage(p);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load calls');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadPage(1); }, []);

  const totalPages = data ? Math.ceil(data.total / 20) : 1;

  return (
    <div className="relative min-h-screen bg-[#030712] text-slate-100">
      <CyberBackground />

      <header className="sticky top-0 z-40 bg-slate-950/70 border-b border-white/10 backdrop-blur-2xl px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link
              href="/"
              className="p-2 rounded-xl bg-white/5 hover:bg-cyan-500/10 border border-white/5 hover:border-cyan-500/30 text-slate-400 hover:text-cyan-300 transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
            </Link>
            <div>
              <h1 className="text-lg font-bold text-white tracking-wide">All Screened Calls</h1>
              {data && <p className="text-xs text-cyan-400/80 font-mono">{data.total} Total Intercepted Records</p>}
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8 relative z-10">
        {error && (
          <div className="card border-rose-500/30 bg-rose-500/10 text-rose-300 mb-6 text-xs">
            <p>{error}</p>
          </div>
        )}

        <div className="card-glow">
          {loading && !data ? (
            <div className="flex items-center justify-center py-16">
              <div className="w-8 h-8 border-4 border-cyan-500 border-t-transparent rounded-full animate-spin shadow-[0_0_20px_rgba(6,182,212,0.5)]" />
            </div>
          ) : (
            <>
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-white/10 text-slate-400">
                    <th className="text-left py-3.5 px-3 font-semibold uppercase tracking-wider">Caller</th>
                    <th className="text-left py-3.5 px-3 font-semibold uppercase tracking-wider">Status</th>
                    <th className="text-left py-3.5 px-3 font-semibold uppercase tracking-wider">Provider</th>
                    <th className="text-left py-3.5 px-3 font-semibold uppercase tracking-wider">Duration</th>
                    <th className="text-left py-3.5 px-3 font-semibold uppercase tracking-wider">Time</th>
                    <th className="text-right py-3.5 px-3 font-semibold uppercase tracking-wider">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {data?.calls.map((call) => (
                    <tr key={call.id} className="hover:bg-white/[0.03] transition-colors group">
                      <td className="py-3.5 px-3">
                        <div className="font-semibold text-white group-hover:text-cyan-400 transition-colors">
                          {call.caller_number || 'Unknown'}
                        </div>
                        <div className="text-[11px] text-slate-500 font-mono">{call.id.substring(0, 8)}…</div>
                      </td>
                      <td className="py-3.5 px-3">
                        <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[10px] font-bold tracking-wider uppercase ${
                          call.status === 'ENDED' ? 'bg-slate-500/10 text-slate-300 border border-slate-500/20'
                          : call.status === 'ACTIVE' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 animate-pulse'
                          : call.status === 'TRANSFERRED' ? 'bg-cyan-500/10 text-cyan-300 border border-cyan-500/30'
                          : 'bg-amber-500/10 text-amber-300 border border-amber-500/30'
                        }`}>{call.status}</span>
                      </td>
                      <td className="py-3.5 px-3 text-slate-400 font-mono">{call.telephony_provider.toUpperCase()}</td>
                      <td className="py-3.5 px-3 text-slate-300 font-mono">{formatDuration(call.duration_seconds)}</td>
                      <td className="py-3.5 px-3 text-slate-400">{formatRelativeTime(call.created_at)}</td>
                      <td className="py-3.5 px-3 text-right">
                        <Link
                          href={`/calls/${call.id}`}
                          className="inline-flex items-center gap-1 text-cyan-400 hover:text-cyan-300 font-semibold text-xs py-1 px-3 rounded-lg bg-cyan-500/10 border border-cyan-500/20 hover:border-cyan-400/40 transition-all"
                        >
                          View Details <ArrowRight className="w-3.5 h-3.5" />
                        </Link>
                      </td>
                    </tr>
                  ))}
                  {(!data?.calls || data.calls.length === 0) && (
                    <tr>
                      <td colSpan={6} className="py-16 text-center text-slate-500">
                        <Phone className="w-10 h-10 mx-auto mb-2 opacity-30 text-cyan-400" />
                        <p>No call archives found</p>
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>

              {totalPages > 1 && (
                <div className="flex items-center justify-between mt-6 pt-4 border-t border-white/10">
                  <button
                    onClick={() => loadPage(page - 1)}
                    disabled={page === 1 || loading}
                    className="btn-secondary flex items-center gap-1 text-xs"
                  >
                    <ChevronLeft className="w-4 h-4" /> Prev
                  </button>
                  <span className="text-xs text-slate-400 font-mono">
                    PAGE {page} OF {totalPages}
                  </span>
                  <button
                    onClick={() => loadPage(page + 1)}
                    disabled={page === totalPages || loading}
                    className="btn-secondary flex items-center gap-1 text-xs"
                  >
                    Next <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      </main>
    </div>
  );
}
