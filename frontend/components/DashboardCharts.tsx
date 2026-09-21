'use client';

import {
  BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis,
  CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts';

const RISK_COLORS: Record<string, string> = {
  LOW: '#22c55e', MEDIUM: '#f59e0b', HIGH: '#ef4444', CRITICAL: '#7c3aed',
};

const CALLER_COLORS: Record<string, string> = {
  HUMAN: '#10b981', AI: '#3b82f6', ROBOCALL: '#f97316', UNKNOWN: '#94a3b8',
};

interface DashboardChartsProps {
  stats: {
    risk_distribution?: Record<string, number>;
    caller_type_distribution?: Record<string, number>;
    intent_distribution?: Record<string, number>;
  } | null;
}

export default function DashboardCharts({ stats }: DashboardChartsProps) {
  const riskData = Object.entries(stats?.risk_distribution || {}).map(([name, value]) => ({ name, value }));
  const riskTotal = riskData.reduce((s, d) => s + d.value, 0);

  const callerData = Object.entries(stats?.caller_type_distribution || {}).map(([name, value]) => ({ name, value }));
  const callerTotal = callerData.reduce((s, d) => s + d.value, 0);

  const intentData = Object.entries(stats?.intent_distribution || {})
    .filter(([, v]) => v > 0)
    .map(([name, value]) => ({ name: name.substring(0, 8), value, fullName: name }));

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
                <Pie data={riskData} cx="50%" cy="50%" innerRadius={45} outerRadius={70} dataKey="value">
                  {riskData.map((entry) => (
                    <Cell key={entry.name} fill={RISK_COLORS[entry.name] || '#94a3b8'} />
                  ))}
                </Pie>
                <Tooltip formatter={(v: number) => [`${v} calls`, '']} />
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
                <Pie data={callerData} cx="50%" cy="50%" innerRadius={45} outerRadius={70} dataKey="value">
                  {callerData.map((entry) => (
                    <Cell key={entry.name} fill={CALLER_COLORS[entry.name] || '#94a3b8'} />
                  ))}
                </Pie>
                <Tooltip formatter={(v: number) => [`${v} calls`, '']} />
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
              <BarChart data={intentData} margin={{ top: 0, right: 0, bottom: 0, left: -20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                <YAxis tick={{ fontSize: 10 }} />
                <Tooltip labelFormatter={(l) => intentData.find(d => d.name === l)?.fullName || l} />
                <Bar dataKey="value" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </div>
  );
}
