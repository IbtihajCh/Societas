import React, { useMemo } from 'react';
import { useSimulationStore } from '@/store/simulationStore';

const EVENT_ICONS: Record<string, string> = {
  env_event: '\u{1F300}', crime: '\u{1F4A2}', marriage: '\u{1F48D}',
  death: '\u{26B0}\uFE0F', birth: '\u{1F476}', protest: '\u{1F6A9}',
  tick_completed: '\u{23F3}',
};

export default function EnvironmentalEventsPanel() {
  const events = useSimulationStore((s) => s.events);

  const envEntries = useMemo(
    () => events.filter(e => e.event_type !== 'tick_completed').slice(-30).reverse(),
    [events],
  );

  if (envEntries.length === 0) {
    return (
      <div className="panel-inner" style={{ textAlign: 'center', color: 'var(--ink-soft)', fontSize: '12px', padding: '30px 14px' }}>
        No environmental or social events yet.
      </div>
    );
  }

  return (
    <div className="panel-inner">
      <div className="log-list">
        {envEntries.map((e) => (
          <div key={e.id} className={`log-entry ${e.event_type === 'crime' ? 'crime' : e.event_type === 'env_event' ? 'economy' : 'social'}`}>
            <span className="tk">
              {EVENT_ICONS[e.event_type] ?? '\u{2753}'} T{e.tick}
            </span>
            <span className="msg">
              <b>{e.event_type.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}</b>
              {typeof e.data?.action === 'string' && <> — {e.data.action}</>}
              {typeof e.data?.agent_id === 'string' && <> — Agent {e.data.agent_id.slice(0, 8)}</>}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
