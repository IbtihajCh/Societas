/**
 * API Types
 *
 * TypeScript types for SOCIETAS API responses.
 * Mirrors the canonical Python DTOs in shared/dto/* (snake_case, as-is).
 * Source of truth: shared/dto/*.py and shared/types/enums.py — keep in sync.
 *
 * Last synced with: origin/main (commit 07d6be7)
 */

// ---------------------------------------------------------------------------
// Enums (mirror shared/types/enums.py)
//
// StrEnum types (ActionType, WealthClass, EmotionType, NeedType, Gender,
// Culture, JobType) serialize as their lowercase string values.
// PolicyCategory and EmploymentStatus use Enum + auto() (integer values),
// but the frontend sends/receives them by member name string.
// ---------------------------------------------------------------------------

export enum ActionType {
  WORK = 'work',
  BUY_FOOD = 'buy_food',
  REST = 'rest',
  SEEK_JOB = 'seek_job',
  BEG = 'beg',
  BEFRIEND = 'befriend',
  CONSOLE = 'console',
  ISOLATE = 'isolate',
  SHARE = 'share',
  STEAL = 'steal',
  HARM_OTHER = 'harm_other',
  PROTEST = 'protest',
  COMPLAIN = 'complain',
  COMPLY = 'comply',
  IDLE = 'idle',
}

export enum NeedType {
  FOOD = 'food',
  WATER = 'water',
  SLEEP = 'sleep',
  SEXUAL_TENSION = 'sexual_tension',
  SAFETY = 'safety',
  FINANCIAL_SECURITY = 'financial_security',
  SHELTER = 'shelter',
  SOCIAL_CONNECTION = 'social_connection',
  FAMILY_BOND = 'family_bond',
  ROMANTIC_BOND = 'romantic_bond',
  SELF_ESTEEM = 'self_esteem',
  REPUTATION = 'reputation',
  INFERIORITY_GAP = 'inferiority_gap',
}

export enum EmotionType {
  HAPPY = 'happy',
  NORMAL = 'normal',
  SAD = 'sad',
  ANGRY = 'angry',
  DESPAIR = 'despair',
}

export enum WealthClass {
  POOR = 'poor',
  MIDDLE = 'middle',
  RICH = 'rich',
}

export enum Gender {
  MALE = 'male',
  FEMALE = 'female',
}

export enum Culture {
  A = 'A',
  B = 'B',
  C = 'C',
}

export enum EducationLevel {
  NONE = 0,
  PRIMARY = 1,
  SECONDARY = 2,
  HIGHER = 3,
}

export enum JobType {
  ENGINEER = 'engineer',
  COMPUTER_SCIENTIST = 'computer_scientist',
  PILOT = 'pilot',
  DOCTOR = 'doctor',
  THERAPIST = 'therapist',
  MECHANIC = 'mechanic',
  ELECTRICIAN = 'electrician',
  CONSTRUCTION_PLANNER = 'construction_planner',
  CONSTRUCTION_WORKER = 'construction_worker',
  CLEANER = 'cleaner',
  TAXI_DRIVER = 'taxi_driver',
  UNEMPLOYED = 'unemployed',
}

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

export enum EmploymentStatus {
  EMPLOYED = 'EMPLOYED',
  UNEMPLOYED = 'UNEMPLOYED',
  STUDENT = 'STUDENT',
  RETIRED = 'RETIRED',
  UNABLE_TO_WORK = 'UNABLE_TO_WORK',
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
  policy_text?: string | null;
}

export interface PolicyResponseDTO {
  id: string;
  name: string;
  description: string;
  category: PolicyCategory;
  weights: Record<string, number>;
  is_active: boolean;
  enactment_tick: number;
  impact_deltas: Record<string, Record<string, number>>;
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

export interface AgentHistoryResponseDTO {
  agent_id: string;
  history: AgentHistoryEntry[];
}

export interface AgentHistoryEntry {
  tick: number;
  action: string;
  details?: Record<string, unknown>;
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
  unlust: MetricPointDTO[];
  morality: MetricPointDTO[];
  protest_intensity: MetricPointDTO[];
  action_frequencies: Record<string, number>;
  emotion_distribution: Record<string, number>;
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
// Policy revoke response (backend returns {status, policy_id} not PolicyResponseDTO)
// ---------------------------------------------------------------------------

export interface PolicyRevokeResponseDTO {
  status: string;
  policy_id: string;
}

// ---------------------------------------------------------------------------
// WebSocket events
//
// The backend broadcasts messages with a "type" discriminator (not
// "event_type"). See backend/app/services/simulation_service.py advance_tick().
// ---------------------------------------------------------------------------

export type WebSocketMessageType =
  | 'tick_completed'
  | 'agent_acted';

export interface TickCompletedMessage {
  type: 'tick_completed';
  tick: number;
  duration_ms: number;
  population: number;
  state_hash: string;
  ambiguity_count: number;
  ai_calls: number;
}

export interface AgentActedMessage {
  type: 'agent_acted';
  agent_id: string;
  action: string;
}

export type WebSocketMessage = TickCompletedMessage | AgentActedMessage;
