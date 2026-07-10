import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  useRef,
  ReactNode,
} from 'react';

import { apiService } from '@/services/api';
import {
  SimulationStateResponseDTO,
<<<<<<< HEAD
  MetricPointDTO,
  WebSocketMessage,
} from '@/types/api';
import {
  SimulationWebSocketClient,
  isTickCompleted,
  isAgentActed,
  ConnectionStatus,
} from '@/services/websocket';

export interface SimulationEvent {
  id: string;
  type: string;
  tick: number;
  description: string;
}

interface SimulationContextType {
  state: SimulationStateResponseDTO | null;
  metrics: MetricPointDTO[] | null;
  events: SimulationEvent[];
=======
  SimulationStatusDTO,
  AgentSummaryDTO,
} from '@/types/api';
import { useSimulationStore } from '@/store/simulationStore';

interface SimulationContextType {
  state: SimulationStateResponseDTO | null;
  agents: AgentSummaryDTO[];
>>>>>>> a2bd1d4 (v1-v6 complete: lifecycle, social systems, economy, self-actualization, governance UI, animated grid, LLM explainability, mock AI fallback, save/load, policy suggestions)
  isConnected: boolean;
  isRunning: boolean;
  error: string | null;
  startSimulation: () => Promise<void>;
  stopSimulation: () => Promise<void>;
  advanceTick: () => Promise<void>;
  refreshAgents: () => Promise<void>;
}

const MAX_EVENTS = 100;

const SimulationContext = createContext<SimulationContextType | undefined>(
  undefined,
);

interface SimulationProviderProps {
  children: ReactNode;
}

export function SimulationProvider({ children }: SimulationProviderProps) {
  const [state, setState] = useState<SimulationStateResponseDTO | null>(null);
<<<<<<< HEAD
  const [metrics, setMetrics] = useState<MetricPointDTO[] | null>(null);
  const [events, setEvents] = useState<SimulationEvent[]>([]);
=======
  const [agents, setAgents] = useState<AgentSummaryDTO[]>([]);
>>>>>>> a2bd1d4 (v1-v6 complete: lifecycle, social systems, economy, self-actualization, governance UI, animated grid, LLM explainability, mock AI fallback, save/load, policy suggestions)
  const [isConnected, setIsConnected] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const wsClientRef = useRef<SimulationWebSocketClient | null>(null);
  const eventCounter = useRef(0);

  const addEvent = useCallback((event: Omit<SimulationEvent, 'id'>) => {
    eventCounter.current += 1;
    const newEvent: SimulationEvent = {
      ...event,
      id: `evt-${eventCounter.current}`,
    };
    setEvents((prev) => [newEvent, ...prev].slice(0, MAX_EVENTS));
  }, []);

  const fetchAgents = useCallback(async () => {
    try {
      const res = await apiService.getAgents(20, 0);
      setAgents(res.agents);
    } catch {
      // ignore
    }
  }, []);

  useEffect(() => {
    const wsClient = new SimulationWebSocketClient();
    wsClientRef.current = wsClient;

    const unsubStatus = wsClient.onStatusChange((status: ConnectionStatus) => {
      setIsConnected(status === 'connected');
    });

    const unsubMessage = wsClient.onMessage((message: WebSocketMessage) => {
      if (isTickCompleted(message)) {
        setState((prev) => ({
          ...(prev ?? {
            tick: 0,
            population: 0,
            economic_health: 0.5,
            social_cohesion: 0.5,
            environmental_quality: 0.5,
            public_order: 0.5,
            innovation_index: 0.5,
            unlust: 0,
            morality: 0.5,
            food_availability: 0.85,
            water_availability: 0.9,
            crime_rate: 0.05,
            protest_intensity: 0,
            unemployment_rate: 0.1,
            tax_rate: 0.15,
            welfare_enabled: false,
            welfare_amount: 8,
          }),
          tick: message.tick,
          population: message.population,
        }));
        addEvent({
          type: 'tick_completed',
          tick: message.tick,
          description: `Tick ${message.tick} completed (${message.duration_ms?.toFixed(1)}ms, ${message.ambiguity_count} ambiguous, ${message.ai_calls} AI calls)`,
        });
      } else if (isAgentActed(message)) {
        addEvent({
          type: 'agent_acted',
          tick: state?.tick ?? 0,
          description: `Agent ${message.agent_id} → ${message.action}`,
        });
      }
    });

    wsClient.connect();

    const fetchStatus = async () => {
      try {
        const status = await apiService.getSimulationStatus();
        setIsConnected(true);
        setError(null);
        setIsRunning(status.is_running);
      } catch {
        setIsConnected(false);
      }
    };

    fetchStatus();
    fetchAgents();

    const interval = setInterval(async () => {
      try {
        await apiService.getHealth();
        setIsConnected(true);
      } catch {
        setIsConnected(false);
      }
    }, 30000);

<<<<<<< HEAD
    return () => {
      unsubStatus();
      unsubMessage();
      wsClient.disconnect();
      clearInterval(interval);
    };
  }, [addEvent, state?.tick]);

  const startSimulation = useCallback(async () => {
    try {
      setError(null);
      const status = await apiService.startSimulation({
        population_size: 80,
        seed: 42,
      });
      setIsRunning(status.is_running);
      setIsConnected(true);
      const simState = await apiService.getSimulationState();
      setState(simState);
      addEvent({
        type: 'simulation_started',
        tick: simState.tick,
        description: 'Simulation started',
      });
=======
    return () => clearInterval(interval);
  }, [fetchAgents]);

  // Poll agents every 2 seconds while simulation is running
  useEffect(() => {
    if (!isRunning) return;
    const interval = setInterval(() => {
      fetchAgents();
    }, 2000);
    return () => clearInterval(interval);
  }, [isRunning, fetchAgents]);

  const startSimulation = useCallback(async () => {
    try {
      const status = await apiService.startSimulation({ population_size: 20, seed: 42, enable_ai: true });
      setIsRunning(status.is_running);
      setIsConnected(true);
      if (status.population > 0) {
        const simState = await apiService.getSimulationState();
        setState(simState);
        useSimulationStore.getState().appendTickData(simState);
      }
      await fetchAgents();
>>>>>>> a2bd1d4 (v1-v6 complete: lifecycle, social systems, economy, self-actualization, governance UI, animated grid, LLM explainability, mock AI fallback, save/load, policy suggestions)
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Unknown error';
      setError(`Failed to start: ${msg}`);
      console.error('Failed to start simulation:', err);
    }
<<<<<<< HEAD
  }, [addEvent]);
=======
  }, [fetchAgents]);
>>>>>>> a2bd1d4 (v1-v6 complete: lifecycle, social systems, economy, self-actualization, governance UI, animated grid, LLM explainability, mock AI fallback, save/load, policy suggestions)

  const stopSimulation = useCallback(async () => {
    try {
      setError(null);
      const status = await apiService.stopSimulation();
      setIsRunning(status.is_running);
<<<<<<< HEAD
      addEvent({
        type: 'simulation_stopped',
        tick: state?.tick ?? 0,
        description: 'Simulation stopped',
      });
=======
      setState(null);
      setAgents([]);
      useSimulationStore.getState().reset();
>>>>>>> a2bd1d4 (v1-v6 complete: lifecycle, social systems, economy, self-actualization, governance UI, animated grid, LLM explainability, mock AI fallback, save/load, policy suggestions)
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Unknown error';
      setError(`Failed to stop: ${msg}`);
      console.error('Failed to stop simulation:', err);
    }
  }, [addEvent, state?.tick]);

  const advanceTick = useCallback(async () => {
    try {
      setError(null);
      const result = await apiService.advanceTick();
      setState(result);
      useSimulationStore.getState().appendTickData(result);
      await fetchAgents();
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Unknown error';
      setError(`Failed to advance tick: ${msg}`);
      console.error('Failed to advance tick:', err);
    }
  }, [fetchAgents]);

  return (
    <SimulationContext.Provider
      value={{
        state,
<<<<<<< HEAD
        metrics,
        events,
=======
        agents,
>>>>>>> a2bd1d4 (v1-v6 complete: lifecycle, social systems, economy, self-actualization, governance UI, animated grid, LLM explainability, mock AI fallback, save/load, policy suggestions)
        isConnected,
        isRunning,
        error,
        startSimulation,
        stopSimulation,
        advanceTick,
        refreshAgents: fetchAgents,
      }}
    >
      {children}
    </SimulationContext.Provider>
  );
}

export function useSimulationContext() {
  const context = useContext(SimulationContext);
  if (!context) {
    throw new Error(
      'useSimulationContext must be used within SimulationProvider',
    );
  }
  return context;
}
