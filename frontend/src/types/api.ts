/**
 * API Types
 * 
 * TypeScript types for API responses.
 */

export interface SimulationStatus {
  isRunning: boolean;
  currentTick: number;
  population: number;
}

export interface SimulationState {
  tick: number;
  economy: EconomyState;
  crime: CrimeState;
  needs: NeedsState;
  psychology: PsychologyState;
}

export interface EconomyState {
  gdp: number;
  unemploymentRate: number;
  inflationRate: number;
  wealthDistribution: number[];
}

export interface CrimeState {
  crimeRate: number;
  enforcementEffectiveness: number;
  crimeTypes: Record<string, number>;
}

export interface NeedsState {
  averageNeeds: Record<string, number>;
  fulfillmentRates: Record<string, number>;
}

export interface PsychologyState {
  averageMorality: number;
  averageHappiness: number;
  averageStress: number;
  emotionalDistribution: Record<string, number>;
}

export interface Policy {
  id: string;
  name: string;
  description: string;
  category: string;
  weights: Record<string, number>;
  enactedAt: string;
  isActive: boolean;
}

export interface Agent {
  id: string;
  persona: string;
  traits: Record<string, number>;
  wealth: number;
  employmentStatus: string;
  happiness: number;
  health: number;
  lastActionTick: number;
  recentActions: AgentAction[];
}

export interface AgentAction {
  type: string;
  tick: number;
  details: any;
}

export interface Metrics {
  population: number;
  happiness: number;
  crimeRate: number;
  gdp: number;
  unemployment: number;
  inflation: number;
}
