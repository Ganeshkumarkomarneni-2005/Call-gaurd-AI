'use client';

import { useEffect, useState } from 'react';
import { callsApi, type CallDetail } from '@/lib/api';
import {
  formatDateTime, formatRelativeTime, formatDuration, formatConfidence,
  riskBadgeClass, callerTypeBadgeClass, intentLabel, decisionLabel,
  type RiskLevel, type CallerType,
} from '@/lib/utils';
import { ArrowLeft, Phone, Shield, AlertTriangle, Briefcase, MessageSquare, Clock } from 'lucide-react';
import Link from 'next/link';

interface PageProps {
  params: { callId: string };
}

export default function CallDetailPage({ params }: PageProps) {
  const [detail, setDetail] = useState<CallDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    callsApi.get(params.callId)
      .then(setDetail)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [params.callId]);

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
    </div>
  );

  if (error) return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="card text-center max-w-md">
        <AlertTriangle className="w-12 h-12 text-red-400 mx-auto mb-3" />
        <h2 className="text-lg font-semibold text-slate-800 mb-2">Call Not Found</h2>
        <p className="text-slate-500 text-sm">{error}</p>
        <Link href="/" className="btn-primary mt-4 inline-block">← Back to Dashboard</Link>
      </div>
    </div>
  );

  if (!detail) return null;

  const { call, transcript, analysis, recruitment_details } = detail;

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 px-6 py-4">
        <div className="max-w-5xl mx-auto flex items-center gap-4">
          <Link href="/" className="text-slate-400 hover:text-slate-600 transition-colors">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-lg font-bold text-slate-900">Call Details</h1>
            <p className="text-xs text-slate-400 font-mono">{call.id}</p>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-8 space-y-6">
        {/* Call Overview */}
        <div className="card">
          <div className="flex items-start justify-between mb-6">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Phone className="w-5 h-5 text-slate-400" />
                <h2 className="text-xl font-bold text-slate-900">
                  {call.caller_number || 'Unknown Number'}
                </h2>
                {analysis && (
                  <span className={callerTypeBadgeClass(analysis.caller_type as CallerType)}>
                    {analysis.caller_type}
                  </span>
                )}
              </div>
              <div className="flex flex-wrap gap-3 text-sm text-slate-500">
                <span className="flex items-center gap-1">
                  <Clock className="w-3.5 h-3.5" />
                  {formatDateTime(call.started_at)}
                </span>
                <span>Duration: {formatDuration(call.duration_seconds)}</span>
                <span>Provider: {call.telephony_provider}</span>
              </div>
            </div>
            <div className="flex flex-col items-end gap-2">
              <span className={`badge text-sm px-3 py-1 ${
                call.status === 'ENDED' ? 'bg-slate-100 text-slate-600'
                : call.status === 'ACTIVE' ? 'bg-green-100 text-green-700'
                : call.status === 'TRANSFERRED' ? 'bg-blue-100 text-blue-700'
                : 'bg-amber-100 text-amber-700'
              }`}>{call.status}</span>
              {analysis && (
                <span className={riskBadgeClass(analysis.risk_level as RiskLevel)}>
                  {analysis.risk_level} RISK
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Analysis Grid */}
        {analysis && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Classification */}
            <div className="card">
              <h3 className="font-semibold text-slate-700 mb-4 flex items-center gap-2">
                <Shield className="w-4 h-4" /> Classification
              </h3>
              <dl className="space-y-3">
                <div className="flex justify-between">
                  <dt className="text-sm text-slate-500">Caller Type</dt>
                  <dd className="flex items-center gap-2">
                    <span className={callerTypeBadgeClass(analysis.caller_type as CallerType)}>
                      {analysis.caller_type}
                    </span>
                    <span className="text-xs text-slate-400">
                      {formatConfidence(analysis.caller_type_confidence)}
                    </span>
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-sm text-slate-500">Intent</dt>
                  <dd className="text-sm font-medium text-slate-800">
                    {intentLabel(analysis.intent)}
                    <span className="text-xs text-slate-400 ml-2">
                      {formatConfidence(analysis.intent_confidence)}
                    </span>
                  </dd>
                </div>
                {analysis.secondary_intent && (
                  <div className="flex justify-between">
                    <dt className="text-sm text-slate-500">Secondary Intent</dt>
                    <dd className="text-sm text-slate-700">{intentLabel(analysis.secondary_intent)}</dd>
                  </div>
                )}
                <div className="flex justify-between items-start">
                  <dt className="text-sm text-slate-500">Risk Level</dt>
                  <dd className="flex flex-col items-end gap-1">
                    <span className={riskBadgeClass(analysis.risk_level as RiskLevel)}>
                      {analysis.risk_level}
                    </span>
                    <span className="text-xs text-slate-400">
                      {formatConfidence(analysis.risk_confidence)} confidence
                    </span>
                  </dd>
                </div>
              </dl>

              {/* Risk Indicators */}
              {analysis.risk_indicators.length > 0 && (
                <div className="mt-4 pt-4 border-t border-slate-100">
                  <p className="text-xs font-semibold text-slate-500 mb-2 uppercase tracking-wide">
                    Risk Indicators
                  </p>
                  <ul className="space-y-1">
                    {analysis.risk_indicators.map((indicator, i) => (
                      <li key={i} className="flex items-center gap-2 text-sm text-red-700">
                        <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0 text-red-400" />
                        {indicator}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            {/* Decision */}
            <div className="card">
              <h3 className="font-semibold text-slate-700 mb-4">Decision</h3>
              <div className="text-center py-4">
                <p className="text-2xl mb-2">{decisionLabel(analysis.decision)}</p>
                <p className="text-xs text-slate-400 mb-4">
                  {formatConfidence(analysis.decision_confidence)} confidence
                </p>
              </div>
              <div className="bg-slate-50 rounded-lg p-3 text-sm text-slate-600">
                <p className="font-medium text-slate-700 mb-1">Reason</p>
                <p>{analysis.decision_reason || '—'}</p>
              </div>
              {analysis.analysis_latency_ms && (
                <p className="text-xs text-slate-400 mt-3 text-right">
                  Pipeline latency: {analysis.analysis_latency_ms}ms
                </p>
              )}
            </div>
          </div>
        )}

        {/* Recruitment Details */}
        {recruitment_details && (
          <div className="card">
            <h3 className="font-semibold text-slate-700 mb-4 flex items-center gap-2">
              <Briefcase className="w-4 h-4" /> Recruitment Details
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              {[
                { label: 'Company', value: recruitment_details.company },
                { label: 'Position', value: recruitment_details.position },
                { label: 'Recruiter', value: recruitment_details.recruiter_name },
                { label: 'Interview Stage', value: recruitment_details.interview_stage },
                { label: 'Interview Date', value: recruitment_details.interview_date },
                { label: 'Interview Time', value: recruitment_details.interview_time },
                { label: 'Next Step', value: recruitment_details.next_step },
              ].map(({ label, value }) => value ? (
                <div key={label}>
                  <p className="text-xs text-slate-400 uppercase tracking-wide">{label}</p>
                  <p className="font-medium text-slate-800 mt-0.5">{value}</p>
                </div>
              ) : null)}
            </div>
            {recruitment_details.is_legitimate !== null && (
              <div className={`mt-4 p-3 rounded-lg text-sm ${
                recruitment_details.is_legitimate
                  ? 'bg-green-50 text-green-800'
                  : 'bg-red-50 text-red-800'
              }`}>
                <strong>{recruitment_details.is_legitimate ? '✅ Legitimate' : '❌ Suspicious'}</strong>
                {recruitment_details.legitimacy_reason && (
                  <span className="ml-2">{recruitment_details.legitimacy_reason}</span>
                )}
              </div>
            )}
          </div>
        )}

        {/* Transcript */}
        {transcript && (
          <div className="card">
            <h3 className="font-semibold text-slate-700 mb-4 flex items-center gap-2">
              <MessageSquare className="w-4 h-4" /> Transcript
              <span className="ml-auto text-xs text-slate-400">{transcript.word_count} words</span>
            </h3>

            {transcript.summary && (
              <div className="bg-blue-50 rounded-lg p-4 mb-4">
                <p className="text-xs font-semibold text-blue-700 mb-1 uppercase tracking-wide">Summary</p>
                <p className="text-sm text-blue-900">{transcript.summary}</p>
              </div>
            )}

            <div className="space-y-3">
              {transcript.segments.map((seg) => (
                <div
                  key={seg.id}
                  className={`flex gap-3 ${seg.speaker === 'AGENT' ? 'flex-row-reverse' : ''}`}
                >
                  <div className={`w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center text-xs font-bold ${
                    seg.speaker === 'CALLER'
                      ? 'bg-slate-200 text-slate-600'
                      : 'bg-blue-600 text-white'
                  }`}>
                    {seg.speaker === 'CALLER' ? '👤' : '🤖'}
                  </div>
                  <div className={`max-w-[75%] rounded-xl px-4 py-2 text-sm ${
                    seg.speaker === 'CALLER'
                      ? 'bg-slate-100 text-slate-800'
                      : 'bg-blue-600 text-white'
                  }`}>
                    <p>{seg.text}</p>
                    {seg.confidence && (
                      <p className={`text-xs mt-1 opacity-60`}>
                        {formatConfidence(seg.confidence)} confidence
                      </p>
                    )}
                  </div>
                </div>
              ))}

              {transcript.segments.length === 0 && (
                <p className="text-slate-400 text-sm text-center py-4">
                  No transcript segments yet.
                </p>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
