import React from 'react';
import { SimulationStateResponseDTO } from '@/types/api';

interface SelfActualizationPanelProps {
  state: SimulationStateResponseDTO | null;
}

export default function SelfActualizationPanel({ state }: SelfActualizationPanelProps) {
  if (!state) {
    return (
      <div className="panel-inner" style={{ textAlign: 'center', color: 'var(--ink-soft)', fontSize: '12px', padding: '30px 14px' }}>
        No simulation running.
      </div>
    );
  }

  const bars = [
    { label: 'Morality', val: state.morality ?? 0, color: '#6d8aaa' },
    { label: 'Innovation', val: state.innovation_index ?? 0, color: '#8aac4a' },
    { label: 'Economic Health', val: state.economic_health ?? 0, color: '#e0b050' },
    { label: 'Social Cohesion', val: state.social_cohesion ?? 0, color: '#9a8a6a' },
  ];

  return (
    <div className="panel-inner">
      <p style={{ fontSize: '11px', color: 'var(--ink-soft)', marginBottom: '12px' }}>
        Collective self-actualization gauges for the society.
      </p>
      {bars.map((b) => (
        <div className="bar-row" key={b.label}>
          <div className="bl">
            <span className="n">{b.label}</span>
            <span>{(b.val * 100).toFixed(0)}%</span>
          </div>
          <div className="bar-track">
            <div className="bar-fill" style={{
              width: `${Math.min(100, b.val * 100)}%`,
              background: b.color,
              boxShadow: `0 0 4px ${b.color}`,
            }} />
          </div>
        </div>
      ))}
    </div>
  );
}
