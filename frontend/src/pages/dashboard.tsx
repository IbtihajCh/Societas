import { useEffect, useState } from 'react';
import { useSimulation } from '@/hooks/useSimulation';
import MetricsPanel from '@/components/dashboard/MetricsPanel';
import SimulationControls from '@/components/dashboard/SimulationControls';
import EventLog from '@/components/dashboard/EventLog';

/**
 * Dashboard Page
 * 
 * Main simulation dashboard with real-time metrics and controls.
 */
export default function Dashboard() {
  const { state, metrics, isConnected } = useSimulation();
  const [tick, setTick] = useState(0);

  useEffect(() => {
    // TODO: Connect to WebSocket for real-time updates
    // TODO: Fetch initial state and metrics
    
    return () => {
      // TODO: Cleanup WebSocket connection
    };
  }, []);

  return (
    <div style={{ padding: '2rem', fontFamily: 'system-ui' }}>
      <header style={{ marginBottom: '2rem' }}>
        <h1>SOCIETAS Dashboard</h1>
        <p>Status: {isConnected ? 'Connected' : 'Disconnected'}</p>
        <p>Current Tick: {tick}</p>
      </header>

      <SimulationControls />

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem', marginTop: '2rem' }}>
        <MetricsPanel metrics={metrics} />
        <EventLog />
      </div>

      <div style={{ marginTop: '2rem' }}>
        <h2>World State</h2>
        <pre>{JSON.stringify(state, null, 2)}</pre>
      </div>
    </div>
  );
}
