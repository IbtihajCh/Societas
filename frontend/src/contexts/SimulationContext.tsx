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
  AgentSummaryDTO,
  WebSocketMessage,
} from '@/types/api';
import {
  SimulationWebSocketClient,
  isTickCompleted,
  isAgentActed,
  ConnectionStatus,
} from '@/services/websocket';
import { useSimulationStore } from '@/store/simulationStore';

interface SimulationContextType {
  state: SimulationStateResponseDTO | null;
  agents: AgentSummaryDTO[];
  isConnected: boolean;
  isRunning: boolean;
  error: string | null;
  connectionFailed: boolean;
  retry: () => void;
  startSimulation: () => Promise<void>;
  stopSimulation: () => Promise<void>;
  advanceTick: () => Promise<void>;
  refreshAgents: () => Promise<void>;
}

const SimulationContext = createContext<SimulationContextType | undefined>(
  undefined,
);

interface SimulationProviderProps {
  children: ReactNode;
}

export function SimulationProvider({ children }: SimulationProviderProps) {
  const [state, setState] = useState<SimulationStateResponseDTO | null>(null);
  const [agents, setAgents] = useState<AgentSummaryDTO[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [connectionFailed, setConnectionFailed] = useState(false);
  const [retryCount, setRetryCount] = useState(0);

  const wsClientRef = useRef<SimulationWebSocketClient | null>(null);
  const stateRef = useRef<SimulationStateResponseDTO | null>(null);
  stateRef.current = state;

  const fetchAgents = useCallback(async () => {
    try {
      const res = await apiService.getAgents(80, 0);
      setAgents(res.agents);
    } catch {
      // ignore
    }
  }, []);

  useEffect(() => {
    const wsClient = new SimulationWebSocketClient();
    wsClientRef.current = wsClient;

    const unsubStatus = wsClient.onStatusChange((status: ConnectionStatus) => {
      // Don't let WS status override HTTP-based isConnected.
      // WS is for real-time push; HTTP health is the source of truth for connection.
      if (status === 'connected') {
        setIsConnected(true);
      }
      // 'connecting' and 'disconnected' do NOT set isConnected=false —
      // the HTTP health poll handles that.
    });

    const unsubMessage = wsClient.onMessage(async (message: WebSocketMessage) => {
      const store = useSimulationStore.getState();
      if (isTickCompleted(message)) {
        store.addEvent({
          id: `ws-tc-${message.tick}`,
          tick: message.tick,
          event_type: 'tick_completed',
          data: {
            duration_ms: message.duration_ms,
            population: message.population,
            ambiguity_count: message.ambiguity_count,
            ai_calls: message.ai_calls,
          },
        });
        try {
          const simState = await apiService.getSimulationState();
          setState(simState);
          store.appendTickData(simState);
        } catch {
          // ignore fetch errors on WS push
        }
      } else if (isAgentActed(message)) {
        store.addEvent({
          id: `ws-aa-${message.agent_id}-${Date.now()}`,
          tick: stateRef.current?.tick ?? 0,
          event_type: 'agent_acted',
          data: {
            agent_id: message.agent_id,
            action: message.action,
          },
        });
      }
    });

    wsClient.connect();

    const fetchStatus = async () => {
      try {
        const status = await apiService.getSimulationStatus();
        setIsConnected(true);
        setConnectionFailed(false);
        setError(null);
        setIsRunning(status.is_running);
        if (status.population > 0) {
          const simState = await apiService.getSimulationState();
          setState(simState);
          useSimulationStore.getState().appendTickData(simState);
        }
        await fetchAgents();
      } catch (err) {
        setIsConnected(false);
        setConnectionFailed(true);
        const msg = err instanceof Error ? err.message : 'Unknown error';
        setError(msg);
      }
    };

    fetchStatus();

    // Immediate health check, then poll every 10s (not 30s)
    apiService.getHealth().then(() => setIsConnected(true)).catch(() => {});

    const interval = setInterval(async () => {
      try {
        await apiService.getHealth();
        setIsConnected(true);
        setConnectionFailed(false);
      } catch {
        setIsConnected(false);
      }
    }, 10000);

    return () => {
      unsubStatus();
      unsubMessage();
      wsClient.disconnect();
      clearInterval(interval);
    };
  }, [fetchAgents, retryCount]);

  useEffect(() => {
    if (!isRunning) return;
    const interval = setInterval(() => {
      fetchAgents();
    }, 2000);
    return () => clearInterval(interval);
  }, [isRunning, fetchAgents]);

  const startSimulation = useCallback(async () => {
    try {
      setError(null);
      useSimulationStore.getState().reset();
      const status = await apiService.startSimulation({
        population_size: 80,
        seed: 42,
        enable_ai: true,
      });
      setIsRunning(status.is_running);
      setIsConnected(true);
      if (status.population > 0) {
        const simState = await apiService.getSimulationState();
        setState(simState);
        useSimulationStore.getState().appendTickData(simState);
      }
      await fetchAgents();
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Unknown error';
      setError(`Failed to start: ${msg}`);
      console.error('Failed to start simulation:', err);
    }
  }, [fetchAgents]);

  const stopSimulation = useCallback(async () => {
    try {
      setError(null);
      const status = await apiService.stopSimulation();
      setIsRunning(status.is_running);
      setState(null);
      setAgents([]);
      useSimulationStore.getState().reset();
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Unknown error';
      setError(`Failed to stop: ${msg}`);
      console.error('Failed to stop simulation:', err);
    }
  }, []);

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

  const retry = useCallback(() => {
    setError(null);
    setConnectionFailed(false);
    setRetryCount((c) => c + 1);
  }, []);

  return (
    <SimulationContext.Provider
      value={{
        state,
        agents,
        isConnected,
        isRunning,
        error,
        connectionFailed,
        retry,
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