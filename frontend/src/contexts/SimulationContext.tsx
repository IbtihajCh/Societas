import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';

import { apiService } from '@/services/api';
import {
  SimulationStateResponseDTO,
  SimulationStatusDTO,
  MetricPointDTO,
} from '@/types/api';

interface SimulationContextType {
  state: SimulationStateResponseDTO | null;
  metrics: MetricPointDTO[] | null;
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
  const [state, setState] = useState<SimulationStateResponseDTO | null>(null);
  const [metrics, setMetrics] = useState<MetricPointDTO[] | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isRunning, setIsRunning] = useState(false);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const status = await apiService.getSimulationStatus();
        setIsConnected(true);
        setIsRunning(status.is_running);

        const simState = await apiService.getSimulationState();
        setState(simState);

        const dashData = await apiService.getDashboardData();
        if (dashData.population) {
          setMetrics(dashData.population);
        }
      } catch {
        setIsConnected(false);
      }
    };

    fetchStatus();

    const interval = setInterval(async () => {
      try {
        await apiService.getHealth();
        setIsConnected(true);
      } catch {
        setIsConnected(false);
      }
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  const startSimulation = useCallback(async () => {
    try {
      const status = await apiService.startSimulation({ population_size: 80, seed: 42 });
      setIsRunning(status.is_running);
      setIsConnected(true);
      const simState = await apiService.getSimulationState();
      setState(simState);
    } catch (err) {
      console.error('Failed to start simulation:', err);
    }
  }, []);

  const stopSimulation = useCallback(async () => {
    try {
      const status = await apiService.stopSimulation();
      setIsRunning(status.is_running);
    } catch (err) {
      console.error('Failed to stop simulation:', err);
    }
  }, []);

  const advanceTick = useCallback(async () => {
    try {
      const result = await apiService.advanceTick();
      setState(result);
      if (result.tick % 10 === 0) {
        const status = await apiService.getSimulationStatus();
        setIsRunning(status.is_running);
      }
    } catch (err) {
      console.error('Failed to advance tick:', err);
    }
  }, []);

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
