import { createContext, useContext, useState, useEffect, ReactNode } from 'react';

/**
 * Simulation Context
 * 
 * Provides global simulation state and actions.
 */
interface SimulationContextType {
  state: any;
  metrics: any;
  isConnected: boolean;
  isRunning: boolean;
  startSimulation: () => Promise<void>;
  stopSimulation: () => Promise<void>;
  advanceTick: () => Promise<void>;
}

const SimulationContext = createContext<SimulationContextType | undefined>(undefined);

interface SimulationProviderProps {
  children: ReactNode;
}

export function SimulationProvider({ children }: SimulationProviderProps) {
  const [state, setState] = useState<any>(null);
  const [metrics, setMetrics] = useState<any>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isRunning, setIsRunning] = useState(false);

  useEffect(() => {
    // TODO: Connect to WebSocket
    // TODO: Fetch initial state
    
    return () => {
      // TODO: Cleanup WebSocket connection
    };
  }, []);

  const startSimulation = async () => {
    // TODO: Call API to start simulation
    setIsRunning(true);
  };

  const stopSimulation = async () => {
    // TODO: Call API to stop simulation
    setIsRunning(false);
  };

  const advanceTick = async () => {
    // TODO: Call API to advance tick
  };

  return (
    <SimulationContext.Provider
      value={{
        state,
        metrics,
        isConnected,
        isRunning,
        startSimulation,
        stopSimulation,
        advanceTick,
      }}
    >
      {children}
    </SimulationContext.Provider>
  );
}

export function useSimulationContext() {
  const context = useContext(SimulationContext);
  if (!context) {
    throw new Error('useSimulationContext must be used within SimulationProvider');
  }
  return context;
}
