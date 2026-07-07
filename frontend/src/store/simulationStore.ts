import { create } from 'zustand';

/**
 * Simulation Store
 * 
 * Zustand store for simulation state management.
 */
interface SimulationStore {
  // State
  currentTick: number;
  isRunning: boolean;
  population: number;
  
  // Actions
  setCurrentTick: (tick: number) => void;
  setIsRunning: (running: boolean) => void;
  setPopulation: (population: number) => void;
  reset: () => void;
}

export const useSimulationStore = create<SimulationStore>((set) => ({
  // Initial state
  currentTick: 0,
  isRunning: false,
  population: 0,
  
  // Actions
  setCurrentTick: (tick) => set({ currentTick: tick }),
  setIsRunning: (running) => set({ isRunning: running }),
  setPopulation: (population) => set({ population }),
  reset: () => set({ currentTick: 0, isRunning: false, population: 0 }),
}));
