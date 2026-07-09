# Shared Module

**Owner:** All Subsystems (Shared Responsibility)

## Purpose

The shared module contains all types, schemas, interfaces, and utilities that are used across multiple subsystems in SOCIETAS. This ensures consistency and prevents duplication.

## Responsibilities

- Define canonical data schemas (AgentState, SimulationState, Policy, etc.)
- Provide Data Transfer Objects (DTOs) for API communication
- Define event types for the event bus system
- Maintain type definitions and enums
- Store configuration constants and thresholds
- Define abstract interfaces for subsystem contracts
- Provide shared utility functions

## Dependencies

- None (this is a foundational module)
- Used by: simulation/, backend/, frontend/, models/

## Public Interfaces

### Schemas
- `AgentState` - Complete agent state representation (40+ fields: traits, needs, emotions, resources, gender, culture, grid position, unlust, morality, etc.)
- `SimulationState` - World state container (economy, crime, needs, psychology sub-states)
- `EconomyState` - Economic metrics and indicators
- `CrimeState` - Crime statistics and enforcement
- `NeedsState` - Agent needs fulfillment status
- `PsychologyState` - Psychological and emotional state
- `Policy` - Policy definition and effects
- `GovernmentPolicy` - Active government policy with `ImpactDelta` per wealth class
- `DecisionRequest` - Request for decision resolution
- `DecisionResponse` - Resolved decision outcome
- `NewsEvent` - News article/event
- `SimulationMetrics` - Aggregated simulation metrics
- `DashboardState` - Dashboard data payload
- `TickResult` - Result of a simulation tick
- `PopulationStatistics` - Population-level statistics

### Interfaces
- `ISimulationEngine` - Simulation engine contract
- `IAgent` - Agent behavior contract
- `IPolicyEngine` - Policy application contract
- `IAIRouter` - AI routing contract
- `IEventBus` - Event bus contract
- `IDataRepository` - Data persistence contract

### Types
- `ActionType` - Enum of possible agent actions (15 values: work, buy_food, rest, seek_job, beg, befriend, console, isolate, share, steal, harm_other, protest, complain, comply, sleep)
- `NeedType` - Enum of agent needs (13 values across 5 Maslow layers)
- `EmotionType` - Enum of emotional states (5 values: happy, normal, sad, angry, despair)
- `WealthClass` - Enum of wealth classifications (3 values: POOR, MIDDLE, RICH)
- `Gender` - Enum (MALE, FEMALE)
- `Culture` - Enum (INDIVIDUALIST, COLLECTIVIST, TRADITIONAL)
- `EducationLevel` - Enum (NONE, BASIC, SECONDARY, TERTIARY)
- `JobType` - Enum (12 job types with salary levels)
- `AgentId`, `TickNumber`, `PolicyId`, `EventId`, `GridCoordinate` - Type aliases

### Constants
- `shared/constants/defaults.py` — 70+ simulation constants (population size, grid size, decay rates, thresholds, weights, tick defaults)
- `shared/constants/simulation_constants.py` — Salary ranges for 11 job types, wealth class distribution config, Beta distribution parameters for traits
- `shared/constants/thresholds.py` — Ambiguity, need, emotion, and death thresholds (configurable)

### Utilities
- `DeterministicRNG` in `shared/utilities/deterministic_rng.py` — Seeded `numpy.random.Generator` wrapper with methods:
  - `beta(a, b, size)` — Beta-distributed random values
  - `weighted_choice(options, weights)` — Weighted random selection
  - `integers(low, high, size)` — Integer random values
  - All methods accept an optional `seed` parameter for sub-stream determinism

## Future Work

- Implement serialization/deserialization utilities
- Add schema versioning support
- Create schema migration tools
