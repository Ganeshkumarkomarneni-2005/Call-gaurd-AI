import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { formatDistanceToNow, format } from 'date-fns';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatRelativeTime(dateStr: string): string {
  try {
    return formatDistanceToNow(new Date(dateStr), { addSuffix: true });
  } catch {
    return dateStr;
  }
}

export function formatDateTime(dateStr: string): string {
  try {
    return format(new Date(dateStr), 'MMM d, yyyy HH:mm');
  } catch {
    return dateStr;
  }
}

export function formatDuration(seconds: number | null): string {
  if (seconds == null) return '—';
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  if (m === 0) return `${s}s`;
  return `${m}m ${s}s`;
}

export function formatConfidence(value: number): string {
  return `${Math.round(value * 100)}%`;
}

export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type CallerType = 'HUMAN' | 'AI' | 'ROBOCALL' | 'UNKNOWN';

export function riskBadgeClass(risk: RiskLevel): string {
  return {
    LOW: 'badge-low',
    MEDIUM: 'badge-medium',
    HIGH: 'badge-high',
    CRITICAL: 'badge-critical',
  }[risk] ?? 'badge-unknown';
}

export function callerTypeBadgeClass(type: CallerType): string {
  return {
    HUMAN: 'badge-human',
    AI: 'badge-ai',
    ROBOCALL: 'badge-robocall',
    UNKNOWN: 'badge-unknown',
  }[type] ?? 'badge-unknown';
}

export function riskColor(risk: RiskLevel): string {
  return {
    LOW: '#22c55e',
    MEDIUM: '#f59e0b',
    HIGH: '#ef4444',
    CRITICAL: '#7c3aed',
  }[risk] ?? '#94a3b8';
}

export function intentLabel(intent: string): string {
  return {
    RECRUITMENT: '💼 Recruitment',
    PROMOTIONAL: '📣 Promotional',
    FRAUD: '⚠️ Fraud',
    CUSTOMER_SERVICE: '🎧 Customer Service',
    DELIVERY: '📦 Delivery',
    PERSONAL: '👤 Personal',
    OTHER: '❓ Other',
    UNKNOWN: '🔍 Unknown',
  }[intent] ?? intent;
}

export function decisionLabel(decision: string): string {
  return {
    AI_HANDLE: '🤖 AI Handled',
    NOTIFY: '🔔 Notify User',
    TRANSFER: '↗️ Transfer',
    END: '🚫 Call Ended',
    FLAG_FOR_REVIEW: '🚩 Flagged for Review',
  }[decision] ?? decision;
}
