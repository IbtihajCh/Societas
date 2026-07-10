import { useSimulation } from '@/hooks/useSimulation';
import MetricsPanel from '@/components/dashboard/MetricsPanel';
import SimulationControls from '@/components/dashboard/SimulationControls';
import EventLog from '@/components/dashboard/EventLog';
import styles from './dashboard.module.css';

export default function Dashboard() {
  const { state, events, isConnected, isRunning, error } = useSimulation();
  const tick = state?.tick ?? 0;

  if (!state && !isConnected) {
    return (
      <div className={styles.loading}>
        <div className={styles.loadingSpinner} />
        <p>Connecting to simulation backend…</p>
      </div>
    );
  }

  return (
    <div className={styles.dashboard}>
      <header className={styles.header}>
        <h1 className={styles.title}>SOCIETAS Dashboard</h1>
        <div className={styles.statusBar}>
          <span>
            <span
              className={`${styles.statusDot} ${isConnected ? styles.statusConnected : styles.statusDisconnected}`}
            />
            {isConnected ? 'Connected' : 'Disconnected'}
          </span>
          <span className={styles.tickInfo}>
            Tick: {tick} | {isRunning ? 'Running' : 'Stopped'}
          </span>
        </div>
      </header>

      {error && (
        <div className={styles.errorBanner}>
          {error}
        </div>
      )}

      {!isConnected && state && (
        <div className={styles.disconnectedBanner}>
          Backend connection lost — showing last known state. Reconnecting…
        </div>
      )}

      <SimulationControls />

      <div className={styles.grid}>
        <MetricsPanel state={state} />
        <EventLog events={events} />
      </div>

      <div className={styles.worldState}>
        <h2>World State</h2>
        <pre className={styles.worldStateJson}>
          {JSON.stringify(state, null, 2)}
        </pre>
      </div>
    </div>
  );
}
