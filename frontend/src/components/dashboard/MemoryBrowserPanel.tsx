import React, { useState, useMemo } from 'react';
import { useSimulationStore } from '@/store/simulationStore';

export default function MemoryBrowserPanel() {
  const llmLog = useSimulationStore((s) => s.llmLog);
  const [search, setSearch] = useState('');

  const filtered = useMemo(() => {
    if (!search.trim()) return llmLog.slice(-30).reverse();
    const q = search.toLowerCase();
    return llmLog.filter(e =>
      e.agent_id?.toLowerCase().includes(q) ||
      e.action?.toLowerCase().includes(q) ||
      e.reason?.toLowerCase().includes(q) ||
      e.feeling?.toLowerCase().includes(q),
    ).slice(-30).reverse();
  }, [llmLog, search]);

  return (
    <div className="panel-inner">
      <div className="explain-form" style={{ marginBottom: 10 }}>
        <input type="text" placeholder="Search agents, actions, reasons…"
          value={search} onChange={e => setSearch(e.target.value)} />
      </div>
      {filtered.length === 0 ? (
        <div style={{ color: 'var(--ink-soft)', fontSize: '12px', textAlign: 'center', padding: '16px 0' }}>
          {search ? 'No matching entries.' : 'No LLM memory entries yet.'}
        </div>
      ) : (
        <div className="log-list">
          {filtered.map((e, i) => (
            <div key={`mem-${e.tick}-${i}`} className="log-entry">
              <span className="tk">T{e.tick}</span>
              <span className="msg">
                <b>{e.agent_id?.slice(0, 8)}</b> → {e.action}
                <span style={{ display: 'block', color: 'var(--ink-soft)', fontSize: '10px', marginTop: 2 }}>
                  {e.reason?.slice(0, 90)}{e.reason?.length > 90 ? '…' : ''}
                </span>
                {e.feeling && (
                  <span style={{ display: 'block', color: 'var(--slate)', fontSize: '9px', marginTop: 1 }}>
                    feeling: {e.feeling}
                  </span>
                )}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
