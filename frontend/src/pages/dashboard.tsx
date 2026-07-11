import { useState, useEffect, useRef } from 'react';
import { useSimulation } from '@/hooks/useSimulation';
import { useSimulationStore } from '@/store/simulationStore';
import { apiService } from '@/services/api';
import { AgentDetailDTO } from '@/types/api';
import MetricsPanel from '@/components/dashboard/MetricsPanel';
import DiagnosticsPanel from '@/components/dashboard/DiagnosticsPanel';
import SimulationControls from '@/components/dashboard/SimulationControls';
import EventLog from '@/components/dashboard/EventLog';
import AgentGrid from '@/components/dashboard/AgentGrid';
import AgentDetailPanel from '@/components/dashboard/AgentDetailPanel';
import TimeSeriesChart from '@/components/dashboard/TimeSeriesChart';
import WealthStratifiedChart from '@/components/dashboard/WealthStratifiedChart';
import ActionFrequencyChart from '@/components/dashboard/ActionFrequencyChart';
import ActionDataSummary from '@/components/dashboard/ActionDataSummary';
import LLMPanel from '@/components/dashboard/LLMPanel';

export default function Dashboard() {
  const { state, agents, isConnected, isRunning, error, advanceTick, refreshAgents } =
    useSimulation();
  const isAutoRunning = useSimulationStore((s) => s.isAutoRunning);
  const setAutoRun = useSimulationStore((s) => s.setAutoRun);
  const tick = state?.tick ?? 0;
  const [showHeatmap, setShowHeatmap] = useState(false);
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null);
  const [selectedAgent, setSelectedAgent] = useState<AgentDetailDTO | null>(null);
  const autoRunRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (!selectedAgentId) {
      setSelectedAgent(null);
      return;
    }
    let cancelled = false;
    apiService.getAgentDetail(selectedAgentId).then((agent) => {
      if (!cancelled) setSelectedAgent(agent);
    });
    return () => {
      cancelled = true;
    };
  }, [selectedAgentId]);

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
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '300px',
          gap: '1rem',
        }}
      >
        <div
          style={{
            width: '40px',
            height: '40px',
            border: '3px solid #e0e0e0',
            borderTopColor: '#0070f3',
            borderRadius: '50%',
            animation: 'spin 0.8s linear infinite',
          }}
        />
        <p>Connecting to simulation backend…</p>
        <style>{`@keyframes spin{to{transform:rotate(360deg)}}`}</style>
      </div>
    );
  }

  return (
    <div style={{ padding: '2rem', fontFamily: 'system-ui' }}>
      <header style={{ marginBottom: '2rem' }}>
        <h1>SOCIETAS — Agent-Based Simulation</h1>
        <p>
          <span
            style={{
              display: 'inline-block',
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              backgroundColor: isConnected ? '#16a34a' : '#dc2626',
              marginRight: '6px',
            }}
          />
          Status: <strong>{isConnected ? 'Connected' : 'Disconnected'}</strong>
          {' | '}Tick: <strong>{tick}</strong>
          {' | '}Population: <strong>{state?.population ?? 0}</strong>
          {' | '}
          {isRunning ? 'Running' : 'Stopped'}
        </p>
      </header>

      {error && (
        <div
          style={{
            backgroundColor: '#fef2f2',
            border: '1px solid #fecaca',
            borderRadius: '8px',
            padding: '1rem',
            marginBottom: '2rem',
            color: '#dc2626',
            fontSize: '0.875rem',
          }}
        >
          {error}
        </div>
      )}

      {!isConnected && state && (
        <div
          style={{
            backgroundColor: '#fffbeb',
            border: '1px solid #fde68a',
            borderRadius: '8px',
            padding: '1rem',
            marginBottom: '2rem',
            color: '#f59e0b',
            fontSize: '0.875rem',
          }}
        >
          Backend connection lost — showing last known state. Reconnecting…
        </div>
      )}

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
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: '2rem',
          marginTop: '2rem',
        }}
      >
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
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '1rem',
            marginBottom: '0.5rem',
          }}
        >
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
        <AgentGrid
          agents={agents}
          gridSize={20}
          showHeatmap={showHeatmap}
          isRunning={isRunning}
          onRefresh={refreshAgents}
          onAgentClick={(id) => setSelectedAgentId(id)}
        />
      </div>

      {/* Action Frequency Chart */}
      <div style={{ marginTop: '2rem' }}>
        <ActionFrequencyChart />
      </div>

      {/* Action Data Summary */}
      <div style={{ marginTop: '2rem' }}>
        <ActionDataSummary />
      </div>

      {/* LLM Panel */}
      <div style={{ marginTop: '2rem' }}>
        <LLMPanel />
      </div>

      {/* Agent Details */}
      <div style={{ marginTop: '2rem' }}>
        <h2>Agent Details</h2>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
          {agents.slice(0, 20).map((a) => (
            <div
              key={a.id}
              style={{
                padding: '0.5rem',
                border: '1px solid #eaeaea',
                borderRadius: '6px',
                fontSize: '0.8rem',
                width: '180px',
                backgroundColor: a.is_alive ? '#f9fff9' : '#fff0f0',
              }}
            >
              <strong>{a.persona || `Agent ${a.id}`}</strong>
              <div>Emotion: {a.emotion}</div>
              <div>Job: {a.job_type}</div>
              <div>
                Unlust:{' '}
                {typeof a.unlust === 'number'
                  ? a.unlust.toFixed(3)
                  : a.unlust}
              </div>
              <div>Class: {a.wealth_class}</div>
              <div>
                Pos: ({a.grid_x}, {a.grid_y})
              </div>
              <div>{a.is_alive ? '✅ Alive' : '💀 Dead'}</div>
            </div>
          ))}
        </div>
      </div>

      {/* World State */}
      <div style={{ marginTop: '2rem' }}>
        <h2>World State</h2>
        <pre
          style={{
            backgroundColor: '#fff',
            border: '1px solid #eaeaea',
            borderRadius: '4px',
            padding: '1rem',
            overflow: 'auto',
            fontSize: '0.875rem',
            maxHeight: '400px',
          }}
        >
          {JSON.stringify(state, null, 2)}
        </pre>
      </div>

      {/* Agent Detail Panel */}
      {selectedAgent && (
        <AgentDetailPanel
          agent={selectedAgent}
          onClose={() => {
            setSelectedAgentId(null);
            setSelectedAgent(null);
          }}
        />
      )}
    </div>
  );
}