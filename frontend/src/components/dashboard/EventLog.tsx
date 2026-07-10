import React from 'react';
<<<<<<< HEAD
import { SimulationEvent } from '@/contexts/SimulationContext';
import styles from './EventLog.module.css';

interface EventLogProps {
  events: SimulationEvent[];
}

export default function EventLog({ events }: EventLogProps) {
  return (
    <div className={styles.panel}>
      <h3 className={styles.title}>Event Log</h3>

      {events.length === 0 ? (
        <p className={styles.empty}>No events yet</p>
      ) : (
        <ul className={styles.list}>
          {events.map((event) => (
            <li
              key={event.id}
              className={`${styles.eventItem} ${styles[`event${event.type.charAt(0).toUpperCase() + event.type.slice(1)}`] || ''}`}
            >
              <span className={styles.eventType}>{event.type}</span>
              <span className={styles.eventDescription}> — {event.description}</span>
              <div className={styles.eventTick}>Tick {event.tick}</div>
            </li>
          ))}
        </ul>
      )}
=======
import { useSimulationStore } from '@/store/simulationStore';
import { SimulationEvent } from '@/types/api';

const EventLog: React.FC = () => {
  const events = useSimulationStore((s) => s.events);
  const clearEvents = useSimulationStore((s) => s.clearEvents);

  return (
    <div className="bg-gray-800 rounded-lg p-4">
      <div className="flex justify-between items-center mb-2">
        <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">Event Log</h3>
        <button
          onClick={clearEvents}
          className="text-xs text-gray-500 hover:text-white"
        >
          Clear
        </button>
      </div>
      <div className="h-48 overflow-y-auto space-y-1 text-xs">
        {events.length === 0 ? (
          <p className="text-gray-500 italic">No events yet. Run the simulation to see events.</p>
        ) : (
          events.slice(-50).reverse().map((ev, i) => (
            <div key={i} className="flex gap-2 text-gray-400">
              <span className="text-gray-600 shrink-0">[T{ev.tick}]</span>
              <span className="text-cyan-400 shrink-0">{ev.event_type}</span>
              <span className="truncate">
                {ev.event_type === 'agent_acted' && ev.data?.action
                  ? `Agent ${ev.data?.agent_id?.toString().slice(0, 8)}: ${ev.data.action}`
                  : ev.event_type === 'tick_completed'
                  ? `Tick ${ev.tick} complete (${ev.data?.duration_ms ?? 0}ms)`
                  : JSON.stringify(ev.data ?? {}).slice(0, 60)}
              </span>
            </div>
          ))
        )}
      </div>
>>>>>>> a2bd1d4 (v1-v6 complete: lifecycle, social systems, economy, self-actualization, governance UI, animated grid, LLM explainability, mock AI fallback, save/load, policy suggestions)
    </div>
  );
};

export default EventLog;
