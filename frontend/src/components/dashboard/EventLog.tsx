import React from 'react';
import { useSimulationStore } from '@/store/simulationStore';
import styles from './EventLog.module.css';

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
          events.slice(-50)
            .reverse()
            .map((ev, i) => (
              <div key={i} className={styles.eventRow}>
                <span className={styles.eventTick}>[T{ev.tick}]</span>
                <span className={styles.eventType}>{ev.event_type}</span>
                <span className={styles.eventDesc}>
                  {ev.event_type === 'agent_acted' && ev.data?.action
                    ? `Agent ${String(ev.data?.agent_id ?? '').slice(0, 8)}: ${ev.data.action}`
                    : ev.event_type === 'tick_completed'
                    ? `Tick ${ev.tick} complete (${ev.data?.duration_ms ?? 0}ms)`
                    : JSON.stringify(ev.data ?? {}).slice(0, 60)}
                </span>
              </div>
            ))
        )}
      </div>
    </div>
  );
};

export default EventLog;