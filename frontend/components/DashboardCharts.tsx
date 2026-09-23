'use client';

import {
  BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis,
  CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts';

const RISK_COLORS: Record<string, string> = {
  low: '#22c55e',
  medium: '#f59e0b',
  high: '#ef4444',
  critical: '#dc2626',
};

const CALLER_COLORS: Record<string, string> = {
  human: '#10b981',
  ai: '#3b82f6',
  robocall: '#f97316',
  unknown: '#64748b',
};

const INTENT_COLORS: string[] = [
  '#3b82f6', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#06b6d4', '#6366f1'
];

interface DashboardChartsProps {
  stats: {
    risk_distribution?: Record<string, number>;
    caller_type_distribution?: Record<string, number>;
    intent_distribution?: Record<string, number>;
  } | null;
}

export default function DashboardCharts({ stats }: DashboardChartsProps) {
  const riskData = Object.entries(stats?.risk_distribution || {}).map(([name, value]) => ({
    name: name.toLowerCase(),
    displayName: name.toUpperCase(),
    value,
  }));
  const riskTotal = riskData.reduce((s, d) => s + d.value, 0);

  const callerData = Object.entries(stats?.caller_type_distribution || {}).map(([name, value]) => ({
    name: name.toLowerCase(),
    displayName: name === 'ai' ? 'AI Bot' : name.charAt(0).toUpperCase() + name.slice(1),
    value,
  }));
  const callerTotal = callerData.reduce((s, d) => s + d.value, 0);

  const intentData = Object.entries(stats?.intent_distribution || {})
    .filter(([, v]) => v > 0)
    .map(([name, value], index) => ({
      name: name.length > 10 ? `${name.substring(0, 9)}…` : name,
      displayName: name.replace(/_/g, ' '),
      value,
      color: INTENT_COLORS[index % INTENT_COLORS.length],
    }));

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      {/* Risk Distribution */}
      <div className="card">
        <h3 className="text-sm font-semibold text-slate-700 mb-4">Risk Distribution</h3>
        {riskTotal === 0 ? (
          <div className="h-48 flex items-center justify-center text-slate-300 text-sm">No data yet</div>
        ) : (
          <div className="w-full h-48">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={riskData} cx="50%" cy="50%" innerRadius={45} outerRadius={70} dataKey="value" nameKey="displayName">
                  {riskData.map((entry) => (
                    <Cell key={entry.name} fill={RISK_COLORS[entry.name] || '#94a3b8'} />
                  ))}
                </Pie>
                <Tooltip formatter={(v: number, name: string) => [`${v} calls`, name]} />
                <Legend iconSize={10} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Caller Type Distribution */}
      <div className="card">
        <h3 className="text-sm font-semibold text-slate-700 mb-4">Caller Type</h3>
        {callerTotal === 0 ? (
          <div className="h-48 flex items-center justify-center text-slate-300 text-sm">No data yet</div>
        ) : (
          <div className="w-full h-48">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={callerData} cx="50%" cy="50%" innerRadius={45} outerRadius={70} dataKey="value" nameKey="displayName">
                  {callerData.map((entry) => (
                    <Cell key={entry.name} fill={CALLER_COLORS[entry.name] || '#94a3b8'} />
                  ))}
                </Pie>
                <Tooltip formatter={(v: number, name: string) => [`${v} calls`, name]} />
                <Legend iconSize={10} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Intent Distribution */}
      <div className="card">
        <h3 className="text-sm font-semibold text-slate-700 mb-4">Intent Distribution</h3>
        {intentData.length === 0 ? (
          <div className="h-48 flex items-center justify-center text-slate-300 text-sm">No data yet</div>
        ) : (
          <div className="w-full h-48">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={intentData} margin={{ top: 10, right: 10, bottom: 20, left: -20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="displayName" tick={{ fontSize: 10 }} interval={0} angle={-15} textAnchor="end" />
                <YAxis tick={{ fontSize: 10 }} allowDecimals={false} />
                <Tooltip formatter={(v: number) => [`${v} calls`, 'Count']} labelFormatter={(label) => `Intent: ${label}`} />
                <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                  {intentData.map((entry, idx) => (
                    <Cell key={`cell-${idx}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </div>
  );
}
