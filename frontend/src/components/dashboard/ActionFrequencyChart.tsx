import React, { useState } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import { useSimulationStore } from '@/store/simulationStore';

const ACTION_CATEGORIES: Record<string, { label: string; color: string }> = {
  survival: { label: 'Survival', color: '#4A90D9' },
  social: { label: 'Social', color: '#50C878' },
  economic: { label: 'Economic', color: '#FF8C00' },
  criminal: { label: 'Criminal', color: '#DC143C' },
  political: { label: 'Political', color: '#8B008B' },
};

const ACTION_CATEGORY_MAP: Record<string, string> = {
  work: 'economic',
  buy_food: 'survival',
  rest: 'survival',
  seek_job: 'economic',
  beg: 'economic',
  befriend: 'social',
  console: 'social',
  isolate: 'social',
  share: 'social',
  steal: 'criminal',
  harm_other: 'criminal',
  protest: 'political',
  complain: 'political',
  comply: 'political',
  idle: 'survival',
};

const ACTION_LABELS: Record<string, string> = {
  work: 'Work',
  buy_food: 'Buy Food',
  rest: 'Rest',
  seek_job: 'Seek Job',
  beg: 'Beg',
  befriend: 'Befriend',
  console: 'Console',
  isolate: 'Isolate',
  share: 'Share',
  steal: 'Steal',
  harm_other: 'Harm Other',
  protest: 'Protest',
  complain: 'Complain',
  comply: 'Comply',
  idle: 'Idle',
};

export default function ActionFrequencyChart() {
  const actionHistory = useSimulationStore((s) => s.actionHistory);
  const [showPercent, setShowPercent] = useState(false);

  if (actionHistory.length === 0) {
    return (
      <div
        style={{
          padding: '1rem',
          border: '1px solid #eaeaea',
          borderRadius: '8px',
          backgroundColor: '#fafafa',
          height: 300,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <p style={{ color: '#999' }}>No action data yet. Run the simulation to see action frequencies.</p>
      </div>
    );
  }

  // Use the latest tick's action counts
  const latest = actionHistory[actionHistory.length - 1];
  const counts = latest.action_counts;
  const totalActions = Object.values(counts).reduce((sum, v) => sum + v, 0);

  // Build chart data
  const chartData = Object.entries(ACTION_LABELS).map(([key, label]) => {
    const value = counts[key] ?? 0;
    const displayValue = showPercent && totalActions > 0
      ? parseFloat(((value / totalActions) * 100).toFixed(2))
      : value;
    const category = ACTION_CATEGORY_MAP[key] || 'survival';
    const color = ACTION_CATEGORIES[category]?.color || '#999';
    return {
      action: label,
      count: displayValue,
      fill: color,
      raw: value,
      category,
    };
  });

  const formatTick = (value: number) => {
    if (showPercent) return `${value}%`;
    return String(value);
  };

  return (
    <div
      style={{
        padding: '1rem',
        border: '1px solid #eaeaea',
        borderRadius: '8px',
        backgroundColor: '#fafafa',
      }}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '0.5rem',
        }}
      >
        <h3 style={{ margin: 0 }}>Action Frequency (Tick {latest.tick})</h3>
        <label style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', fontSize: '0.8rem', cursor: 'pointer' }}>
          <input
            type="checkbox"
            checked={showPercent}
            onChange={() => setShowPercent((p) => !p)}
          />
          Show percentages
        </label>
      </div>

      {/* Color legend by category */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem', marginBottom: '0.75rem' }}>
        {Object.entries(ACTION_CATEGORIES).map(([key, config]) => (
          <span key={key} style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', fontSize: '0.78rem' }}>
            <span
              style={{
                width: 10,
                height: 10,
                borderRadius: '2px',
                backgroundColor: config.color,
                display: 'inline-block',
              }}
            />
            {config.label}
          </span>
        ))}
      </div>

      <div style={{ width: '100%', height: 300 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
            <XAxis
              dataKey="action"
              stroke="#666"
              fontSize={11}
              angle={-35}
              textAnchor="end"
              height={60}
              interval={0}
            />
            <YAxis stroke="#666" fontSize={12} tickFormatter={formatTick} />
            <Tooltip
              contentStyle={{
                backgroundColor: '#fff',
                border: '1px solid #eaeaea',
                borderRadius: '4px',
                fontSize: '0.8rem',
              }}
              formatter={(value: number, _name: string, item: any) => {
                const raw = item?.payload?.raw ?? value;
                const cat = ACTION_CATEGORIES[item?.payload?.category]?.label || 'Unknown';
                return showPercent
                  ? [`${value}% (${raw} total)`, cat]
                  : [`${raw}`, cat];
              }}
              labelFormatter={(label: string) => label}
            />
            <Bar dataKey="count" name="Count" isAnimationActive={false}>
              {chartData.map((entry, index) => (
                <Cell key={index} fill={entry.fill} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
