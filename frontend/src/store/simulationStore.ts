import { create } from 'zustand';
import { SimulationEvent, ActionType, SimulationStateResponseDTO, AgentDetailDTO } from '@/types/api';
import { apiService } from '@/services/api';

/**
 * Historical data entry for simulation metrics per tick.
 */
export interface MetricsHistoryEntry {
  tick: number;
  economic_health: number;
  social_cohesion: number;
  crime_rate: number;
  protest_intensity: number;
  unemployment_rate: number;
  avg_unlust: number;
  morality: number;
  population: number;
}

/**
 * Action count entry per tick.
 */
export interface ActionHistoryEntry {
  tick: number;
  action_counts: Record<string, number>;
}

/**
 * Wealth class distribution entry per tick.
 */
export interface WealthStratifiedEntry {
  tick: number;
  poor: number;
  middle: number;
  rich: number;
}

const MAX_HISTORY = 100;

/**
 * Simulation Store
 * 
 * Zustand store for simulation state management and historical data tracking.
 */
export interface AgentAnimPosition {
  x: number;
  y: number;
}

interface SimulationStore {
  // State
  currentTick: number;
  isRunning: boolean;
  population: number;

  // Agent animation positions (grid coordinates, 0..gridSize)
  agentAnimPositions: Record<string, AgentAnimPosition>;
  agentTargetPositions: Record<string, AgentAnimPosition>;

  // Historical data
  metricsHistory: MetricsHistoryEntry[];
  actionHistory: ActionHistoryEntry[];
  wealthStratified: WealthStratifiedEntry[];

  // Snapshot fields (latest values from the current state)
  unlust: number;
  morality: number;
  food_availability: number;
  crime_rate: number;
  protest_intensity: number;
  unemployment_rate: number;
  tax_rate: number;
  welfare_enabled: boolean;
  welfare_amount: number;
  duration_ms: number;
  ai_calls: number;
  state_hash: string;

  // Events
  events: SimulationEvent[];
  llmLog: Array<{ tick: number; agent_id: string; model_type: string; action: string; reason: string; feeling: string }>;
  isAutoRunning: boolean;
  autoRunIntervalMs: number;

  // Selected agent detail panel state
  selectedAgent: AgentDetailDTO | null;
  selectedAgentId: string | null;

  // Actions
  setCurrentTick: (tick: number) => void;
  setIsRunning: (running: boolean) => void;
  setPopulation: (population: number) => void;
  reset: () => void;
  appendTickData: (state: SimulationStateResponseDTO) => void;
  updateAnimPositions: (targetPositions: Record<string, AgentAnimPosition>) => void;
  advanceAnimations: (deltaTime: number) => void;
  setAutoRun: (active: boolean, intervalMs?: number) => void;
  addEvent: (event: SimulationEvent) => void;
  clearEvents: () => void;
  setSelectedAgent: (agent: AgentDetailDTO | null) => void;
  setSelectedAgentId: (id: string | null) => void;
}

const ANIMATION_DURATION = 0.2; // seconds

export const useSimulationStore = create<SimulationStore>((set) => ({
  // Initial state
  currentTick: 0,
  isRunning: false,
  population: 0,

  // Agent animation positions
  agentAnimPositions: {},
  agentTargetPositions: {},

  // Historical data
  metricsHistory: [],
  actionHistory: [],
  wealthStratified: [],

  // Snapshot fields
  unlust: 0,
  morality: 0,
  food_availability: 0,
  crime_rate: 0,
  protest_intensity: 0,
  unemployment_rate: 0,
  tax_rate: 0,
  welfare_enabled: false,
  welfare_amount: 0,
  duration_ms: 0,
  ai_calls: 0,
  state_hash: '',

  // Events
  events: [],
  llmLog: [],
  isAutoRunning: false,
  autoRunIntervalMs: 1000,

  // Selected agent detail panel state
  selectedAgent: null,
  selectedAgentId: null,

  // Actions
  setCurrentTick: (tick) => set({ currentTick: tick }),
  setIsRunning: (running) => set({ isRunning: running }),
  setPopulation: (population) => set({ population }),

  appendTickData: (state) =>
    set((prev) => {
      const entry: MetricsHistoryEntry = {
        tick: state.tick,
        economic_health: state.economic_health,
        social_cohesion: state.social_cohesion,
        crime_rate: state.crime_rate,
        protest_intensity: state.protest_intensity,
        unemployment_rate: state.unemployment_rate,
        avg_unlust: state.unlust,
        morality: state.morality,
        population: state.population,
      };

      const metricsHistory = [...prev.metricsHistory, entry].slice(-MAX_HISTORY);

      let actionHistory = prev.actionHistory;
      if (state.action_counts) {
        const actionEntry: ActionHistoryEntry = {
          tick: state.tick,
          action_counts: state.action_counts,
        };
        actionHistory = [...prev.actionHistory, actionEntry].slice(-MAX_HISTORY);
      }

      let wealthStratified = prev.wealthStratified;
      if (state.wealth_stratified) {
        const wealthEntry: WealthStratifiedEntry = {
          tick: state.tick,
          poor: state.wealth_stratified.poor,
          middle: state.wealth_stratified.middle,
          rich: state.wealth_stratified.rich,
        };
        wealthStratified = [...prev.wealthStratified, wealthEntry].slice(-MAX_HISTORY);
      }

      let llmLog = prev.llmLog;
      if (state.llm_log && state.llm_log.length > 0) {
        llmLog = [...prev.llmLog, ...state.llm_log].slice(-200);
      }

      return {
        currentTick: state.tick,
        population: state.population,
        unlust: state.unlust,
        morality: state.morality,
        food_availability: state.food_availability,
        crime_rate: state.crime_rate,
        protest_intensity: state.protest_intensity,
        unemployment_rate: state.unemployment_rate,
        tax_rate: state.tax_rate,
        welfare_enabled: state.welfare_enabled,
        welfare_amount: state.welfare_amount,
        duration_ms: state.duration_ms,
        ai_calls: state.ai_calls,
        state_hash: state.state_hash,
        metricsHistory,
        actionHistory,
        wealthStratified,
        llmLog,
      };
    }),

  updateAnimPositions: (targetPositions) =>
    set((state) => {
      const nextCurrent: Record<string, AgentAnimPosition> = {};
      const nextTarget: Record<string, AgentAnimPosition> = {};

      for (const [id, target] of Object.entries(targetPositions)) {
        nextTarget[id] = { ...target };
        // Start new agents at their target so they don't snap from nowhere.
        nextCurrent[id] = state.agentAnimPositions[id]
          ? { ...state.agentAnimPositions[id] }
          : { ...target };
      }

      return {
        agentTargetPositions: nextTarget,
        agentAnimPositions: nextCurrent,
      };
    }),

  advanceAnimations: (deltaTime) =>
    set((state) => {
      const { agentAnimPositions, agentTargetPositions } = state;
      const next: Record<string, AgentAnimPosition> = {};
      const speed = 1 / ANIMATION_DURATION; // grid units per second
      let changed = false;

      for (const [id, target] of Object.entries(agentTargetPositions)) {
        const current = agentAnimPositions[id];
        if (!current) {
          next[id] = { ...target };
          changed = true;
          continue;
        }

        const dx = target.x - current.x;
        const dy = target.y - current.y;
        const maxStep = speed * deltaTime;

        if (Math.abs(dx) <= maxStep && Math.abs(dy) <= maxStep) {
          next[id] = { ...target };
          if (dx !== 0 || dy !== 0) changed = true;
        } else {
          const distance = Math.hypot(dx, dy) || 1;
          next[id] = {
            x: current.x + (dx / distance) * maxStep,
            y: current.y + (dy / distance) * maxStep,
          };
          changed = true;
        }
      }

      if (!changed) return state;
      return { agentAnimPositions: next };
    }),

  setAutoRun: (active: boolean, intervalMs: number = 1000) => {
    set({ isAutoRunning: active, autoRunIntervalMs: intervalMs });
    if (active) {
      apiService.autoRun({ active: true, interval_ms: intervalMs }).catch(console.error);
    } else {
      apiService.autoRun({ active: false }).catch(console.error);
    }
  },
  setSelectedAgent: (agent: AgentDetailDTO | null) => set({ selectedAgent: agent }),
  setSelectedAgentId: (id: string | null) => set({ selectedAgentId: id }),
  addEvent: (event: SimulationEvent) => {
    set((prev) => ({
      events: [...prev.events.slice(-200), event],
    }));
  },
  clearEvents: () => {
    set({ events: [] });
  },

  reset: () =>
    set({
      currentTick: 0,
      isRunning: false,
      population: 0,
      unlust: 0,
      morality: 0,
      food_availability: 0,
      crime_rate: 0,
      protest_intensity: 0,
      unemployment_rate: 0,
      tax_rate: 0,
      welfare_enabled: false,
      welfare_amount: 0,
      duration_ms: 0,
      ai_calls: 0,
      state_hash: '',
      agentAnimPositions: {},
      agentTargetPositions: {},
      metricsHistory: [],
      actionHistory: [],
      wealthStratified: [],
      events: [],
      llmLog: [],
      isAutoRunning: false,
      autoRunIntervalMs: 1000,
      selectedAgent: null,
      selectedAgentId: null,
    }),
}));
