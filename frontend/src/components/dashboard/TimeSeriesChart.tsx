import React, { useState } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { useSimulationStore } from '@/store/simulationStore';

const METRICS_CONFIG: Record<string, { label: string; color: string; normalized: boolean }> = {
  economic_health: { label: 'Economic Health', color: '#4CAF50', normalized: true },
  social_cohesion: { label: 'Social Cohesion', color: '#2196F3', normalized: true },
  crime_rate: { label: 'Crime Rate', color: '#F44336', normalized: true },
  protest_intensity: { label: 'Protest Intensity', color: '#9C27B0', normalized: true },
  unemployment_rate: { label: 'Unemployment Rate', color: '#FF9800', normalized: true },
  avg_unlust: { label: 'Avg Unlust', color: '#795548', normalized: true },
  population: { label: 'Population', color: '#607D8B', normalized: false },
};

const DEFAULT_VISIBLE = ['economic_health', 'crime_rate', 'avg_unlust'];

export default function TimeSeriesChart() {
  const metricsHistory = useSimulationStore((s) => s.metricsHistory);
  const [visible, setVisible] = useState<Set<string>>(new Set(DEFAULT_VISIBLE));

  const toggleMetric = (key: string) => {
    setVisible((prev) => {
      const next = new Set(prev);
      if (next.has(key)) {
        next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });
  };

  if (metricsHistory.length === 0) {
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
        <p style={{ color: '#999' }}>No metrics history yet. Run the simulation to see data.</p>
      </div>
    );
  }

  return (
    <div
      style={{
        padding: '1rem',
        border: '1px solid #eaeaea',
        borderRadius: '8px',
        backgroundColor: '#fafafa',
      }}
    >
      <h3 style={{ margin: 0, marginBottom: '0.5rem' }}>Time-Series Metrics</h3>

      {/* Toggle checkboxes */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '0.75rem' }}>
        {Object.entries(METRICS_CONFIG).map(([key, config]) => (
          <label
            key={key}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.3rem',
              fontSize: '0.8rem',
              cursor: 'pointer',
              userSelect: 'none',
            }}
          >
            <input
              type="checkbox"
              checked={visible.has(key)}
              onChange={() => toggleMetric(key)}
            />
            <span
              style={{
                width: 10,
                height: 10,
                borderRadius: '50%',
                backgroundColor: config.color,
                display: 'inline-block',
              }}
            />
            {config.label}
          </label>
        ))}
      </div>

      <div style={{ width: '100%', height: 300 }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={metricsHistory} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
            <XAxis dataKey="tick" stroke="#666" fontSize={12} />
            <YAxis stroke="#666" fontSize={12} />
            <Tooltip
              contentStyle={{
                backgroundColor: '#fff',
                border: '1px solid #eaeaea',
                borderRadius: '4px',
                fontSize: '0.8rem',
              }}
            />
            <Legend />
            {Object.entries(METRICS_CONFIG).map(([key, config]) => {
              if (!visible.has(key)) return null;
              return (
                <Line
                  key={key}
                  type="monotone"
                  dataKey={key}
                  name={config.label}
                  stroke={config.color}
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 4 }}
                  isAnimationActive={false}
                />
              );
            })}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
