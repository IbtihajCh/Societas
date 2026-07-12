import React from 'react';
import { SimulationStateResponseDTO, MetricsResponseDTO } from '@/types/api';
import { useSimulationStore } from '@/store/simulationStore';
import Sparkline from './Sparkline';

interface MetricsPanelProps {
  state: SimulationStateResponseDTO | null;
  metrics?: MetricsResponseDTO | null;
}

function deltaStr(curr: number, prev: number | undefined): { text: string; cls: 'up' | 'down' | 'steady' } {
  if (prev === undefined) return { text: 'steady', cls: 'steady' };
  const d = curr - prev;
  if (Math.abs(d) < 0.005) return { text: 'steady', cls: 'steady' };
  return { text: `${d > 0 ? '▲' : '▼'} ${Math.abs(d).toFixed(3)}`, cls: d > 0 ? 'up' : 'down' };
}

const METRICS = [
  { label: 'POPULATION', key: 'population' as const, fmt: (v: any) => `${v}` },
  { label: 'ECONOMIC HEALTH', key: 'economic_health' as const, fmt: (v: any) => (v ?? 0).toFixed(2) },
  { label: 'EMPLOYMENT', key: 'unemployment_rate' as const, invert: true, fmt: (v: any) => ((v ?? 0) * 100).toFixed(1) + '%' },
  { label: 'CRIME RATE', key: 'crime_rate' as const, invert: true, fmt: (v: any) => ((v ?? 0) * 100).toFixed(1) + '%' },
  { label: 'SOCIAL COHESION', key: 'social_cohesion' as const, fmt: (v: any) => (v ?? 0).toFixed(2) },
  { label: 'MORALITY', key: 'morality' as const, fmt: (v: any) => (v ?? 0).toFixed(2) },
];

const GAUGES = [
  { label: 'ECON', key: 'economic_health' as const },
  { label: 'COHESION', key: 'social_cohesion' as const },
  { label: 'MORALITY', key: 'morality' as const },
  { label: 'SAFETY', key: 'public_order' as const },
];

function RingGauge({ value, label }: { value: number; label: string }) {
  const R = 36;
  const circ = 2 * Math.PI * R;
  const pct = Math.min(1, Math.max(0, value));
  // Start at -130 deg, end at +130 deg
  const startAngle = -130 * Math.PI / 180;
  const sweepAngle = (pct * 260) * Math.PI / 180;
  const x1 = 48 + R * Math.cos(startAngle);
  const y1 = 48 + R * Math.sin(startAngle);
  const x2 = 48 + R * Math.cos(startAngle + sweepAngle);
  const y2 = 48 + R * Math.sin(startAngle + sweepAngle);
  const largeArc = pct > 0.5 ? 1 : 0;

  const color = value > 0.7 ? 'var(--moss)' : value > 0.4 ? 'var(--ochre)' : 'var(--oxblood)';

  return (
    <div className="gauge">
      <svg width="96" height="96" viewBox="0 0 96 96">
        <circle cx="48" cy="48" r={R} fill="none" stroke="var(--rule)" strokeWidth="5" />
        <path d={`M${x1},${y1} A${R},${R} 0 ${largeArc},1 ${x2},${y2}`}
          fill="none" stroke={color} strokeWidth="5" strokeLinecap="round" />
        <text x="48" y="49" textAnchor="middle" dominantBaseline="middle"
          fill="var(--ink)" fontSize="16" fontWeight="600" fontFamily="var(--font-mono)">
          {(value * 100).toFixed(0)}%
        </text>
      </svg>
      <span className="g-label">{label}</span>
    </div>
  );
}

export default function MetricsPanel({ state, metrics }: MetricsPanelProps) {
  const metricsHistory = useSimulationStore((s) => s.metricsHistory);
  const prevTick = (state?.tick ?? 0) - 1;
  const prev = (key: string) => {
    const arr = metrics?.[key as keyof MetricsResponseDTO];
    if (Array.isArray(arr)) {
      const found = arr.find((p: any) => p.tick === prevTick);
      return found?.value;
    }
    return undefined;
  };

  const getSparklineValues = (key: string): number[] => {
    const sparkData = metrics?.[key as keyof MetricsResponseDTO];
    if (Array.isArray(sparkData)) {
      return sparkData.map((p: any) => p.value);
    }
    // Fallback to metricsHistory store
    if (metricsHistory.length > 0) {
      const vals = metricsHistory.map((h: any) => h[key]).filter((v: any) => typeof v === 'number');
      if (vals.length > 1) return vals;
    }
    return [];
  };

  return (
    <div className="metrics-panel-dark">
      <div className="metrics-stat-row">
        {METRICS.map((m) => {
          const val = state ? (state as any)[m.key] ?? 0 : 0;
          const pv = prev(m.key);
          const d = deltaStr(val, pv);
          const sparkVals = getSparklineValues(m.key);

          return (
            <div className="metrics-stat-card" key={m.key}>
              <span className="metrics-stat-label">{m.label}</span>
              <span className="metrics-stat-value">{m.fmt(val)}</span>
              <span className={`metrics-stat-delta ${d.cls}`}>{d.text}</span>
              {sparkVals.length > 1 && (
                <div className="metrics-sparkline">
                  <Sparkline
                    data={sparkVals}
                    width={50}
                    height={20}
                    colorVar="--gold"
                  />
                </div>
              )}
            </div>
          );
        })}
      </div>
      <div className="metrics-divider" />
      <div className="metrics-gauge-row">
        {GAUGES.map((g) => (
          <RingGauge
            key={g.key}
            value={(state as any)?.[g.key] ?? 0}
            label={g.label}
          />
        ))}
      </div>
    </div>
  );
}
