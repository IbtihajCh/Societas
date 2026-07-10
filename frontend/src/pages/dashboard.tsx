<<<<<<< HEAD
=======
import { useState, useEffect, useRef } from 'react';
>>>>>>> a2bd1d4 (v1-v6 complete: lifecycle, social systems, economy, self-actualization, governance UI, animated grid, LLM explainability, mock AI fallback, save/load, policy suggestions)
import { useSimulation } from '@/hooks/useSimulation';
import { useSimulationStore } from '@/store/simulationStore';
import MetricsPanel from '@/components/dashboard/MetricsPanel';
import DiagnosticsPanel from '@/components/dashboard/DiagnosticsPanel';
import SimulationControls from '@/components/dashboard/SimulationControls';
import EventLog from '@/components/dashboard/EventLog';
<<<<<<< HEAD
import styles from './dashboard.module.css';

export default function Dashboard() {
  const { state, events, isConnected, isRunning, error } = useSimulation();
=======
import AgentGrid from '@/components/dashboard/AgentGrid';
import TimeSeriesChart from '@/components/dashboard/TimeSeriesChart';
import WealthStratifiedChart from '@/components/dashboard/WealthStratifiedChart';
import ActionFrequencyChart from '@/components/dashboard/ActionFrequencyChart';
import ActionDataSummary from '@/components/dashboard/ActionDataSummary';
import LLMPanel from '@/components/dashboard/LLMPanel';

export default function Dashboard() {
  const { state, agents, isConnected, isRunning, advanceTick, refreshAgents } = useSimulation();
  const isAutoRunning = useSimulationStore((s) => s.isAutoRunning);
  const setAutoRun = useSimulationStore((s) => s.setAutoRun);
>>>>>>> a2bd1d4 (v1-v6 complete: lifecycle, social systems, economy, self-actualization, governance UI, animated grid, LLM explainability, mock AI fallback, save/load, policy suggestions)
  const tick = state?.tick ?? 0;
  const [showHeatmap, setShowHeatmap] = useState(false);
  const autoRunRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (isAutoRunning) {
      autoRunRef.current = setInterval(() => {
        advanceTick();
      }, useSimulationStore.getState().autoRunIntervalMs);
    } else {
      if (autoRunRef.current) {
        clearInterval(autoRunRef.current);
        autoRunRef.current = null;
      }
    }
    return () => {
      if (autoRunRef.current) {
        clearInterval(autoRunRef.current);
        autoRunRef.current = null;
      }
    };
  }, [isAutoRunning, advanceTick]);

  if (!state && !isConnected) {
    return (
      <div className={styles.loading}>
        <div className={styles.loadingSpinner} />
        <p>Connecting to simulation backend…</p>
      </div>
    );
  }

  return (
<<<<<<< HEAD
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
=======
    <div style={{ padding: '2rem', fontFamily: 'system-ui' }}>
      <header style={{ marginBottom: '2rem' }}>
        <h1>SOCIETAS — Agent-Based Simulation</h1>
        <p>
          Status: <strong style={{ color: isConnected ? '#4caf50' : '#f44336' }}>
            {isConnected ? 'Connected' : 'Disconnected'}
          </strong>
          {' | '}Tick: <strong>{tick}</strong>
          {' | '}Population: <strong>{state?.population ?? 0}</strong>
        </p>
      </header>

      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <SimulationControls />
        <button
          onClick={() => setAutoRun(!isAutoRunning)}
          style={{
            padding: '0.4rem 0.8rem',
            fontSize: '0.85rem',
            borderRadius: '4px',
            border: '1px solid #ccc',
            background: isAutoRunning ? '#4caf50' : '#fff',
            color: isAutoRunning ? '#fff' : '#333',
            cursor: 'pointer',
          }}
        >
          {isAutoRunning ? 'Stop Auto' : 'Auto-Run'}
        </button>
      </div>

      {/* Top row: Metrics + Diagnostics + TimeSeries (left), EventLog + Wealth (right) */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem', marginTop: '2rem' }}>
        <div>
          <MetricsPanel state={state} />
          <div style={{ marginTop: '1rem' }}>
            <DiagnosticsPanel state={state} />
          </div>
          <div style={{ marginTop: '1rem' }}>
            <TimeSeriesChart />
          </div>
        </div>
        <div>
          <EventLog />
          <div style={{ marginTop: '1rem' }}>
            <WealthStratifiedChart />
          </div>
        </div>
      </div>

      {/* Agent Grid */}
      <div style={{ marginTop: '2rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '0.5rem' }}>
          <h2 style={{ margin: 0 }}>Agent Grid — 20×20 World</h2>
          <button
            type="button"
            onClick={() => setShowHeatmap((prev) => !prev)}
            style={{
              padding: '0.4rem 0.8rem',
              fontSize: '0.85rem',
              borderRadius: '4px',
              border: '1px solid #ccc',
              background: showHeatmap ? '#333' : '#fff',
              color: showHeatmap ? '#fff' : '#333',
              cursor: 'pointer',
            }}
          >
            {showHeatmap ? 'Hide Heatmap' : 'Show Heatmap'}
          </button>
        </div>
        <AgentGrid agents={agents} gridSize={20} showHeatmap={showHeatmap} isRunning={isRunning} onRefresh={refreshAgents} />
      </div>

      {/* Action Frequency Chart */}
      <div style={{ marginTop: '2rem' }}>
        <ActionFrequencyChart />
      </div>

      {/* Action Data Summary */}
      <div style={{ marginTop: '2rem' }}>
        <ActionDataSummary />
      </div>

      {/* Agent Details */}
      <div style={{ marginTop: '2rem' }}>
        <h2>Agent Details</h2>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
          {agents.slice(0, 20).map((a) => (
            <div key={a.id} style={{
              padding: '0.5rem',
              border: '1px solid #eaeaea',
              borderRadius: '6px',
              fontSize: '0.8rem',
              width: '180px',
              backgroundColor: a.is_alive ? '#f9fff9' : '#fff0f0'
            }}>
              <strong>{a.persona || `Agent ${a.id}`}</strong>
              <div>Emotion: {a.emotion}</div>
              <div>Job: {a.job_type}</div>
              <div>Unlust: {typeof a.unlust === 'number' ? a.unlust.toFixed(3) : a.unlust}</div>
              <div>Class: {a.wealth_class}</div>
              <div>Pos: ({a.grid_x}, {a.grid_y})</div>
              <div>{a.is_alive ? '✅ Alive' : '💀 Dead'}</div>
            </div>
          ))}
        </div>
>>>>>>> a2bd1d4 (v1-v6 complete: lifecycle, social systems, economy, self-actualization, governance UI, animated grid, LLM explainability, mock AI fallback, save/load, policy suggestions)
      </div>
    </div>
  );
}
