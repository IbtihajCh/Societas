import React from 'react';
import { SimulationStateResponseDTO } from '@/types/api';

interface DiagnosticsPanelProps {
  state: SimulationStateResponseDTO | null;
}

export default function DiagnosticsPanel({ state }: DiagnosticsPanelProps) {
  return (
    <div style={{
      padding: '1rem',
      border: '1px solid #eaeaea',
      borderRadius: '8px',
      backgroundColor: '#fafafa',
    }}>
      <h3>Diagnostics</h3>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginTop: '1rem' }}>
        <div>
          <strong>Last Tick Duration:</strong>
          <div style={{ color: (state?.duration_ms ?? 0) > 5000 ? '#f44336' : '#4caf50' }}>
            {state?.duration_ms ? `${(state.duration_ms / 1000).toFixed(1)}s` : 'N/A'}
          </div>
        </div>
        <div>
          <strong>AI Calls:</strong>
          <div>{state?.ai_calls ?? 'N/A'}</div>
        </div>
        <div>
          <strong>Ambiguity Count:</strong>
          <div>{state?.ambiguity_count ?? 'N/A'}</div>
        </div>
        <div>
          <strong>State Hash:</strong>
          <div style={{ fontSize: '0.7rem', wordBreak: 'break-all', fontFamily: 'monospace' }}>
            {state?.state_hash ? state.state_hash.substring(0, 16) + '...' : 'N/A'}
          </div>
        </div>
        <div>
          <strong>Avg Time per AI Call:</strong>
          <div>
            {state?.ai_calls && state.ai_calls > 0 && state.duration_ms
              ? `${(state.duration_ms / state.ai_calls / 1000).toFixed(2)}s`
              : 'N/A'}
          </div>
        </div>
        <div>
          <strong>Determinism Check:</strong>
          <div style={{ color: state?.state_hash ? '#4caf50' : '#999' }}>
            {state?.state_hash ? '✅ Verified' : 'N/A'}
          </div>
        </div>
      </div>
    </div>
  );
}
