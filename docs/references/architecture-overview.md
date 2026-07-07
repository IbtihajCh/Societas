# Architecture Overview

SOCIETAS uses a three-layer architecture inspired by dual-process cognitive theory. This document provides a high-level reference.

---

## Three-Layer Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                     │
│                                                          │
│  Dashboard · Charts · News Feed · Agent Stories         │
│  Policy Reports · Metrics · User Interaction             │
│                                                          │
│  Technology: React/TypeScript, WebSocket, D3/Charting    │
├─────────────────────────────────────────────────────────┤
│                   COGNITIVE REASONING LAYER                │
│                                                          │
│  Gemma 9B / 26B via vLLM                                 │
│                                                          │
│  Tie-Breaking · Policy Translation · Narrative Gen       │
│  Persona Generation · Governance Advisory                │
│                                                          │
│  Technology: FastAPI, vLLM, Gemma, Structured Prompts    │
├─────────────────────────────────────────────────────────┤
│                  DETERMINISTIC SIMULATION LAYER            │
│                                                          │
│  World State · Agent State · Economy · Needs             │
│  Psychology · Emotions · Decision Scores · Policies      │
│  Environment · Crime · Employment · Tick Updates         │
│                                                          │
│  Technology: Python, NumPy, Pydantic                     │
└─────────────────────────────────────────────────────────┘
```

---

## Decision Pipeline (detail)

```
┌─────────────┐
│ Agent State │  Needs, psychology, emotions, resources
└──────┬──────┘
       ↓
┌─────────────┐
│ Rule Engine │  Compute action utility scores (deterministic)
└──────┬──────┘
       ↓
┌─────────────────┐
│ Ambiguity Check │  Is (top_score - second_score) < threshold?
└──────┬──────────┘
       │
  ┌────┴────┐
  │         │
  │ NO      │ YES
  │         ↓
  │  ┌──────────────┐
  │  │ Escalate to  │
  │  │ Gemma        │
  │  └──────┬───────┘
  │         ↓
  │  ┌──────────────┐
  │  │ Hybrid Fusion│  Blend deterministic + LLM scores
  │  └──────┬───────┘
  │         ↓
  └────┬────┘
       ↓
┌─────────────┐
│   Action    │  Execute the selected action
└─────────────┘
```

---

## Data Flow

```
Simulation Engine ──(state)──→ FastAPI ──(JSON)──→ Dashboard
       │                                                 │
       │  (escalation)                                   │
       ↓                                                 │
   vLLM Router ──(prompt)──→ Gemma ──(scores)──→ Engine  │
       │                                                 │
       │  (events)                                       │
       └─────────────────────────────────────────────────┘
                         News Feed, Narratives
```

---

## Subsystem Boundaries

| Layer | Owns | Does NOT Own |
|-------|------|--------------|
| Simulation | Agent state, world, economy, needs, decisions | API, UI, LLM calls |
| AI (Gemma) | Prompts, model routing, reasoning | Core state, economics, physics |
| Backend | API, WebSocket, data persistence | Simulation logic, frontend rendering |
| Frontend | Dashboard, charts, user interaction | Business logic, data computation |

---

## Key Design Decisions

- **Determinism first** — The simulation engine is fully deterministic (see [ADR-002](../adr/ADR-002-deterministic-simulation-design.md))
- **LLM as advisor** — Gemma influences decisions but never overrides (see [ADR-003](../adr/ADR-003-hybrid-decision-fusion.md))
- **Proportional LLM usage** — Escalation only when ambiguity is detected (see [ADR-004](../adr/ADR-004-escalation-threshold.md))
- **Modular subsystems** — Each layer can be tested independently (see [testing strategy](../../tests/README.md))

---

## Related

- [Master Context §4](../../SOCIETAS_Master_Context.md)
- [ADR-002: Deterministic Simulation](../adr/ADR-002-deterministic-simulation-design.md)
- [ADR-003: Hybrid Decision Fusion](../adr/ADR-003-hybrid-decision-fusion.md)
- [Glossary](glossary.md)
