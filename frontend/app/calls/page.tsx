'use client';

import { useEffect, useState } from 'react';
import { callsApi, type Call, type CallListResponse } from '@/lib/api';
import { formatRelativeTime, formatDuration, riskBadgeClass, callerTypeBadgeClass, type RiskLevel, type CallerType } from '@/lib/utils';
import { Phone, ArrowLeft, ChevronLeft, ChevronRight, Search } from 'lucide-react';
import Link from 'next/link';

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
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200 px-6 py-4">
        <div className="max-w-5xl mx-auto flex items-center gap-4">
          <Link href="/" className="text-slate-400 hover:text-slate-600 transition-colors">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-lg font-bold text-slate-900">All Calls</h1>
            {data && <p className="text-xs text-slate-400">{data.total} total calls</p>}
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-8">
        {error && (
          <div className="card border-red-200 bg-red-50 text-red-700 mb-6">
            <p>{error}</p>
          </div>
        )}

        <div className="card">
          {loading && !data ? (
            <div className="flex items-center justify-center py-12">
              <div className="w-6 h-6 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : (
            <>
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-100">
                    <th className="text-left py-3 px-3 text-slate-500 font-medium">Caller</th>
                    <th className="text-left py-3 px-3 text-slate-500 font-medium">Status</th>
                    <th className="text-left py-3 px-3 text-slate-500 font-medium">Provider</th>
                    <th className="text-left py-3 px-3 text-slate-500 font-medium">Duration</th>
                    <th className="text-left py-3 px-3 text-slate-500 font-medium">Time</th>
                    <th className="text-left py-3 px-3 text-slate-500 font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {data?.calls.map((call) => (
                    <tr key={call.id} className="border-b border-slate-50 hover:bg-slate-50 transition-colors">
                      <td className="py-3 px-3">
                        <div className="font-medium text-slate-800">{call.caller_number || '—'}</div>
                        <div className="text-xs text-slate-400 font-mono">{call.id.substring(0, 8)}…</div>
                      </td>
                      <td className="py-3 px-3">
                        <span className={`badge ${
                          call.status === 'ENDED' ? 'bg-slate-100 text-slate-600'
                          : call.status === 'ACTIVE' ? 'bg-green-100 text-green-700'
                          : call.status === 'TRANSFERRED' ? 'bg-blue-100 text-blue-700'
                          : 'bg-amber-100 text-amber-700'
                        }`}>{call.status}</span>
                      </td>
                      <td className="py-3 px-3 text-slate-500 text-xs">{call.telephony_provider}</td>
                      <td className="py-3 px-3 text-slate-600">{formatDuration(call.duration_seconds)}</td>
                      <td className="py-3 px-3 text-slate-400 text-xs">{formatRelativeTime(call.created_at)}</td>
                      <td className="py-3 px-3">
                        <Link href={`/calls/${call.id}`} className="text-blue-600 hover:text-blue-800 text-xs font-medium">
                          View →
                        </Link>
                      </td>
                    </tr>
                  ))}
                  {(!data?.calls || data.calls.length === 0) && (
                    <tr>
                      <td colSpan={6} className="py-12 text-center text-slate-400">
                        <Phone className="w-8 h-8 mx-auto mb-2 opacity-30" />
                        <p>No calls yet</p>
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>

              {totalPages > 1 && (
                <div className="flex items-center justify-between mt-4 pt-4 border-t border-slate-100">
                  <button
                    onClick={() => loadPage(page - 1)}
                    disabled={page === 1 || loading}
                    className="btn-secondary flex items-center gap-1"
                  >
                    <ChevronLeft className="w-4 h-4" /> Prev
                  </button>
                  <span className="text-sm text-slate-500">
                    Page {page} of {totalPages}
                  </span>
                  <button
                    onClick={() => loadPage(page + 1)}
                    disabled={page === totalPages || loading}
                    className="btn-secondary flex items-center gap-1"
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
