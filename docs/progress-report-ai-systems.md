# Progress Report: AI Systems

**Date:** July 9, 2026
**Team:** SOCIETAS — AI Systems
**Status:** Complete ✅

---

## Objective

Build the AI inference layer — 4 services (tie-breaking, policy translation, persona generation, news/narration) wired to AMD Developer Console (Gemma 2 9B via OpenAI-compatible endpoint). Establish a shared client foundation, expose via FastAPI endpoints, and provide an evaluation runner + mock router for parallel development.

---

## Deliverables (21 source files, +1,000+ lines)

| Module | Files | Description |
|--------|-------|-------------|
| **AMD Client** | `models/client/amd_client.py`, `__init__.py` | `AMDClient` — httpx-based inference client with retry/backoff targeting AMD_API_BASE_URL. Configurable via env var or `AIConfig`. |
| **Prompt Loader** | `models/client/prompt_loader.py` | `PromptLoader` — loads prompts from `prompts/*.md` with YAML frontmatter parsing, Jinja2 template rendering, and in-memory caching. |
| **Response Parser** | `models/client/response_parser.py` | `parse_response` — extracts JSON from code fences, hydrates dataclasses, retries on parse failure. |
| **Tie-Breaking** | `models/tie_break/tie_breaker.py` | `TieBreaker` — resolves ambiguous agent decisions via `tie-break.md` prompt. Confidence clamping, fallback to first option on parse failure. |
| **Policy Translation** | `models/policy/policy_translator.py` | `PolicyTranslator` — converts agent persona + goal into 6-dimension `PolicyWeights` delta vector. |
| **Persona Generation** | `models/personas/persona_generator.py` | `PersonaGenerator` — generates 1-2 sentence personas from 8 trait dimensions with empty-response fallback. |
| **News & Narration** | `models/narration/narrative_generator.py` | `NarrativeGenerator` — generates `NewsEvent` and `SpotlightNarration` with structured JSON parsing. |
| **Model Router** | `models/router/config.py`, `ai_router.py` | `AIConfig` dataclass (7 fields), `AIRouter` facade implementing `IAIRouter` interface — orchestrates all 4 services. |
| **FastAPI Endpoints** | `backend/app/routers/ai.py` | 5 endpoints: `POST /translate-policy`, `/tie-break`, `/generate-news`, `/generate-persona`, `/generate-narration` + `GET /status`. |
| **Evaluation** | `models/evaluation/evaluate.py`, `runner.py` | `run_evaluation_suite()` with 4 smoke-test scenarios. `runner.py` — CLI entry point with pass/fail summary. |
| **Mock AI Router** | `tools/mocks/mock_ai_router.py` | `MockAIRouter` — implements all 6 `IAIRouter` methods with deterministic keyword-based responses for simulation dev without AMD endpoint. |
| **Prompts** | `prompts/*.md` (7 files) | 5 purpose prompts + 1 shared components + 1 README. All have YAML frontmatter, versioning, input/output schemas. Governance advisor prompt exists as stretch. |
| **Unit Tests** | `tests/unit/models/` (8 files) | 48 tests across all AI modules — AMD client, prompt loader, response parser, all 4 services, AI router. |

---

## Architecture

```
POST /ai/* ──→ backend/app/routers/ai.py
models/
├── client/
│   ├── amd_client.py          ──→ AMD Console (Gemma 2 9B)
│   ├── prompt_loader.py       ──→ prompts/*.md
│   └── response_parser.py     ──→ Dataclass hydration
├── tie_break/tie_breaker.py
├── policy/policy_translator.py
├── personas/persona_generator.py
├── narration/narrative_generator.py
├── router/
│   ├── config.py              ──→ AIConfig dataclass
│   └── ai_router.py           ──→ IAIRouter orchestrator
└── evaluation/
    ├── evaluate.py            ──→ Evaluation scenarios
    └── runner.py              ──→ CLI entry point

tools/mocks/mock_ai_router.py  ──→ Deterministic mock for simulation dev
```

All inference goes through AMD Developer Console (`gemma-2-9b-it`). No external API costs — self-hosted on AMD hardware. Mock router available for offline development.

---

## Test Results

**48/48 tests passing** across all AI modules:

| Test File | Tests | Status |
|-----------|-------|--------|
| `test_amd_client.py` | 8 | ✅ Pass |
| `test_ai_router.py` | 8 | ✅ Pass |
| `test_tie_breaker.py` | 5 | ✅ Pass |
| `test_policy_translator.py` | 4 | ✅ Pass |
| `test_persona_generator.py` | 4 | ✅ Pass |
| `test_narrative_generator.py` | 7 | ✅ Pass |
| `test_prompt_loader.py` | 5 | ✅ Pass |
| `test_response_parser.py` | 7 | ✅ Pass |

All tests are unit tests with mocked `AMDClient` — no live endpoint required.

---

## Key Design Decisions

1. **AMD Developer Console over external API** — Self-hosted Gemma 2 9B via OpenAI-compatible endpoint. Zero auth overhead, no API costs, full control over inference.
2. **Raw httpx over OpenAI SDK** — Keeps dependency footprint minimal. AMD endpoint uses the same `/chat/completions` schema as OpenAI so the client is trivially swappable.
3. **Dependency injection via constructor** — All 4 services accept an optional `AMDClient` in their constructor, enabling mock injection in tests without patching.
4. **Prompts as markdown with frontmatter** — Every prompt has `temperature`, `max_tokens`, and `version` in YAML frontmatter. PromptLoader reads them at runtime — no hardcoded params in service code.
5. **Mock router for parallel development** — `MockAIRouter` provides deterministic responses for all 6 `IAIRouter` methods, letting simulation and backend engineers develop without a running AMD endpoint.
6. **Retry with exponential backoff** — All AMD API calls retry up to `max_retries` times with `2^attempt` sleep, covering transient failures without crashing the tick.
7. **Evaluation as self-contained CLI** — `python -m models.evaluation.runner` runs 4 smoke-test scenarios against the real endpoint. Results printed with timing; exit code 0/1 for CI.

---

## Cross-Team Flags

1. **Simulation — AI escalation not wired.** `SimulationEngine` tick docstring has a TODO: "if ambiguous, queue for AI escalation" but no integration exists. `SimulationConfig.enable_ai_escalation` and `ambiguity_threshold` fields are ready. **Action: Simulation Engineer to integrate `IAIRouter.tie_break()` into the tick loop.**

2. **Backend — No AI dependency injection in container.** `backend/app/dependencies/container.py` provides services for engine, policy, agent, metrics — but no `get_ai_router()`. The AI router currently uses a lazy global singleton in `routers/ai.py`. **Action: Backend Engineer to add `get_ai_router()` to the DI container.**

3. **Contracts — openapi.yaml missing AI endpoints.** The 5 AI endpoints (`POST /translate-policy`, `/tie-break`, etc.) exist in code but are not documented in `contracts/api/openapi.yaml`. **Action: Tech Lead to reconcile contracts with live AI endpoints.**

---

## Next Steps

- End-to-end testing against live AMD endpoint (requires endpoint accessible from dev environment)
- Wire `AIRouter.tie_break()` into simulation engine tick loop
- Add `get_ai_router()` to backend DI container
- Refine prompt temperatures and `max_tokens` based on real AMD response quality
- Contract documentation for AI endpoints in `openapi.yaml`
