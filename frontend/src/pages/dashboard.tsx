import { useState, useEffect, useRef } from 'react';
import { useSimulation } from '@/hooks/useSimulation';
import { useSimulationStore } from '@/store/simulationStore';
import MetricsPanel from '@/components/dashboard/MetricsPanel';
import DiagnosticsPanel from '@/components/dashboard/DiagnosticsPanel';
import SimulationControls from '@/components/dashboard/SimulationControls';
import EventLog from '@/components/dashboard/EventLog';
import AgentGrid from '@/components/dashboard/AgentGrid';
import TimeSeriesChart from '@/components/dashboard/TimeSeriesChart';
import WealthStratifiedChart from '@/components/dashboard/WealthStratifiedChart';
import ActionFrequencyChart from '@/components/dashboard/ActionFrequencyChart';
import ActionDataSummary from '@/components/dashboard/ActionDataSummary';
import LLMPanel from '@/components/dashboard/LLMPanel';
import styles from './dashboard.module.css';

export default function Dashboard() {
  const { state, agents, isConnected, isRunning, error, advanceTick, refreshAgents } =
    useSimulation();
  const isAutoRunning = useSimulationStore((s) => s.isAutoRunning);
  const setAutoRun = useSimulationStore((s) => s.setAutoRun);
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
    <div>
      <div className={styles.masthead}>
        <div>
          <h1 className={styles.mastheadTitle}>World Overview</h1>
          <div className={styles.dateline}>
            {state?.population ?? 0} citizens on record — seed no. 42
          </div>
        </div>
        <div className={styles.controls}>
          <SimulationControls />
          <button
            onClick={() => setAutoRun(!isAutoRunning)}
            className={`${styles.btn} ${styles.btnQuiet}`}
          >
            {isAutoRunning ? 'Stop Auto' : 'Auto-Run'}
          </button>
        </div>
      </div>

      <div className={styles.subhead}>
        <span className={styles.entry}>
          <span
            className={`${styles.statusDot} ${
              isConnected ? styles.statusConnected : styles.statusDisconnected
            }`}
          />
          {isConnected ? 'Connected' : 'Disconnected'}
          {' | '}Entry no. <b>{tick.toLocaleString()}</b>
          {' | '}{isRunning ? 'Running' : 'Stopped'}
        </span>
      </div>

      {error && <div className={styles.errorBanner}>{error}</div>}

      {!isConnected && state && (
        <div className={styles.disconnectedBanner}>
          Backend connection lost — showing last known state. Reconnecting…
        </div>
      )}

      {/* Stat strip */}
      <div className={styles.statStrip}>
        <div className={styles.stat}>
          <div className={`${styles.statLabel} ${styles.sc}`}>Population</div>
          <div className={styles.statValue}>{state?.population ?? '—'}</div>
        </div>
        <div className={styles.stat}>
          <div className={`${styles.statLabel} ${styles.sc}`}>Economic Health</div>
          <div className={styles.statValue}>
            {state ? state.economic_health.toFixed(2) : '—'}
          </div>
        </div>
        <div className={styles.stat}>
          <div className={`${styles.statLabel} ${styles.sc}`}>Unemployment</div>
          <div className={styles.statValue} style={{ color: 'var(--color-ochre)' }}>
            {state ? `${(state.unemployment_rate * 100).toFixed(0)}%` : '—'}
          </div>
        </div>
        <div className={styles.stat}>
          <div className={`${styles.statLabel} ${styles.sc}`}>Crime Rate</div>
          <div className={styles.statValue} style={{ color: 'var(--color-oxblood)' }}>
            {state ? `${(state.crime_rate * 100).toFixed(1)}%` : '—'}
          </div>
        </div>
        <div className={styles.stat}>
          <div className={`${styles.statLabel} ${styles.sc}`}>Cohesion</div>
          <div className={styles.statValue}>
            {state ? state.social_cohesion.toFixed(2) : '—'}
          </div>
        </div>
        <div className={styles.stat}>
          <div className={`${styles.statLabel} ${styles.sc}`}>Morality Avg</div>
          <div className={styles.statValue}>
            {state ? state.morality.toFixed(2) : '—'}
          </div>
        </div>
      </div>

      {/* Main 2-col layout */}
      <div className={styles.layout}>
        {/* Left column */}
        <div className={styles.stack}>
          <MetricsPanel state={state} />
          <DiagnosticsPanel state={state} />
          <TimeSeriesChart />
        </div>

        {/* Right column */}
        <div className={styles.stack}>
          <EventLog />
          <WealthStratifiedChart />
        </div>
      </div>

      {/* Agent Grid */}
      <div className={styles.section}>
        <div className={styles.sectionHeader}>
          <h2 className={styles.sectionTitle}>Citizen Grid — 20×20 World</h2>
          <button
            type="button"
            onClick={() => setShowHeatmap((prev) => !prev)}
            className={`${styles.btn} ${styles.btnQuiet}`}
          >
            {showHeatmap ? 'Hide Heatmap' : 'Show Heatmap'}
          </button>
        </div>
        <AgentGrid
          agents={agents}
          gridSize={20}
          showHeatmap={showHeatmap}
          isRunning={isRunning}
          onRefresh={refreshAgents}
        />
      </div>

      {/* Action Frequency + Summary */}
      <div className={styles.section}>
        <ActionFrequencyChart />
      </div>
      <div className={styles.section}>
        <ActionDataSummary />
      </div>

      {/* LLM Panel */}
      <div className={styles.section}>
        <LLMPanel />
      </div>

      {/* Agent Details */}
      <div className={styles.section}>
        <h2 className={styles.sectionTitle}>Citizens</h2>
        <div className={styles.agentGrid}>
          {agents.slice(0, 20).map((a) => (
            <div
              key={a.id}
              className={styles.agentCard}
              style={{
                backgroundColor: a.is_alive ? 'var(--color-cream)' : '#fff0f0',
              }}
            >
              <strong>{a.persona || `Citizen #${a.id}`}</strong>
              <div className={styles.agentRow}>Mood: {a.emotion}</div>
              <div className={styles.agentRow}>Trade: {a.job_type}</div>
              <div className={styles.agentRow}>
                Unlust: {typeof a.unlust === 'number' ? a.unlust.toFixed(3) : a.unlust}
              </div>
              <div className={styles.agentRow}>Class: {a.wealth_class}</div>
              <div className={styles.agentRow}>
                Pos: ({a.grid_x}, {a.grid_y})
              </div>
              <div className={styles.agentRow}>
                {a.is_alive ? '✦ Alive' : '✗ Deceased'}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* World State */}
      <div className={styles.section}>
        <h2 className={styles.sectionTitle}>World State</h2>
        <pre className={styles.worldStateJson}>
          {JSON.stringify(state, null, 2)}
        </pre>
      </div>
    </div>
  );
}