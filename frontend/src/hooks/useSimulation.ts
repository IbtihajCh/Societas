import { useSimulationContext } from '@/contexts/SimulationContext';

/**
 * useSimulation Hook
 * 
 * Custom hook for accessing simulation state and actions.
 */
export function useSimulation() {
  return useSimulationContext();
}
