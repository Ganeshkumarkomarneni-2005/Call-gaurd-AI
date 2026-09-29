'use client';

import { useEffect, useState } from 'react';
import { callsApi, type CallDetail } from '@/lib/api';
import {
  formatDateTime, formatDuration, formatConfidence,
  riskBadgeClass, callerTypeBadgeClass, intentLabel, decisionLabel,
  type RiskLevel, type CallerType,
} from '@/lib/utils';
import { ArrowLeft, Phone, Shield, AlertTriangle, Briefcase, MessageSquare, Clock, Zap, Bot, User, CheckCircle2 } from 'lucide-react';
import Link from 'next/link';
import CyberBackground from '@/components/CyberBackground';

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
    <div className="min-h-screen bg-[#030712] flex items-center justify-center">
      <div className="text-center">
        <div className="w-10 h-10 border-4 border-cyan-500 border-t-transparent rounded-full animate-spin mx-auto mb-4 shadow-[0_0_20px_rgba(6,182,212,0.5)]" />
        <p className="text-cyan-400 text-xs font-mono tracking-widest uppercase">Decryption & Analysis in Progress…</p>
      </div>
    </div>
  );

  if (error) return (
    <div className="min-h-screen bg-[#030712] flex items-center justify-center p-4">
      <div className="card-glow text-center max-w-md">
        <AlertTriangle className="w-12 h-12 text-rose-400 mx-auto mb-3" />
        <h2 className="text-lg font-bold text-white mb-2">Call Record Unavailable</h2>
        <p className="text-slate-400 text-xs mb-4">{error}</p>
        <Link href="/" className="btn-primary inline-flex items-center gap-2 text-xs">
          ← Return to Command Center
        </Link>
      </div>
    </div>
  );

  if (!detail) return null;

  const { call, transcript, analysis, recruitment_details } = detail;

  return (
    <div className="relative min-h-screen bg-[#030712] text-slate-100 selection:bg-cyan-500/30">
      <CyberBackground />

      {/* Cyberpunk Top Bar */}
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
              <div className="flex items-center gap-2">
                <h1 className="text-lg font-bold text-white tracking-wide">Screened Call Intelligence</h1>
                <span className="text-[10px] font-mono text-cyan-400 bg-cyan-500/10 border border-cyan-500/20 px-2 py-0.5 rounded-full">
                  TELEMETRY REPORT
                </span>
              </div>
              <p className="text-xs text-slate-400 font-mono">{call.id}</p>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8 space-y-6 relative z-10">
        
        {/* Call Overview Header Card */}
        <div className="card-glow">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-3 mb-2">
                <div className="p-2.5 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400">
                  <Phone className="w-6 h-6" />
                </div>
                <div>
                  <h2 className="text-2xl font-extrabold text-white tracking-tight">
                    {call.caller_number || 'Unknown Number'}
                  </h2>
                  <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400 mt-1 font-mono">
                    <span className="flex items-center gap-1">
                      <Clock className="w-3.5 h-3.5 text-cyan-400" />
                      {formatDateTime(call.started_at)}
                    </span>
                    <span>·</span>
                    <span>Duration: <strong className="text-white">{formatDuration(call.duration_seconds)}</strong></span>
                    <span>·</span>
                    <span>Provider: <strong className="text-cyan-400 uppercase">{call.telephony_provider}</strong></span>
                  </div>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wide ${
                call.status?.toUpperCase() === 'ENDED' ? 'bg-slate-500/10 text-slate-300 border border-slate-500/20'
                : call.status?.toUpperCase() === 'ACTIVE' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 animate-pulse'
                : 'bg-cyan-500/10 text-cyan-300 border border-cyan-500/30'
              }`}>
                {call.status}
              </span>

              {analysis && (
                <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wide border ${
                  String(analysis.risk_level).toUpperCase() === 'LOW'
                    ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30 shadow-[0_0_15px_rgba(16,185,129,0.2)]'
                    : String(analysis.risk_level).toUpperCase() === 'MEDIUM'
                    ? 'bg-amber-500/10 text-amber-400 border-amber-500/30 shadow-[0_0_15px_rgba(245,158,11,0.2)]'
                    : 'bg-rose-500/10 text-rose-400 border-rose-500/30 shadow-[0_0_15px_rgba(244,63,94,0.3)]'
                }`}>
                  {analysis.risk_level} RISK
                </span>
              )}
            </div>

          </div>
        </div>

        {/* 2-Column Intelligence Grid */}
        {analysis && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            
            {/* Classification Card */}
            <div className="card-glow">
              <div className="flex items-center justify-between mb-4 border-b border-white/5 pb-3">
                <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                  <Shield className="w-4 h-4 text-cyan-400" />
                  Multi-Factor Classification
                </h3>
                <span className="text-[10px] text-cyan-400 font-mono">ACOUSTIC & NLU</span>
              </div>

              <dl className="space-y-4 text-xs">
                <div className="flex items-center justify-between">
                  <dt className="text-slate-400">Caller Acoustic Profile</dt>
                  <dd className="flex items-center gap-2">
                    <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-cyan-500/10 text-cyan-300 border border-cyan-500/30 uppercase">
                      {analysis.caller_type}
                    </span>
                    <span className="text-[10px] text-slate-500 font-mono">
                      {formatConfidence(analysis.caller_type_confidence)}
                    </span>
                  </dd>
                </div>

                <div className="flex items-center justify-between">
                  <dt className="text-slate-400">Intent Vector</dt>
                  <dd className="flex items-center gap-2">
                    <span className="font-semibold text-white">
                      {intentLabel(analysis.intent)}
                    </span>
                    <span className="text-[10px] text-slate-500 font-mono">
                      {formatConfidence(analysis.intent_confidence)}
                    </span>
                  </dd>
                </div>

                {analysis.secondary_intent && (
                  <div className="flex items-center justify-between">
                    <dt className="text-slate-400">Secondary Vector</dt>
                    <dd className="text-slate-300">{intentLabel(analysis.secondary_intent)}</dd>
                  </div>
                )}

                <div className="flex items-center justify-between">
                  <dt className="text-slate-400">Evaluated Risk Score</dt>
                  <dd className="flex items-center gap-2">
                    <span className="font-bold text-white uppercase">
                      {analysis.risk_level}
                    </span>
                    <span className="text-[10px] text-slate-500 font-mono">
                      {formatConfidence(analysis.risk_confidence)} confidence
                    </span>
                  </dd>
                </div>
              </dl>

              {/* Risk Indicators */}
              {(analysis.risk_indicators || []).length > 0 && (
                <div className="mt-4 pt-4 border-t border-white/5">
                  <p className="text-[10px] font-bold text-rose-400 mb-2 uppercase tracking-wider">
                    Threat Indicators Detected
                  </p>
                  <ul className="space-y-1.5">
                    {(analysis.risk_indicators || []).map((indicator, i) => (
                      <li key={i} className="flex items-center gap-2 text-xs text-rose-300 bg-rose-500/10 border border-rose-500/20 p-2 rounded-lg">
                        <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0 text-rose-400" />
                        <span>{indicator}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            {/* Decision & Action Card */}
            <div className="card-glow">
              <div className="flex items-center justify-between mb-4 border-b border-white/5 pb-3">
                <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                  <Zap className="w-4 h-4 text-purple-400" />
                  Policy Verdict & Decision
                </h3>
                <span className="text-[10px] text-purple-400 font-mono">RULE ENGINE</span>
              </div>

              <div className="text-center py-4 bg-slate-950/60 rounded-xl border border-white/5 mb-4">
                <p className="text-2xl font-extrabold text-white tracking-wide">{decisionLabel(analysis.decision)}</p>
                <p className="text-[11px] text-slate-400 font-mono mt-1">
                  Confidence: {formatConfidence(analysis.decision_confidence)}
                </p>
              </div>

              <div className="bg-slate-950/40 rounded-xl p-3.5 border border-white/5 text-xs text-slate-300">
                <p className="font-semibold text-cyan-400 mb-1">Arbitration Reason</p>
                <p className="leading-relaxed">{analysis.decision_reason || 'Screening policy evaluated successfully.'}</p>
              </div>

              {analysis.analysis_latency_ms && (
                <p className="text-[11px] text-slate-500 font-mono mt-3 text-right">
                  Pipeline Latency: <span className="text-cyan-400">{analysis.analysis_latency_ms}ms</span>
                </p>
              )}
            </div>

          </div>
        )}

        {/* Recruitment Intelligence Card */}
        {recruitment_details && (
          <div className="card-glow">
            <div className="flex items-center justify-between mb-4 border-b border-white/5 pb-3">
              <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <Briefcase className="w-4 h-4 text-cyan-400" />
                Structured Recruitment Intelligence
              </h3>
              <span className="text-[10px] text-emerald-400 font-mono">ENTITY EXTRACTION</span>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
              {[
                { label: 'Company Target', value: recruitment_details.company },
                { label: 'Position / Role', value: recruitment_details.position },
                { label: 'Recruiter Name', value: recruitment_details.recruiter_name },
                { label: 'Interview Stage', value: recruitment_details.interview_stage },
                { label: 'Scheduled Date', value: recruitment_details.interview_date },
                { label: 'Scheduled Time', value: recruitment_details.interview_time },
                { label: 'Next Protocol Step', value: recruitment_details.next_step },
              ].map(({ label, value }) => value ? (
                <div key={label} className="bg-slate-950/40 p-3 rounded-xl border border-white/5">
                  <p className="text-[10px] text-slate-500 uppercase font-mono">{label}</p>
                  <p className="font-semibold text-white mt-0.5 truncate">{value}</p>
                </div>
              ) : null)}
            </div>

            {recruitment_details.is_legitimate !== null && (
              <div className={`mt-4 p-3.5 rounded-xl text-xs border ${
                recruitment_details.is_legitimate
                  ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
                  : 'bg-rose-500/10 text-rose-300 border-rose-500/30'
              }`}>
                <strong>{recruitment_details.is_legitimate ? '✅ Legitimate Opportunity:' : '❌ Suspicious Job Pretext:'}</strong>
                {recruitment_details.legitimacy_reason && (
                  <span className="ml-2">{recruitment_details.legitimacy_reason}</span>
                )}
              </div>
            )}
          </div>
        )}

        {/* Real-time Audio Transcript Card */}
        {transcript && (
          <div className="card-glow">
            <div className="flex items-center justify-between mb-4 border-b border-white/5 pb-3">
              <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <MessageSquare className="w-4 h-4 text-cyan-400" />
                Decoded Speech Transcript
              </h3>
              <span className="text-[10px] text-slate-400 font-mono">{transcript.word_count} WORDS ANALYZED</span>
            </div>

            {transcript.summary && (
              <div className="bg-slate-950/70 border border-cyan-500/20 rounded-2xl p-4 mb-6 text-xs text-slate-300 leading-relaxed font-mono whitespace-pre-line shadow-[0_0_20px_rgba(6,182,212,0.1)]">
                <p className="text-[10px] font-bold text-cyan-400 mb-2 uppercase tracking-widest flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-cyan-400" />
                  Executive Call Summary
                </p>
                {transcript.summary}
              </div>
            )}

            <div className="space-y-3.5">
              {(transcript.segments || []).map((seg) => (
                <div
                  key={seg.id}
                  className={`flex gap-3 ${seg.speaker === 'AGENT' ? 'flex-row-reverse' : ''}`}
                >
                  <div className={`w-8 h-8 rounded-xl flex-shrink-0 flex items-center justify-center text-xs font-bold border ${
                    seg.speaker === 'CALLER'
                      ? 'bg-slate-800 text-slate-300 border-white/10'
                      : 'bg-cyan-500 text-slate-950 border-cyan-400 shadow-[0_0_15px_rgba(6,182,212,0.4)]'
                  }`}>
                    {seg.speaker === 'CALLER' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                  </div>
                  
                  <div className={`max-w-[80%] rounded-2xl px-4 py-3 text-xs leading-relaxed border ${
                    seg.speaker === 'CALLER'
                      ? 'bg-slate-900/80 text-slate-200 border-white/10'
                      : 'bg-gradient-to-r from-cyan-950/80 to-blue-950/80 text-cyan-100 border-cyan-500/30 shadow-[0_0_20px_rgba(6,182,212,0.15)]'
                  }`}>
                    <p>{seg.text}</p>
                    {seg.confidence && (
                      <p className="text-[10px] mt-1.5 font-mono opacity-50">
                        {formatConfidence(seg.confidence)} confidence
                      </p>
                    )}
                  </div>
                </div>
              ))}

              {transcript.segments.length === 0 && (
                <p className="text-slate-500 text-xs text-center py-6 font-mono">
                  NO SPEECH PACKETS RECORDED IN THIS SESSION
                </p>
              )}
            </div>
          </div>
        )}

      </main>
    </div>
  );
}
