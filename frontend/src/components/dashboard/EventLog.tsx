import React from 'react';
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
    </div>
  );
}
