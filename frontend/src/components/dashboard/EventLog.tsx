import React from 'react';
import { useSimulationStore } from '@/store/simulationStore';
import styles from './EventLog.module.css';

const EVENT_COLORS: Record<string, string> = {
  crime: 'var(--oxblood)',
  env_event: 'var(--ochre)',
  marriage: 'var(--moss)',
  tick_completed: 'var(--slate)',
};

function formatLabel(eventType: string): string {
  return eventType
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function describeEvent(data: Record<string, unknown>): string {
  const parts: string[] = [];
  if (typeof data.action === 'string' && data.action) {
    parts.push(data.action);
  }
  if (typeof data.agent_id === 'string' && data.agent_id) {
    parts.push(`Agent ${data.agent_id.slice(0, 8)}`);
  }
  if (typeof data.duration_ms === 'number') {
    parts.push(`${data.duration_ms}ms`);
  }
  return parts.join(' · ');
}

const EventLog: React.FC = () => {
  const events = useSimulationStore((s) => s.events);
  const clearEvents = useSimulationStore((s) => s.clearEvents);

  return (
    <div className={styles.panel}>
      <div className={styles.headerRow}>
        <h3 className={styles.title}>Event Log</h3>
        <button onClick={clearEvents} className={styles.clearBtn}>
          Clear
        </button>
      </div>
      <div className={styles.scrollArea}>
        {events.length === 0 ? (
          <p className={styles.empty}>No events yet. Run the simulation to see events.</p>
        ) : (
          events
            .slice(-50)
            .reverse()
            .map((ev) => (
              <div key={ev.id} className="event">
                <div
                  className="event-mark"
                  style={{
                    backgroundColor:
                      EVENT_COLORS[ev.event_type] ?? 'var(--ink-soft)',
                    borderRadius: '50%',
                  }}
                />
                <div className="event-text">
                  <b>{formatLabel(ev.event_type)}</b>
                  {describeEvent(ev.data) && (
                    <> — {describeEvent(ev.data)}</>
                  )}
                </div>
                <span className="event-time">T{ev.tick}</span>
              </div>
            ))
        )}
      </div>
    </div>
  );
};

export default EventLog;