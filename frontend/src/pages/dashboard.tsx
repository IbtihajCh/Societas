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
import Sparkline from '@/components/dashboard/Sparkline';
import WorldGauge from '@/components/dashboard/WorldGauge';
import styles from './dashboard.module.css';

export default function Dashboard() {
  const { state, agents, isConnected, isRunning, error, connectionFailed, retry, advanceTick, refreshAgents } =
    useSimulation();
  const isAutoRunning = useSimulationStore((s) => s.isAutoRunning);
  const setAutoRun = useSimulationStore((s) => s.setAutoRun);
  const metricsHistory = useSimulationStore((s) => s.metricsHistory);
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

  // ── Connection failed ──
  if (connectionFailed && !isConnected) {
    return (
      <div className={styles.loading}>
        <div className={styles.loadCrest}>✦</div>
        <h2 className={styles.loadingTitle}>Imperial Registry Unreachable</h2>
        <p className={styles.loadingDesc}>
          {error
            ? `Error: ${error}`
            : 'Cannot connect to the world simulation engine.'}
        </p>
        <p className={styles.loadingHint}>
          Ensure the backend is running at <code>localhost:8000</code>
        </p>
        <button onClick={retry} className={`${styles.btn} ${styles.btnPrimary}`}>
          Retry Connection
        </button>
      </div>
    );
  }

  // ── Loading initial connection ──
  if (!state && !isConnected) {
    return (
      <div className={styles.loading}>
        <div className={styles.loadingSpinner} />
        <p className={styles.loadingText}>Connecting to Imperial Registry…</p>
      </div>
    );
  }

  const econHist = metricsHistory.map((m) => m.economic_health);
  const cohesionHist = metricsHistory.map((m) => m.social_cohesion);
  const crimeHist = metricsHistory.map((m) => m.crime_rate);
  const unempHist = metricsHistory.map((m) => m.unemployment_rate);

  return (
    <div className={styles.worldMonitor}>
      {/* ── Imperial Masthead ── */}
      <div className={styles.masthead}>
        <div className={styles.mastheadLeft}>
          <span className={styles.mastheadSigil}>✦</span>
          <div>
            <h1 className={styles.mastheadTitle}>World Monitor</h1>
            <div className={styles.dateline}>
              {state?.population ?? 0} citizens on record — seed no. 42
              {tick > 0 && `  ·  cycle ${tick.toLocaleString()}`}
            </div>
          </div>
        </div>
        <div className={styles.controls}>
          <SimulationControls />
          <button
            onClick={() => setAutoRun(!isAutoRunning)}
            className={`${styles.btn} ${styles.btnQuiet}`}
          >
            {isAutoRunning ? '◼ Stop Auto' : '▶ Auto-Run'}
          </button>
        </div>
      </div>

      {/* ── Status Bar ── */}
      <div className={styles.statusBar}>
        <span className={styles.statusEntry}>
          <span
            className={`${styles.statusDot} ${
              isConnected ? styles.statusConnected : styles.statusDisconnected
            }`}
          />
          {isConnected ? 'Connected' : 'Disconnected'}
        </span>
        <span className={styles.statusDivider}>·</span>
        <span className={styles.statusEntry}>
          Entry no. <b>{tick.toLocaleString()}</b>
        </span>
        <span className={styles.statusDivider}>·</span>
        <span className={styles.statusEntry}>{isRunning ? 'Running' : 'Stopped'}</span>
        {state && state.ai_calls > 0 && (
          <>
            <span className={styles.statusDivider}>·</span>
            <span className={styles.statusEntry}>AI calls: {state.ai_calls}</span>
          </>
        )}
        {isRunning && (
          <>
            <span className={styles.statusDivider}>·</span>
            <span className={styles.statusAutoBtn} onClick={() => setAutoRun(!isAutoRunning)}>
              {isAutoRunning ? 'Auto-running' : 'Manual'}
            </span>
          </>
        )}
      </div>

      {error && <div className={styles.errorBanner}>{error}</div>}

      {!isConnected && state && (
        <div className={styles.disconnectedBanner}>
          Backend connection lost — showing last known state. Reconnecting…
        </div>
      )}

      {/* ── Imperial Stat Card Row ── */}
      <div className={styles.statCards}>
        <div className={styles.statCard}>
          <div className={styles.statCardHeader}>
            <span className={styles.statIcon}>◈</span>
            <span className={styles.statCardLabel}>Population</span>
          </div>
          <div className={styles.statCardValue}>{state?.population ?? '—'}</div>
          <div className={styles.statCardSpark}>
            <Sparkline data={metricsHistory.map((m) => m.population)} width={90} height={22} colorVar="--color-ink" />
          </div>
        </div>
        <div className={styles.statCard}>
          <div className={styles.statCardHeader}>
            <span className={styles.statIcon}>◆</span>
            <span className={styles.statCardLabel}>Economic Health</span>
          </div>
          <div className={styles.statCardValue}>{state ? state.economic_health.toFixed(2) : '—'}</div>
          <div className={styles.statCardSpark}>
            <Sparkline data={econHist} width={90} height={22} colorVar="--color-moss" />
          </div>
        </div>
        <div className={styles.statCard}>
          <div className={styles.statCardHeader}>
            <span className={styles.statIcon} style={{ color: 'var(--color-ochre)' }}>●</span>
            <span className={styles.statCardLabel}>Unemployment</span>
          </div>
          <div className={styles.statCardValue} style={{ color: 'var(--color-ochre)' }}>
            {state ? `${(state.unemployment_rate * 100).toFixed(0)}%` : '—'}
          </div>
          <div className={styles.statCardSpark}>
            <Sparkline data={unempHist} width={90} height={22} colorVar="--color-ochre" />
          </div>
        </div>
        <div className={styles.statCard}>
          <div className={styles.statCardHeader}>
            <span className={styles.statIcon} style={{ color: 'var(--color-oxblood)' }}>▲</span>
            <span className={styles.statCardLabel}>Crime Rate</span>
          </div>
          <div className={styles.statCardValue} style={{ color: 'var(--color-oxblood)' }}>
            {state ? `${(state.crime_rate * 100).toFixed(1)}%` : '—'}
          </div>
          <div className={styles.statCardSpark}>
            <Sparkline data={crimeHist} width={90} height={22} colorVar="--color-oxblood" />
          </div>
        </div>
        <div className={styles.statCard}>
          <div className={styles.statCardHeader}>
            <span className={styles.statIcon} style={{ color: 'var(--color-slate)' }}>◆</span>
            <span className={styles.statCardLabel}>Cohesion</span>
          </div>
          <div className={styles.statCardValue}>{state ? state.social_cohesion.toFixed(2) : '—'}</div>
          <div className={styles.statCardSpark}>
            <Sparkline data={cohesionHist} width={90} height={22} colorVar="--color-slate" />
          </div>
        </div>
        <div className={styles.statCard}>
          <div className={styles.statCardHeader}>
            <span className={styles.statIcon} style={{ color: 'var(--color-moss)' }}>❖</span>
            <span className={styles.statCardLabel}>Morality</span>
          </div>
          <div className={styles.statCardValue}>{state ? state.morality.toFixed(2) : '—'}</div>
        </div>
      </div>

      {/* ── Gauges Row ── */}
      {state && (
        <div className={styles.gaugeRow}>
          <div className={styles.gaugePanel}>
            <span className={styles.gaugePanelLabel}>World Indices</span>
            <div className={styles.gauges}>
              <WorldGauge value={state.economic_health} label="Economy" colorVar="--color-moss" />
              <WorldGauge value={state.social_cohesion} label="Cohesion" colorVar="--color-slate" />
              <WorldGauge value={state.morality} label="Morality" colorVar="--color-moss" />
              <WorldGauge value={state.food_availability} label="Food" colorVar="--color-ochre" />
              <WorldGauge value={state.water_availability} label="Water" colorVar="--color-slate" />
              <WorldGauge value={1 - state.crime_rate} label="Order" colorVar="--color-oxblood" displayValue={`${(state.crime_rate * 100).toFixed(0)}%`} />
              <WorldGauge value={1 - state.unemployment_rate} label="Employ" displayValue={`${(state.unemployment_rate * 100).toFixed(0)}%`} colorVar="--color-ochre" />
              <WorldGauge value={state.environmental_quality} label="Environ" colorVar="--color-moss" />
            </div>
          </div>
        </div>
      )}

      {/* ── Map + Chron. (left) & Chronicle Log (right) ── */}
      <div className={styles.layout}>
        {/* Left column */}
        <div className={styles.stack}>
          {/* ── Citizen Grid — World Map ── */}
          <div className={styles.section}>
            <div className={styles.sectionHeader}>
              <h2 className={styles.sectionTitle}>Citizen Grid — 20×20 World Map</h2>
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

          {/* ── Metrics + Time Series ── */}
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

      {/* ── Citizens Detail ── */}
      <div className={styles.section}>
        <h2 className={styles.sectionTitle}>Citizens</h2>
        <div className={styles.agentGrid}>
          {agents.slice(0, 20).map((a) => (
            <div
              key={a.id}
              className={styles.agentCard}
              style={{
                backgroundColor: a.is_alive ? 'var(--color-cream)' : '#f0e0e0',
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

      {/* ── Charts ── */}
      <div className={styles.section}>
        <ActionFrequencyChart />
      </div>
      <div className={styles.section}>
        <ActionDataSummary />
      </div>

      {/* ── LLM Panel ── */}
      <div className={styles.section}>
        <LLMPanel />
      </div>

      {/* ── World State JSON ── */}
      <div className={styles.section}>
        <h2 className={styles.sectionTitle}>World State — Raw Ledger</h2>
        <pre className={styles.worldStateJson}>
          {JSON.stringify(state, null, 2)}
        </pre>
      </div>
    </div>
  );
}