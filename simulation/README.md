# Simulation Module

**Owner:** Simulation Engineer

## Purpose

Core deterministic simulation engine for SOCIETAS. Implements agent-based modeling with psychological traits, economic systems, needs fulfillment, and policy application.

## Responsibilities

- Manage autonomous agents with decision-making capabilities
- Simulate economic systems (employment, wealth, markets)
- Track agent needs and psychological states
- Apply government policies and calculate effects
- Execute deterministic tick-based simulation
- Collect and aggregate simulation metrics
- Publish events for other subsystems

## Dependencies

- `shared/` - Shared schemas, types, and interfaces
- `numpy` - Deterministic random number generation

## Public Interfaces

### SimulationEngine
- `tick()` - Advance simulation by one tick
- `reset()` - Reset to initial state
- `apply_policy()` - Apply a government policy
- `get_state()` - Get current world state
- `get_metrics()` - Get simulation metrics
- `get_agent()` - Get specific agent state
- `get_agents()` - Get all agents

### Agent
- `evaluate_needs()` - Evaluate agent needs
- `calculate_utility_scores()` - Calculate action utilities
- `select_action()` - Select best action
- `execute_action()` - Execute selected action

## Future Work

- Implement full tick execution logic
- Add agent lifecycle (birth, death, aging)
- Implement economy subsystem
- Add crime and enforcement
- Implement needs fulfillment
- Add psychology and emotions
- Implement policy effect calculation
- Add event generation and narration triggers
