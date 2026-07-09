import React from 'react';
import { SimulationStateResponseDTO } from '@/types/api';

interface MetricsPanelProps {
  state: SimulationStateResponseDTO | null;
}

export default function MetricsPanel({ state }: MetricsPanelProps) {
  const format = (v: number | undefined | null, d = 'N/A') =>
    v !== undefined && v !== null ? v.toFixed(2) : d;

  return (
    <div
      style={{
        padding: '1rem',
        border: '1px solid #eaeaea',
        borderRadius: '8px',
        backgroundColor: '#fafafa',
      }}
    >
      <h3>Key Metrics</h3>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: '1rem',
          marginTop: '1rem',
        }}
      >
        <div>
          <strong>Population:</strong>
          <div>{state?.population ?? 'N/A'}</div>
        </div>

        <div>
          <strong>Economic Health:</strong>
          <div>{format(state?.economic_health)}</div>
        </div>

        <div>
          <strong>Social Cohesion:</strong>
          <div>{format(state?.social_cohesion)}</div>
        </div>

        <div>
          <strong>Crime Rate:</strong>
          <div>{format(state?.crime_rate)}</div>
        </div>

        <div>
          <strong>Protest Intensity:</strong>
          <div>{format(state?.protest_intensity)}</div>
        </div>

        <div>
          <strong>Unemployment:</strong>
          <div>{format(state?.unemployment_rate)}</div>
        </div>

        <div>
          <strong>System Unlust:</strong>
          <div>{format(state?.unlust)}</div>
        </div>

        <div>
          <strong>Morality:</strong>
          <div>{format(state?.morality)}</div>
        </div>
      </div>
    </div>
  );
}
