import React, { useMemo } from 'react';
import { useSimulationStore } from '@/store/simulationStore';

export default function ModelLogPanel() {
  const llmLog = useSimulationStore((s) => s.llmLog);

  const entries = useMemo(() => llmLog.slice(-50).reverse(), [llmLog]);

  return (
    <div className="panel-inner">
      {entries.length === 0 ? (
        <div style={{ color: 'var(--ink-soft)', fontSize: '12px', padding: '20px 0', textAlign: 'center' }}>
          No LLM calls yet. Run with AI enabled to see model logs.
        </div>
      ) : (
        <div className="log-list">
          {entries.map((e, i) => (
            <div key={`${e.tick}-${e.agent_id}-${i}`} className="log-entry">
              <span className="tk">T{e.tick}</span>
              <span className="stamp" style={{
                fontSize: '9px', fontFamily: 'var(--font-mono)', padding: '2px 5px',
                textAlign: 'center', fontWeight: 600, border: '1px solid',
                color: e.model_type === 'moral' ? '#6d8aaa' : '#c54a3f',
                borderColor: e.model_type === 'moral' ? '#6d8aaa' : '#c54a3f',
                flex: '0 0 auto',
              }}>
                {e.model_type}
              </span>
              <span className="msg" style={{ flex: 1 }}>
                Agent <b>{e.agent_id?.slice(0, 8)}</b> → {e.action}
                <span style={{ color: 'var(--ink-soft)', display: 'block', fontSize: '10px', marginTop: '2px' }}>
                  {e.reason?.slice(0, 80)}{e.reason?.length > 80 ? '…' : ''}
                </span>
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
