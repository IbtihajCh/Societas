# Progress Report: Frontend API Contract Alignment

**Date:** July 8, 2026
**Team:** SOCIETAS — Frontend
**Branch:** `fe/align-api-contract` (pushed to origin)
**Status:** Complete ✅

---

## Objective

Align the frontend TypeScript types and API service with the actual backend
DTOs in `shared/dto/*`, replacing stale types that did not match the running
FastAPI server. Establish type safety across the frontend and fix latent bugs
exposed by the new types.

---

## Context

After the backend engineer completed the service layer (PR #9, 17 tests
passing), a review revealed significant **contract drift** between the
frontend's `src/types/api.ts` / `contracts/openapi.yaml` and the backend's
actual DTOs in `shared/dto/*`. The frontend types were fiction — they
described a nested `SimulationState` with `economy`, `crime`, `needs`, and
`psychology` sub-objects, while the backend returns a flat
`SimulationStateResponseDTO` with `economic_health`, `social_cohesion`,
`public_order`, `innovation_index`, `unlust`, and `morality`. The policy
categories were also wrong (5 vs the real 8). This PR makes the frontend
types match reality.

---

## Deliverables (1 commit, +473 / -144 lines, 11 files)

| File | Change | Description |
|------|--------|-------------|
| `src/types/api.ts` | **Rewritten** | Full rewrite mirroring `shared/dto/*` (snake_case as-is). Added enums: `PolicyCategory` (8 values), `ActionType` (13), `EmploymentStatus` (5), `WealthClass` (6). Added simulation event types for WebSocket (`tick_completed`, `agent_acted`, `policy_enacted`, `agent_deceased`, `ambiguity_detected`). |
| `src/services/api.ts` | **Rewritten** | Typed all return values (replaced `any`). Added Axios response interceptor with `ApiError` class. Added `getHealth`, `resetSimulation` methods. Start request now sends `{population_size, seed}`. |
| `src/components/policies/PolicyForm.tsx` | **Fixed** | Category select now uses the real 8 `PolicyCategory` enum values (was missing `ENVIRONMENTAL`, `PUBLIC_ORDER`, `HEALTHCARE`, `INFRASTRUCTURE`, `CULTURAL`). `onSubmit` typed as `PolicyCreateRequestDTO`. |
| `src/pages/agents.tsx` | **Fixed** | Fixed latent bug: `setState` was receiving the whole `AgentListResponseDTO` object instead of `data.agents` array (masked by `any`). Added `useEffect` cleanup. |
| `src/pages/policies.tsx` | **Fixed** | Same latent bug: `setState` received `PolicyListResponseDTO` instead of `data.policies`. Refactored to `useCallback` for clean effect + handler sharing. |
| `src/pages/index.tsx` | **Fixed** | Replaced `<a>` with `next/link` `<Link>` (ESLint `no-html-link-for-pages` error). |
| `src/components/agents/AgentDetail.tsx` | **Fixed** | Fixed `useEffect` exhaustive-deps warning by inlining the load function with cancellation guard. |
| `frontend/.eslintrc.json` | **New** | Next.js strict ESLint config (`next/core-web-vitals`) for non-interactive `next lint`. |
| `frontend/package.json` | **Updated** | Added `typecheck` script (`tsc --noEmit`) referenced by root `package.json`. |
| `frontend/README.md` | **Updated** | Added contract source-of-truth note, backend endpoint table, and prerequisites section. |
| `frontend/next-env.d.ts` | **New** | Standard Next.js TypeScript environment file. |

---

## Contract Drift Findings

| Concept | Frontend types (old) | Backend actual (shared/dto/*) |
|---------|---------------------|-------------------------------|
| `SimulationState` | Nested `{economy, crime, needs, psychology}` | **Flat** `{economic_health, social_cohesion, public_order, innovation_index, unlust, morality}` |
| `SimulationStatus` | camelCase `{isRunning, currentTick}` | snake_case `{is_running, tick, speed, population}` |
| `Policy.category` | 5 values (incl. `CRIMINAL`, `HEALTH`) | **8 values**: `ECONOMIC, SOCIAL, ENVIRONMENTAL, PUBLIC_ORDER, EDUCATION, HEALTHCARE, INFRASTRUCTURE, CULTURAL` |
| `AgentDetail` | `{wealth, happiness, health, recentActions}` | `{traits, needs, emotions, resources, wealth_class, employment_status, age, location, last_action, social_connections}` |
| `Metrics` | Flat scalars | Time-series `List<{tick, value}>` per domain + `summary` |

**Decision:** Consume snake_case as-is (no transform layer). This keeps the
frontend types as a direct mirror of the backend DTOs with zero conversion
bugs — the right tradeoff for hackathon speed.

---

## Verification

All three gates passed before push:

| Gate | Command | Result |
|------|---------|--------|
| Lint | `npm run lint` | ✅ No ESLint warnings or errors |
| Typecheck | `npm run typecheck` (`tsc --noEmit`) | ✅ Clean |
| Build | `npm run build` (`next build`) | ✅ Compiled successfully, 6/6 pages generated |

Pages built: `/`, `/_app`, `/404`, `/agents`, `/dashboard`, `/policies`

---

## Key Design Decisions

1. **snake_case as-is** — Frontend types match backend serialization directly. No camelCase transform layer. Fewest moving parts, fewest bugs.
2. **Types mirror shared/dto/\*** — The Python DTOs are the canonical source of truth, not `contracts/openapi.yaml` (which is stale). `src/types/api.ts` must be kept in sync manually.
3. **Enums over string literals** — Policy categories, action types, employment status, and wealth class are TypeScript enums matching `shared/types/enums.py`, enabling compile-time safety in forms and rendering.
4. **ApiError interceptor** — Axios responses pass through an error interceptor that normalizes errors into a typed `ApiError` with `status` and `detail`, ready for UI error states in PR 2.

---

## Cross-Team Flags

These are items outside frontend ownership that need attention from other
team members:

1. **Backend — WebSocket broadcast not wired.** `WebSocketManager.broadcast()`
   exists but nothing calls it. `advance_tick()` in `simulation_service.py`
   does not broadcast `tick_completed` / `agent_acted` events. The `/ws`
   endpoint only echoes. The frontend will use REST polling as a fallback
   until this is connected. **Action: Backend Engineer to wire
   `ws_manager.broadcast()` into the tick lifecycle.**

2. **Tech Lead — contracts/openapi.yaml is stale.** The OpenAPI spec and
   `contracts/schemas/*.json` do not match `shared/dto/*`. The frontend now
   treats `shared/dto/*` as the source of truth. **Action: Tech Lead to
   reconcile `contracts/` with `shared/dto/` or mark the DTOs as canonical.**

3. **Tech Lead — CHANGELOG.md.** I do not own `CHANGELOG.md` (tech-lead
   owned per CODEOWNERS). Proposed entry for `[Unreleased]`:

   ```
   ### Frontend
   - Aligned `src/types/api.ts` with backend DTOs (`shared/dto/*`)
   - Added type safety across API service and pages
   - Fixed PolicyForm categories (8 PolicyCategory values)
   - Fixed latent state bugs in agents.tsx and policies.tsx
   - Added ESLint config and typecheck script
   ```

---

## Next Steps (PR 2 — `fe/real-time-data-pipeline`)

- Delete orphaned Zustand store (`simulationStore.ts`)
- Create WebSocket client (`src/services/websocket.ts`)
- Implement `SimulationContext` with real API calls + REST polling fallback
- CSS Modules foundation (design tokens + component conversion)
- Wire `dashboard.tsx` to live data with loading/error/disconnected states
- Jest setup + component tests (70% line coverage on touched files)
- Feature spec in `vault/060-Features/` + sprint plan in `vault/030-Sprints/`

---

# Update: DTO Sync with Simulation & AI Layers

**Date:** July 9, 2026
**Branch:** `Frontend` (rebased onto `origin/main`)
**Status:** Complete ✅

---

## Context

After PR 1 was merged, three major work streams landed on `main` (38 commits):

1. **Simulation Engine** (Phases 1–6) — full deterministic engine with 475 tests
2. **AI Inference Layer** — Gemma 2 9B via AMD Developer Console, 5 new API endpoints, 48 tests
3. **Backend Fixes** — WebSocket broadcast wired, engine persistence, DTO returns

The simulation engineer's commit `ac10a78` ("fix(sim): update stale DTOs and
interfaces to match implemented schemas") rewrote the shared DTOs and enums
to match the new Project Guide v1.0 (ADR-005). This required a frontend sync.

---

## What Changed (8 files)

| File | Change | Description |
|------|--------|-------------|
| `src/types/api.ts` | **Rewritten** | All enums updated: `ActionType` 13→15 (lowercase StrEnum), `WealthClass` 6→3 (`poor/middle/rich`). Added 6 new enums: `NeedType` (13), `EmotionType` (5), `Gender` (2), `Culture` (3), `EducationLevel` (4), `JobType` (12). `SimulationStateResponseDTO` +8 fields (`food_availability`, `water_availability`, `crime_rate`, `protest_intensity`, `unemployment_rate`, `tax_rate`, `welfare_enabled`, `welfare_amount`). `AgentDetailDTO` +28 fields (identity, psychology, behavioral, economic, grid, social, `last_reasoning`). `AgentSummaryDTO` +3 (`emotion`, `unlust`, `job_type`). `PolicyCreateRequestDTO` +`policy_text`. `PolicyResponseDTO` +`impact_deltas`. `MetricsResponseDTO` +4 series + 2 distributions. WebSocket events: `event_type`→`type` discriminator, simplified payloads. Added `PolicyRevokeResponseDTO`, `AgentHistoryResponseDTO`. |
| `src/services/api.ts` | **Fixed** | `revokePolicy` return type → `PolicyRevokeResponseDTO` (was `PolicyResponseDTO`). `getAgentHistory` return type → `AgentHistoryResponseDTO` (was `unknown[]`). |
| `src/components/agents/AgentList.tsx` | **Fixed** | Typed `agents` prop as `AgentSummaryDTO[]` (was `any[]`). Replaced `agent.lastActionTick` (doesn't exist) with `agent.emotion`. |
| `src/components/agents/AgentDetail.tsx` | **Fixed** | Typed `agent` state as `AgentDetailDTO \| null`. Replaced old fields: `wealth`→`money`, `employmentStatus`→`employment_status`, `happiness`→`happiness_score`. Removed `recentActions` (doesn't exist), added `last_action` + `last_reasoning` display. Added `emotion`, `unlust`, `wealth_class`, `job_type` to state grid. |
| `src/components/policies/PolicyList.tsx` | **Fixed** | Typed `policies` prop as `PolicyResponseDTO[]`. Replaced `policy.enactedAt` → `policy.enactment_tick`. |
| `src/components/dashboard/MetricsPanel.tsx` | **Fixed** | Typed `metrics` prop as `SimulationStateResponseDTO \| null`. Replaced old fields (`happiness`, `crimeRate`, `gdp`) with real flat metrics (`economic_health`, `public_order`, `social_cohesion`, `unlust`, `morality`, `crime_rate`, `unemployment_rate`). |
| `src/contexts/SimulationContext.tsx` | **Fixed** | Typed `state` and `metrics` as `SimulationStateResponseDTO \| null` (was `any`). |

---

## Enum Changes Summary

| Enum | Before | After | Type |
|------|--------|-------|------|
| `ActionType` | 13 values, UPPERCASE | 15 values, lowercase (`work`, `buy_food`, `steal`, `harm_other`…) | `StrEnum` |
| `WealthClass` | 6 values, UPPERCASE | 3 values, lowercase (`poor`, `middle`, `rich`) | `StrEnum` |
| `PolicyCategory` | 8 values | 8 values (unchanged) | `Enum` |
| `EmploymentStatus` | 5 values | 5 values (unchanged) | `Enum` |
| `EmotionType` | — | 5 values (`happy`, `normal`, `sad`, `angry`, `despair`) | `StrEnum` (new) |
| `NeedType` | — | 13 values (Maslow hierarchy) | `StrEnum` (new) |
| `Gender` | — | 2 values (`male`, `female`) | `StrEnum` (new) |
| `Culture` | — | 3 values (`A`, `B`, `C`) | `StrEnum` (new) |
| `EducationLevel` | — | 4 values (0–3) | `IntEnum` (new) |
| `JobType` | — | 12 values (11 jobs + `unemployed`) | `StrEnum` (new) |

---

## WebSocket Update

**Resolved:** Backend commit `37765c3` wired `ws_manager.broadcast()` into
`advance_tick()`. The `/ws` endpoint now broadcasts real events (was echo-only).

**Message format** (differs from `shared/events/simulation_events.py` dataclasses):
```json
{"type": "tick_completed", "tick": 5, "population": 1000}
{"type": "agent_acted", "agent_id": "1", "action": "work"}
```

Frontend WS types updated to use `"type"` discriminator with simplified payloads.

---

## Verification

| Gate | Command | Result |
|------|---------|--------|
| Lint | `npm run lint` | ✅ No ESLint warnings or errors |
| Typecheck | `npm run typecheck` (`tsc --noEmit`) | ✅ Clean |
| Build | `npm run build` (`next build`) | ✅ Compiled successfully, 6/6 pages generated |

---

## Cross-Team Flags (Updated)

1. ~~**Backend — WebSocket broadcast not wired.**~~ **RESOLVED** ✅ —
   Backend now broadcasts `tick_completed` and `agent_acted` events.

2. **Tech Lead — contracts/openapi.yaml still stale.** The OpenAPI spec and
   `contracts/schemas/*.json` do not match `shared/dto/*` (which were updated
   in `ac10a78`). The frontend treats `shared/dto/*` as the source of truth.
   **Action: Tech Lead to reconcile `contracts/` with `shared/dto/`.**

3. **Backend — `_state_to_dto()` only maps 9 of 17 `SimulationStateResponseDTO` fields.**
   The 8 new fields (`food_availability`, `water_availability`, etc.) will return
   defaults until the backend populates them from the simulation state.
   **Action: Backend Engineer to map all fields in `_state_to_dto()`.**

4. **Backend — `_agent_to_detail()` only maps 12 of ~40 `AgentDetailDTO` fields.**
   The 28 new fields will return defaults until the backend populates them.
   **Action: Backend Engineer to map all fields in `_agent_to_detail()`.**

5. **New AI endpoints available** (not yet in frontend `apiService`):
   `POST /api/v1/translate-policy`, `/tie-break`, `/generate-news`,
   `/generate-persona`, `/generate-narration`. Relevant for PR 2+ features
   (news feed, policy translation, agent stories).
