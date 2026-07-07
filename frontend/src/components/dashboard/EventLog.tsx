import React from 'react';

/**
 * Event Log Component
 * 
 * Displays a scrollable log of simulation events.
 */
interface EventLogProps {
  events?: any[];
}

export default function EventLog({ events = [] }: EventLogProps) {
  // TODO: Display events in a scrollable list
  // TODO: Add filtering by event type
  // TODO: Add auto-scroll to latest event
  
  return (
    <div style={{ 
      padding: '1rem', 
      border: '1px solid #eaeaea', 
      borderRadius: '8px',
      backgroundColor: '#fafafa',
      maxHeight: '400px',
      overflowY: 'auto'
    }}>
      <h3>Event Log</h3>
      
      {events.length === 0 ? (
        <p style={{ color: '#999' }}>No events yet</p>
      ) : (
        <ul style={{ listStyle: 'none', padding: 0, marginTop: '1rem' }}>
          {events.map((event, index) => (
            <li 
              key={index}
              style={{
                padding: '0.5rem',
                borderBottom: '1px solid #eaeaea',
                fontSize: '0.9rem'
              }}
            >
              <strong>{event.type}</strong>: {event.description}
              <div style={{ color: '#999', fontSize: '0.8rem' }}>
                Tick {event.tick}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
