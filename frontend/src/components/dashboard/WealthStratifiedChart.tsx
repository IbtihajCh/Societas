import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { useSimulationStore } from '@/store/simulationStore';

function cssVar(name: string): string {
  if (typeof window === 'undefined') return '#000';
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim() || '#000';
}

const CLASS_COLORS: Record<string, string> = {
  poor: cssVar('--oxblood'),
  middle: cssVar('--ochre'),
  rich: cssVar('--gold'),
};

interface WealthStratifiedChartProps {
  state?: any;
}

export default function WealthStratifiedChart(_props: WealthStratifiedChartProps) {
  const wealthStratified = useSimulationStore((s) => s.wealthStratified);
  const metricsHistory = useSimulationStore((s) => s.metricsHistory);

  if (wealthStratified.length === 0) {
    return (
      <div
        className="panel"
        style={{
          height: 300,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <p style={{ color: 'var(--ink-soft)' }}>No wealth data yet. Run the simulation to see distribution.</p>
      </div>
    );
  }

  // Build summary for the latest tick
  const latest = wealthStratified[wealthStratified.length - 1];
  const latestTick = latest.tick;
  const latestMetrics = metricsHistory.find((m) => m.tick === latestTick);
  const totalWealth = latest.poor + latest.middle + latest.rich;
  const pctPoor = totalWealth > 0 ? ((latest.poor / totalWealth) * 100).toFixed(1) : '0.0';
  const pctMiddle = totalWealth > 0 ? ((latest.middle / totalWealth) * 100).toFixed(1) : '0.0';
  const pctRich = totalWealth > 0 ? ((latest.rich / totalWealth) * 100).toFixed(1) : '0.0';

  return (
    <div className="panel">
      <h3 style={{ margin: 0, marginBottom: '0.75rem' }}>Wealth Stratification</h3>

      <div style={{ width: '100%', height: 300 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={wealthStratified} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={cssVar('--rule')} strokeOpacity={0.5} />
            <XAxis dataKey="tick" stroke={cssVar('--ink-soft')} fontSize={12} />
            <YAxis stroke={cssVar('--ink-soft')} fontSize={12} />
            <Tooltip
              contentStyle={{
                backgroundColor: cssVar('--parchment'),
                border: '1px solid ' + cssVar('--rule-strong'),
                borderRadius: '4px',
                fontSize: '0.8rem',
              }}
              labelStyle={{ color: cssVar('--ink') }}
              itemStyle={{ color: cssVar('--ink-soft') }}
              formatter={(value: number, name: string) => {
                const label = name.charAt(0).toUpperCase() + name.slice(1);
                return [value, label];
              }}
            />
            <Legend wrapperStyle={{ color: cssVar('--ink-soft') }} />
            <Bar dataKey="poor" name="Poor" fill={CLASS_COLORS.poor} stackId="wealth" />
            <Bar dataKey="middle" name="Middle" fill={CLASS_COLORS.middle} stackId="wealth" />
            <Bar dataKey="rich" name="Rich" fill={CLASS_COLORS.rich} stackId="wealth" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Summary table */}
      <div style={{ marginTop: '0.75rem', fontSize: '0.85rem' }}>
        <h4 style={{ margin: 0, marginBottom: '0.5rem' }}>Latest Distribution (Tick {latestTick})</h4>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--rule)' }}>
              <th style={{ textAlign: 'left', padding: '0.3rem 0.5rem' }}>Class</th>
              <th style={{ textAlign: 'right', padding: '0.3rem 0.5rem' }}>Count</th>
              <th style={{ textAlign: 'right', padding: '0.3rem 0.5rem' }}>Percentage</th>
            </tr>
          </thead>
          <tbody>
            <tr style={{ borderBottom: '1px solid var(--rule)' }}>
              <td style={{ padding: '0.3rem 0.5rem' }}>
                <span style={{ color: CLASS_COLORS.poor, fontWeight: 'bold' }}>●</span> Poor
              </td>
              <td style={{ textAlign: 'right', padding: '0.3rem 0.5rem' }}>{latest.poor}</td>
              <td style={{ textAlign: 'right', padding: '0.3rem 0.5rem' }}>{pctPoor}%</td>
            </tr>
            <tr style={{ borderBottom: '1px solid var(--rule)' }}>
              <td style={{ padding: '0.3rem 0.5rem' }}>
                <span style={{ color: CLASS_COLORS.middle, fontWeight: 'bold' }}>●</span> Middle
              </td>
              <td style={{ textAlign: 'right', padding: '0.3rem 0.5rem' }}>{latest.middle}</td>
              <td style={{ textAlign: 'right', padding: '0.3rem 0.5rem' }}>{pctMiddle}%</td>
            </tr>
            <tr>
              <td style={{ padding: '0.3rem 0.5rem' }}>
                <span style={{ color: CLASS_COLORS.rich, fontWeight: 'bold' }}>●</span> Rich
              </td>
              <td style={{ textAlign: 'right', padding: '0.3rem 0.5rem' }}>{latest.rich}</td>
              <td style={{ textAlign: 'right', padding: '0.3rem 0.5rem' }}>{pctRich}%</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}
