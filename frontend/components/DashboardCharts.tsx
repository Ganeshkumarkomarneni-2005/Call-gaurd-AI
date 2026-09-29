'use client';

import {
  BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis,
  CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts';

const RISK_COLORS: Record<string, string> = {
  low: '#10b981',      // neon emerald
  medium: '#f59e0b',   // neon amber
  high: '#f43f5e',     // neon rose
  critical: '#a855f7', // neon purple
};

const CALLER_COLORS: Record<string, string> = {
  human: '#6366f1',    // neon indigo
  ai: '#06b6d4',       // neon cyan
  robocall: '#f97316', // neon orange
  unknown: '#64748b',  // slate
};

const INTENT_COLORS: string[] = [
  '#06b6d4', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#3b82f6', '#6366f1'
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
      <div className="card-glow">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Risk Matrix</h3>
          <span className="text-[10px] text-cyan-400 font-mono">LIVE TELEMETRY</span>
        </div>
        {riskTotal === 0 ? (
          <div className="h-48 flex items-center justify-center text-slate-500 text-xs font-mono">NO THREATS DETECTED</div>
        ) : (
          <div className="w-full h-48">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={riskData} cx="50%" cy="50%" innerRadius={48} outerRadius={72} stroke="#030712" strokeWidth={2} dataKey="value" nameKey="displayName">
                  {riskData.map((entry) => (
                    <Cell key={entry.name} fill={RISK_COLORS[entry.name] || '#94a3b8'} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#06b6d4', borderRadius: '12px', fontSize: '12px', color: '#fff' }}
                  itemStyle={{ color: '#06b6d4' }}
                  formatter={(v: number, name: string) => [`${v} calls`, name]}
                />
                <Legend iconSize={8} wrapperStyle={{ fontSize: '11px', color: '#94a3b8' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Caller Type Distribution */}
      <div className="card-glow">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Caller Acoustics</h3>
          <span className="text-[10px] text-purple-400 font-mono">VOICE DSP</span>
        </div>
        {callerTotal === 0 ? (
          <div className="h-48 flex items-center justify-center text-slate-500 text-xs font-mono">NO ACOUSTIC SAMPLES</div>
        ) : (
          <div className="w-full h-48">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={callerData} cx="50%" cy="50%" innerRadius={48} outerRadius={72} stroke="#030712" strokeWidth={2} dataKey="value" nameKey="displayName">
                  {callerData.map((entry) => (
                    <Cell key={entry.name} fill={CALLER_COLORS[entry.name] || '#94a3b8'} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#8b5cf6', borderRadius: '12px', fontSize: '12px', color: '#fff' }}
                  itemStyle={{ color: '#8b5cf6' }}
                  formatter={(v: number, name: string) => [`${v} calls`, name]}
                />
                <Legend iconSize={8} wrapperStyle={{ fontSize: '11px', color: '#94a3b8' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Intent Distribution */}
      <div className="card-glow">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Intent Vectors</h3>
          <span className="text-[10px] text-emerald-400 font-mono">NLU ENGINE</span>
        </div>
        {intentData.length === 0 ? (
          <div className="h-48 flex items-center justify-center text-slate-500 text-xs font-mono">NO INTENT DATA</div>
        ) : (
          <div className="w-full h-48">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={intentData} margin={{ top: 10, right: 10, bottom: 20, left: -20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="displayName" tick={{ fill: '#94a3b8', fontSize: 10 }} interval={0} angle={-15} textAnchor="end" />
                <YAxis tick={{ fill: '#94a3b8', fontSize: 10 }} allowDecimals={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#10b981', borderRadius: '12px', fontSize: '12px', color: '#fff' }}
                  formatter={(v: number) => [`${v} calls`, 'Count']}
                  labelFormatter={(label) => `Intent: ${label}`}
                />
                <Bar dataKey="value" radius={[6, 6, 0, 0]}>
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
