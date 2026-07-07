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
- `AgentState` - Complete agent state representation
- `SimulationState` - World state container
- `EconomyState` - Economic metrics and indicators
- `CrimeState` - Crime statistics and enforcement
- `NeedsState` - Agent needs fulfillment status
- `PsychologyState` - Psychological and emotional state
- `Policy` - Policy definition and effects
- `GovernmentPolicy` - Active government policy
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
- `ActionType` - Enum of possible agent actions
- `NeedType` - Enum of agent needs
- `EmotionType` - Enum of emotional states
- `WealthClass` - Enum of wealth classifications
- `AgentId`, `TickNumber`, `PolicyId`, `EventId` - Type aliases

## Future Work

- Add validation schemas using Pydantic
- Implement serialization/deserialization utilities
- Add schema versioning support
- Create schema migration tools
