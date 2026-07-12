import React from 'react';
import { SimulationStateResponseDTO } from '@/types/api';

interface DiagnosticsPanelProps {
  state: SimulationStateResponseDTO | null;
}

export default function DiagnosticsPanel({ state }: DiagnosticsPanelProps) {
  return (
    <div className="panel diagnostics-card">
      <h3>Diagnostics</h3>
      <div className="diagnostics-grid">
        <div className="diag-row">
          <span className="diag-label">Last Tick Duration:</span>
          <span className="diag-val" style={{ color: (state?.duration_ms ?? 0) > 5000 ? 'var(--oxblood)' : 'var(--moss)' }}>
            {state?.duration_ms ? `${(state.duration_ms / 1000).toFixed(1)}s` : 'N/A'}
          </span>
        </div>
        <div className="diag-row">
          <span className="diag-label">AI Calls:</span>
          <span className="diag-val">{state?.ai_calls ?? 'N/A'}</span>
        </div>
        <div className="diag-row">
          <span className="diag-label">Ambiguity Count:</span>
          <span className="diag-val">{state?.ambiguity_count ?? 'N/A'}</span>
        </div>
        <div className="diag-row">
          <span className="diag-label">State Hash:</span>
          <span className="diag-hash">
            {state?.state_hash ? state.state_hash.substring(0, 16) + '...' : 'N/A'}
          </span>
        </div>
        <div className="diag-row">
          <span className="diag-label">Avg Time per AI Call:</span>
          <span className="diag-val">
            {state?.ai_calls && state.ai_calls > 0 && state.duration_ms
              ? `${(state.duration_ms / state.ai_calls / 1000).toFixed(2)}s`
              : 'N/A'}
          </span>
        </div>
        <div className="diag-row">
          <span className="diag-label">Determinism Check:</span>
          <span className="diag-val" style={{ color: state?.state_hash ? 'var(--moss)' : 'var(--ink-soft)' }}>
            {state?.state_hash ? '✅ Verified' : 'N/A'}
          </span>
        </div>
      </div>
      <style>{`
        .diagnostics-card { padding: 1rem; }
        .diagnostics-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 1rem; }
        .diag-hash { font-size: 0.7rem; word-break: break-all; font-family: monospace; }
      `}</style>
    </div>
  );
}
