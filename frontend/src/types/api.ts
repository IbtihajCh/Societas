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
  BUY_FOOD = 'BUY_FOOD',
  REST = 'REST',
  SEEK_JOB = 'SEEK_JOB',
  BEG = 'BEG',
  BEFRIEND = 'BEFRIEND',
  CONSOLE = 'CONSOLE',
  ISOLATE = 'ISOLATE',
  SHARE = 'SHARE',
  STEAL = 'STEAL',
  HARM_OTHER = 'HARM_OTHER',
  PROTEST = 'PROTEST',
  COMPLAIN = 'COMPLAIN',
  COMPLY = 'COMPLY',
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
  MIDDLE = 'MIDDLE',
  RICH = 'RICH',
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
  food_availability: number;
  water_availability: number;
  crime_rate: number;
  protest_intensity: number;
  unemployment_rate: number;
  tax_rate: number;
  welfare_enabled: boolean;
  welfare_amount: number;
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
  emotion: string;
  unlust: number;
  job_type: string;
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
  is_alive: boolean;
  location: string;
  last_action: string | null;
  last_reasoning: string;
  social_connections: number;
  gender: string;
  culture: string;
  born_tick: number;
  unlust: number;
  happiness_score: number;
  emotion: string;
  emotion_timer: number;
  good_acts: number;
  crimes_committed: number;
  notoriety: number;
  trust_in_govt: number;
  protest_count: number;
  money: number;
  base_salary: number;
  employed: boolean;
  education: string;
  property: boolean;
  health: number;
  job_type: string;
  grid_x: number;
  grid_y: number;
  spouse: string | null;
  enemies: string[];
  community_id: string | null;
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
