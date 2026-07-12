# Governance, Population & Morality Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix three bugs — population showing 0, food subsidy not updating UI, and morality avg missing sparkline

**Architecture:** Two backend Python fixes, two frontend TypeScript fixes

**Tech Stack:** FastAPI/Python (backend), Next.js/TypeScript (frontend)

## Global Constraints

- Must pass TypeScript compilation (`npx tsc --noEmit` in `frontend/`)
- No test breaks — run `pytest` in root
- Existing frontend UI behavior preserved

---

### Task 1: Fix population showing 0 before first tick

**Bug:** `SimulationStateResponseDTO.population` shows 0 because `SimulationState.population` defaults to 0 and is only set during `update_world_metrics()` (which runs each tick). The `/simulation/state` endpoint reads `state.population` directly from the `SimulationState` dataclass, which stays at 0 until the first tick completes.

**Files:**
- Modify: `backend/app/services/simulation_service.py:181`

**Interfaces:**
- Consumes: `simulation_service.py :: _state_to_dto(self, state, result)`
- Produces: `SimulationStateResponseDTO.population` correctly shows living agent count even before first tick

- [ ] **Step 1: Fix `_state_to_dto` to compute population from agents**

In `backend/app/services/simulation_service.py`, line 181:
```python
            population=state.population,
```
replace with:
```python
            population=len([a for a in agents if a.is_alive]),
```

- [ ] **Step 2: Verify compilation**

Run: `npx tsc --noEmit` (in `frontend/`) and `pytest tests/unit/backend/test_api.py -x -q`

- [ ] **Step 3: Commit**

```bash
git add backend/app/services/simulation_service.py
git commit -m "fix: population shows living agent count even before first tick"
```

---

### Task 2: Fix governance food subsidy not updating UI display

**Bug:** The governance page slider onChange calls `applyChanges()` which ignores the API response, so `simState` is never updated with the new `food_availability`. The World State Overview display (line 187) keeps showing the old value.

**Files:**
- Modify: `frontend/src/pages/governance.tsx:69-78`

- [ ] **Step 1: Fix `applyChanges` to update local state from response**

In `frontend/src/pages/governance.tsx`, change `applyChanges` (lines 69-78):
```typescript
  const applyChanges = useCallback(async (changes: Record<string, object>) => {
    try {
      await apiService.applyGovernance(changes);
      setApplyStatus('Applied ✓');
      setTimeout(() => setApplyStatus(''), 2000);
    } catch (err) {
      setApplyStatus('Failed to apply');
      console.error('Governance apply error:', err);
    }
  }, []);
```
to:
```typescript
  const applyChanges = useCallback(async (changes: Record<string, object>) => {
    try {
      const result = await apiService.applyGovernance(changes);
      setSimState(result);
      setApplyStatus('Applied ✓');
      setTimeout(() => setApplyStatus(''), 2000);
    } catch (err) {
      setApplyStatus('Failed to apply');
      console.error('Governance apply error:', err);
    }
  }, []);
```

This updates `simState` with the full response DTO (which includes the new `food_availability`), causing line 187 to display the updated value.

- [ ] **Step 2: Verify TypeScript compilation**

Run: `npx tsc --noEmit` (in `frontend/`)

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/governance.tsx
git commit -m "fix: governance apply updates local state from API response"
```

---

### Task 3: Fix morality avg missing sparkline (graph)

**Bug:** The "morality avg" StatBox in the dashboard (line 278) has no `history`/`historyKey` props, so it never renders a sparkline. Additionally, `MetricsHistoryEntry` has no `morality` field to track.

**Files:**
- Modify: `frontend/src/store/simulationStore.ts:15` (add `morality` to `MetricsHistoryEntry`)
- Modify: `frontend/src/store/simulationStore.ts:149-162` (add morality to `appendTickData`)
- Modify: `frontend/src/pages/dashboard.tsx:278` (add `history`/`historyKey` to StatBox)

- [ ] **Step 1: Add `morality` to `MetricsHistoryEntry`**

In `frontend/src/store/simulationStore.ts`, line 15 (after `avg_unlust`):
```typescript
export interface MetricsHistoryEntry {
  tick: number;
  economic_health: number;
  social_cohesion: number;
  crime_rate: number;
  protest_intensity: number;
  unemployment_rate: number;
  avg_unlust: number;
  morality: number;
  population: number;
}
```

- [ ] **Step 2: Add morality to `appendTickData`**

In the same file, in `appendTickData` function (around line 158), add after `avg_unlust: state.unlust,`:
```typescript
        morality: state.morality,
```

- [ ] **Step 3: Add sparkline props to morality StatBox**

In `frontend/src/pages/dashboard.tsx`, change line 278:
```typescript
<StatBox label="morality avg" value={fmt(s.morality)} delta={null} />
```
to:
```typescript
<StatBox label="morality avg" value={fmt(s.morality)} delta={null} history={metricsHistory} historyKey="morality" />
```

- [ ] **Step 4: Verify TypeScript compilation**

Run: `npx tsc --noEmit`

- [ ] **Step 5: Commit**

```bash
git add frontend/src/store/simulationStore.ts frontend/src/pages/dashboard.tsx
git commit -m "fix: add morality sparkline to dashboard stat box"
```

---

### Task 4: Fix frontend governance slider using hardcoded 0.85 base (bonus)

**Bug:** The dashboard governance handleGovernance (line 110) and the governance page handleApplyFoodSubsidy (line 115) both use a hardcoded base of `0.85` instead of the current `food_availability` from state.

**Files:**
- Modify: `frontend/src/pages/dashboard.tsx:110`
- Modify: `frontend/src/components/dashboard/GovernanceCard.tsx:29` (if exists)

- [ ] **Step 1: Fix dashboard handleGovernance**

In `frontend/src/pages/dashboard.tsx`, line 110:
```typescript
food_availability: Math.min(1, 0.85 + govSubsidy / 100),
```
Replace `0.85` with `state?.food_availability ?? 0.85`:
```typescript
food_availability: Math.min(1, (state?.food_availability ?? 0.85) + govSubsidy / 100),
```

- [ ] **Step 2: Fix GovernanceCard.tsx if it exists**

Read `frontend/src/components/dashboard/GovernanceCard.tsx` and replace any hardcoded `0.85` with the current state value.

- [ ] **Step 3: Verify TypeScript compilation**

Run: `npx tsc --noEmit`

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/dashboard.tsx
git commit -m "fix: governance uses current food_availability instead of hardcoded 0.85"
```
