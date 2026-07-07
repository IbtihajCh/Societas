/**
 * API Types
 *
 * TypeScript types for SOCIETAS API responses.
 * Mirrors the canonical Python DTOs in shared/dto/* (snake_case, as-is).
 * Source of truth: shared/dto/*.py — keep in sync.
 */

// ---------------------------------------------------------------------------
// Enums (mirror shared/types/enums.py)
// ---------------------------------------------------------------------------

export enum PolicyCategory {
  ECONOMIC = 'ECONOMIC',
  SOCIAL = 'SOCIAL',
  ENVIRONMENTAL = 'ENVIRONMENTAL',
  PUBLIC_ORDER = 'PUBLIC_ORDER',
  EDUCATION = 'EDUCATION',
  HEALTHCARE = 'HEALTHCARE',
  INFRASTRUCTURE = 'INFRASTRUCTURE',
  CULTURAL = 'CULTURAL',
}

export enum ActionType {
  WORK = 'WORK',
  LEISURE = 'LEISURE',
  SOCIALIZE = 'SOCIALIZE',
  CONSUME = 'CONSUME',
  SAVE = 'SAVE',
  INVEST = 'INVEST',
  EDUCATE = 'EDUCATE',
  REST = 'REST',
  MIGRATE = 'MIGRATE',
  PROTEST = 'PROTEST',
  COMMIT_CRIME = 'COMMIT_CRIME',
  VOLUNTEER = 'VOLUNTEER',
  IDLE = 'IDLE',
}

export enum EmploymentStatus {
  EMPLOYED = 'EMPLOYED',
  UNEMPLOYED = 'UNEMPLOYED',
  STUDENT = 'STUDENT',
  RETIRED = 'RETIRED',
  UNABLE_TO_WORK = 'UNABLE_TO_WORK',
}

export enum WealthClass {
  POOR = 'POOR',
  WORKING = 'WORKING',
  MIDDLE = 'MIDDLE',
  UPPER_MIDDLE = 'UPPER_MIDDLE',
  WEALTHY = 'WEALTHY',
  ELITE = 'ELITE',
}

// ---------------------------------------------------------------------------
// Simulation DTOs (mirror shared/dto/simulation_dto.py)
// ---------------------------------------------------------------------------

export interface SimulationStatusDTO {
  tick: number;
  is_running: boolean;
  speed: number;
  population: number;
}

export interface SimulationStartRequestDTO {
  population_size?: number;
  seed?: number | null;
  speed?: number;
  config?: Record<string, unknown>;
}

export interface SimulationStateResponseDTO {
  tick: number;
  population: number;
  economic_health: number;
  social_cohesion: number;
  environmental_quality: number;
  public_order: number;
  innovation_index: number;
  unlust: number;
  morality: number;
}

// ---------------------------------------------------------------------------
// Policy DTOs (mirror shared/dto/policy_dto.py)
// ---------------------------------------------------------------------------

export interface PolicyCreateRequestDTO {
  name: string;
  description: string;
  category: PolicyCategory;
  weights?: Record<string, number>;
}

export interface PolicyResponseDTO {
  id: string;
  name: string;
  description: string;
  category: PolicyCategory;
  weights: Record<string, number>;
  is_active: boolean;
  enactment_tick: number;
}

export interface PolicyListResponseDTO {
  policies: PolicyResponseDTO[];
  total: number;
}

// ---------------------------------------------------------------------------
// Agent DTOs (mirror shared/dto/agent_dto.py)
// ---------------------------------------------------------------------------

export interface AgentSummaryDTO {
  id: string;
  persona: string;
  wealth_class: WealthClass;
  employment_status: EmploymentStatus;
  age: number;
  is_alive: boolean;
}

export interface AgentDetailDTO {
  id: string;
  persona: string;
  traits: Record<string, number>;
  needs: Record<string, number>;
  emotions: Record<string, number>;
  resources: Record<string, number>;
  employment_status: EmploymentStatus;
  wealth_class: WealthClass;
  age: number;
  location: string;
  last_action: ActionType | null;
  social_connections: number;
}

export interface AgentListResponseDTO {
  agents: AgentSummaryDTO[];
  total: number;
  page: number;
  page_size: number;
}

// ---------------------------------------------------------------------------
// Metrics DTOs (mirror shared/dto/metrics_dto.py)
// ---------------------------------------------------------------------------

export interface MetricPointDTO {
  tick: number;
  value: number;
}

export interface MetricsResponseDTO {
  current_tick: number;
  population: MetricPointDTO[];
  economy: MetricPointDTO[];
  crime: MetricPointDTO[];
  happiness: MetricPointDTO[];
  summary: Record<string, number>;
}

// ---------------------------------------------------------------------------
// Health
// ---------------------------------------------------------------------------

export interface HealthResponse {
  status: 'healthy' | 'unhealthy';
  service?: string;
  version?: string;
  timestamp?: string;
}

// ---------------------------------------------------------------------------
// Simulation events (mirror shared/events/simulation_events.py)
// Used by the WebSocket message handler.
// ---------------------------------------------------------------------------

export type SimulationEventType =
  | 'tick_started'
  | 'tick_completed'
  | 'agent_acted'
  | 'agent_created'
  | 'agent_deceased'
  | 'policy_enacted'
  | 'ambiguity_detected';

export interface SimulationEvent {
  id: string;
  tick: number;
  event_type: SimulationEventType;
  data: Record<string, unknown>;
}

export interface TickCompletedEvent extends SimulationEvent {
  event_type: 'tick_completed';
  duration_ms: number;
  agent_count: number;
  ambiguity_count: number;
}

export interface AgentActedEvent extends SimulationEvent {
  event_type: 'agent_acted';
  agent_id: string;
  action: string;
  outcome: string;
}

export interface AgentCreatedEvent extends SimulationEvent {
  event_type: 'agent_created';
  agent_id: string;
  persona: string;
}

export interface AgentDeceasedEvent extends SimulationEvent {
  event_type: 'agent_deceased';
  agent_id: string;
  cause: string;
}

export interface PolicyEnactedEvent extends SimulationEvent {
  event_type: 'policy_enacted';
  policy_id: string;
  policy_name: string;
}

export interface AmbiguityDetectedEvent extends SimulationEvent {
  event_type: 'ambiguity_detected';
  agent_id: string;
  top_score: number;
  second_score: number;
}
