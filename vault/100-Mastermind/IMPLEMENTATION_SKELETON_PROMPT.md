---
type: prompt
status: executed
version: 1.0
tags: [skeleton, implementation, specification]
---

# IMPLEMENTATION SKELETON GENERATION

> **Status:** This specification has been executed. The implementation skeleton (shared/, simulation/, models/, backend/, frontend/, contracts/, tests/, tools/mocks/) has been created.
> See also: [[PROJECT_CONTEXT]] and [[NON_NEGOTIABLE_RULES]].

## Context

The repository already contains:

- Documentation
- Architecture
- Obsidian Vault
- GitHub configuration
- Development workflow
- AI Context
- Standards

Do NOT regenerate these.

Do NOT rewrite existing documentation.

Assume PROJECT_CONTEXT.md and NON_NEGOTIABLE_RULES.md are the canonical source of truth.

Your task is to prepare the repository so six developers using AI coding assistants can begin implementation immediately without blocking one another.

---

# OBJECTIVE

Transform the repository into a complete implementation skeleton.

This means creating:

- folders
- placeholder files
- interfaces
- abstract classes
- DTOs
- schemas
- API contracts
- TODO comments
- mock implementations

Do NOT implement business logic.

Do NOT build complete features.

The result should resemble a professional production codebase waiting for implementation.

---

# GENERAL RULES

Every subsystem must be independently buildable.

Every subsystem must compile.

Every subsystem must contain clear TODO markers.

Every public function should contain documentation.

Never create placeholder names like

foo

bar

test

Instead create realistic production names.

---

# CREATE THE COMPLETE FOLDER STRUCTURE

Create every missing directory.

Example

SOCIETAS/

backend/

frontend/

simulation/

models/

shared/

contracts/

tests/

scripts/

docker/

docs/

.github/

vault/

---

# SHARED MODULE

Create

shared/

Purpose:

Contains every object shared between multiple systems.

Examples

shared/

schemas/

dto/

events/

types/

constants/

interfaces/

utilities/

Create placeholder models for

AgentState

SimulationState

Policy

GovernmentPolicy

CitizenDecision

DecisionRequest

DecisionResponse

NewsEvent

SimulationMetrics

DashboardState

TickResult

EconomyState

CrimeState

NeedsState

PsychologyState

PopulationStatistics

Every module should import these instead of creating duplicates.

---

# SIMULATION MODULE

Create

simulation/

engine/

agents/

economy/

world/

crime/

needs/

psychology/

policies/

scheduler/

events/

metrics/

interfaces/

tests/

Each folder should contain

README.md

placeholder files

base interfaces

abstract classes

factory placeholders

TODO comments

Expose interfaces only.

No implementation.

---

# AI MODULE

Create

models/

router/

policy/

narration/

personas/

tie_break/

evaluation/

schemas/

prompts/

memory/

batching/

tests/

Create interfaces for

Policy Translator

Tie Break Engine

Narrator

Persona Generator

News Generator

Model Router

Prompt Builder

Context Loader

Batch Processor

Do not connect to actual models.

---

# BACKEND MODULE

Create

backend/

app/

routers/

services/

repositories/

schemas/

middleware/

dependencies/

config/

websocket/

database/

models/

tests/

Create FastAPI skeleton.

Generate

main.py

router registration

dependency injection

health endpoint

configuration loader

logging

error handlers

mock services

Do not implement business logic.

---

# FRONTEND MODULE

Create

frontend/

src/

pages/

components/

layouts/

hooks/

services/

types/

contexts/

store/

charts/

dashboard/

simulation/

news/

policies/

assets/

Create placeholder pages.

Create component skeletons.

Create service layer.

Create mock data providers.

Create API adapters.

Create routing.

Do not implement visuals.

---

# CONTRACTS

Create

contracts/

simulation_api.yaml

frontend_api.yaml

backend_api.yaml

ai_api.yaml

websocket_api.yaml

events.yaml

schemas/

Document every endpoint.

Document every payload.

Document every websocket event.

Document every DTO.

---

# MOCK API STRATEGY

Generate complete mock APIs.

Examples

GET

/simulation/state

/simulation/metrics

/simulation/agents

/news

/policies

/dashboard

Return realistic JSON.

These mocks should allow frontend development immediately.

---

# TESTING STRUCTURE

Create

unit/

integration/

performance/

fixtures/

mock_data/

Generate placeholders.

No tests required yet.

---

# DOCUMENTATION

Each major folder should contain

README.md

describing

Purpose

Responsibilities

Dependencies

Owner

Public Interfaces

Future Work

---

# TODO MARKERS

Every placeholder should clearly explain

What belongs here

What developer owns it

Dependencies

Integration points

Expected inputs

Expected outputs

---

# INTERFACES

Expose interfaces only.

Simulation exposes

tick()

reset()

apply_policy()

get_state()

get_metrics()

get_agent()

Backend exposes

REST

WebSocket

Health

Frontend consumes

API

WebSocket

AI exposes

translate_policy()

tie_break()

generate_news()

generate_persona()

generate_narration()

---

# DEPENDENCY RULES

Simulation

Never imports Frontend.

Simulation

Never imports Backend.

Frontend

Never imports Simulation.

Frontend

Only uses APIs.

Backend

Coordinates everything.

AI

Never modifies simulation state directly.

---

# CODE QUALITY

Every generated file must

Compile

Contain docstrings

Contain TODOs

Contain proper naming

Contain comments

Contain type hints

Contain clean imports

No dead code.

---

# FINAL DELIVERABLE

When complete, the repository should look like a professional software project where:

- Every subsystem has a complete skeleton.
- Every engineer immediately knows where to work.
- Every AI coding assistant has stable interfaces.
- No subsystem blocks another.
- Mock APIs enable full parallel development.
- Integration can happen later without major refactoring.

Do NOT implement business logic.

Do NOT generate production algorithms.

Generate architecture and implementation scaffolding only.

The result should be ready for six developers to begin coding in parallel immediately.