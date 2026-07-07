# SOCIETAS — Master Context & Architecture Decisions (v2.0)

> **Purpose:** This document is the persistent engineering context for SOCIETAS. It complements the main Project Design Document and records strategic decisions, architectural philosophy, AI integration, and implementation constraints. Any AI coding agent or new developer joining the project should read this document before contributing.

---

# 1. Project Overview

**Project:** SOCIETAS

**Type:** AI-powered Governance & Society Simulation Platform

**Competition:**
AMD Developer Hackathon: Act II (lablab.ai)

**Track:**
Unicorn Track

**Goal:**

Build a real-time, explainable, large-scale governance simulator capable of modeling how policy decisions cascade through an artificial society consisting of autonomous individuals with realistic psychological, economic, and social behavior.

Unlike traditional simulations, SOCIETAS combines:

- Rule-based Agent Based Modeling (ABM)
- Cognitive Psychology
- Behavioral Economics
- Emergent Social Systems
- Large Language Models (Gemma)
- Explainable AI

---

# 2. Core Philosophy

The project follows one guiding principle:

> **Deterministic systems should model reality.
LLMs should model human reasoning.**

The simulation itself must remain:

- explainable
- reproducible
- deterministic
- mathematically grounded

Gemma is **not** the simulation.

Gemma acts as a reasoning layer that augments—not replaces—the deterministic engine.

---

# 3. Competition Strategy

The project is intentionally designed to satisfy BOTH:

- AMD Infrastructure Prize
- Google Gemma Prize

simultaneously.

---

## AMD Story

AMD hardware is not included simply because the competition requires it.

Instead:

AMD GPUs make possible

- local inference
- multi-model execution
- real-time reasoning
- batched inference
- lower operational cost

The product becomes economically feasible specifically because inference runs locally.

---

## Gemma Story

Gemma performs multiple independent responsibilities:

- policy translation
- decision reasoning
- narrative generation
- governance explanation
- persona generation

This demonstrates meaningful model utilization rather than replacing one API with another.

---

# 4. System Architecture

The architecture now consists of three logical layers.

---

## Layer 1 — Deterministic Simulation

This is the heart of SOCIETAS.

Everything here must remain deterministic.

Responsible for:

- World Simulation
- Agent State
- Economy
- Needs
- Unlust
- Psychology
- Emotions
- Decision Scores
- Policies
- Environment
- Crime
- Employment
- Tick Updates

No LLM involvement.

This layer is fully explainable.

---

## Layer 2 — Cognitive Reasoning Layer

This layer contains Gemma.

It is **not** responsible for running the simulation.

Instead it assists the simulation whenever genuine reasoning is required.

Responsibilities:

- tie-breaking
- contextual reasoning
- policy interpretation
- narrative generation
- advisory reasoning

Think of this layer as **System 2 Thinking**.

---

## Layer 3 — Presentation Layer

Responsible for:

- Dashboard
- Charts
- News Feed
- Agent Stories
- Policy Reports
- Metrics
- User Interaction

---

# 5. Dual Process Cognitive Architecture

The project now follows a dual-process cognitive model inspired by modern cognitive psychology.

System 1

Fast

Cheap

Deterministic

Rule Based

↓

System 2

Slow

Reasoning Heavy

LLM Powered

↓

Final Decision

This architecture preserves explainability while allowing realistic reasoning in ambiguous situations.

---

# 6. Decision Pipeline

Every agent follows the same pipeline.

Agent State

↓

Rule Engine

↓

Action Utility Scores

↓

Ambiguity Check

↓

IF NOT AMBIGUOUS

Execute highest score

↓

IF AMBIGUOUS

Send to Gemma

↓

Gemma adjusts reasoning

↓

Final Action

This keeps inference proportional to uncertainty rather than population size.

---

# 7. Escalation Threshold

LLM usage must remain mathematically bounded.

Gemma should never be invoked simply because an agent exists.

Instead escalation occurs only when deterministic uncertainty exceeds a configurable threshold.

Example conditions:

- Decision probability difference ≤ 0.05
- Borderline emotional thresholds
- Multiple actions nearly identical
- Internal conflict between morality and survival

Example

Steal

0.44

Protest

0.43

Difference

0.01

↓

Escalate

---

Suggested configuration

```python
LLM_ESCALATION_THRESHOLD = 0.05
```

This value should remain configurable.

---

# 8. Hybrid Decision Fusion

Gemma should not directly replace actions.

Instead it contributes reasoning weights.

Rule Engine

```text
Steal     0.44
Protest   0.43
Work      0.13
```

Gemma

```text
Steal     0.31
Protest   0.55
Work      0.14
```

Fusion

```text
Steal     0.40
Protest   0.48
Work      0.12
```

The deterministic engine still owns the decision.

Gemma influences it.

This preserves explainability.

---

# 9. Tie Break Schema

Input

```json
{
    "id":42,
    "state":"angry",
    "unlust":0.59,
    "morality":0.61,
    "options":["steal","protest"]
}
```

Output

```json
{
    "id":42,
    "action":"protest",
    "confidence":0.73,
    "reason":"Moderate morality outweighs desperation."
}
```

Reason is optional.

Confidence is encouraged.

---

# 10. AI Responsibility Matrix

| Event | Model | Frequency | Batch |
|----------|----------|------------|------------|
| Agent Birth | Gemma 26B | Once | No |
| Policy Translation | Gemma 26B | Policy Only | No |
| Decision Tie Break | Gemma 26B | Rare | Yes |
| News Feed | Gemma 31B | Major Events | Small |
| Spotlight Narration | Gemma 31B | Few Agents | Small |
| Governance Advisor | Gemma 31B | Policy Complete | No |

---

# 11. Persona Generation

Each agent receives a one-time generated persona.

Input traits

- morality
- creativity
- ambition
- resilience
- dominance
- anger tendency
- extraversion
- wealth class

Output

Maximum

Two sentences.

Example

> "I grew up believing hard work matters, but every setback chips away at that belief. I avoid violence until survival leaves me no choice."

The persona is generated exactly once.

Never regenerated.

Stored permanently.

---

# 12. vLLM Deployment

Architecture

FastAPI Router

↓

Gemma 26B

↓

Gemma 31B

Router Responsibilities

- Request routing
- Queue management
- Model selection
- Batch aggregation

No complex orchestration is required for hackathon scope.

---

# 13. Feature Priority

## Must Ship

✔ Simulation

✔ Dashboard

✔ Policy Translation

✔ News Feed

---

## High Priority

✔ Spotlight Narration

---

## Stretch Goal

Governance Advisor

---

## Post Hackathon

Hybrid Narrative Override

Communities

Families

Political Parties

Religion

Organized Crime

International Relations

---

# 14. Engineering Principles

Every major component must satisfy:

Explainability

Performance

Reproducibility

Modularity

Testability

Scalability

No feature should compromise these principles.

---

# 15. AI Usage Philosophy

LLMs are used for

✔ Reasoning

✔ Interpretation

✔ Narrative

✔ Advisory

✔ Context

LLMs are NOT used for

✘ Physics

✘ Economy

✘ Needs

✘ Tick Updates

✘ Simulation State

✘ Core Mathematics

---

# 16. Repository Philosophy

Repository should resemble a startup-grade open source project.

Structure

/backend

/frontend

/simulation

/docs

/presentation

/vault

/prompts

/scripts

.github

The Obsidian Vault lives inside `/vault` and is version controlled with Git.

---

# 17. Development Workflow

Every feature follows

Research

↓

Specification

↓

Architecture

↓

Planning

↓

Implementation

↓

Testing

↓

Documentation

↓

Review

↓

Merge

AI agents must never skip these steps.

---

# 18. Current Team

Team Size

6 Members

Recommended Roles

Technical Lead

Simulation Engineer

AI Systems Engineer

Backend Engineer

Frontend Engineer

Infrastructure / DevOps Engineer

Each member owns an entire subsystem rather than isolated tasks.

---

# 19. Current Project Status

Completed

✔ Overall Architecture

✔ Competition Strategy

✔ AI Philosophy

✔ Layered System Design

✔ Escalation Threshold Design

✔ JSON Tie Break Schema

✔ Model Routing Design

✔ Persona Strategy

✔ Feature Prioritization

Next Major Milestones

- Repository setup
- GitHub workflow
- Obsidian Vault
- Feature specifications
- Sprint planning
- Simulation implementation
- AI integration
- Dashboard
- Demo preparation

---

# 20. Vision Statement

SOCIETAS is not intended to be another agent simulation.

The objective is to build the first explainable AI-assisted governance sandbox where deterministic simulation and large language models work together through a principled hybrid cognitive architecture.

The simulation provides causality.

The LLM provides reasoning.

Together they create an interactive environment capable of helping humans understand the societal consequences of complex policy decisions.