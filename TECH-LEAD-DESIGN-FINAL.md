# SOCIETAS — Tech Lead Design Final

> Comprehensive design specification for the SOCIETAS frontend dashboard.
> Theme: Logo-inspired palette — Earthy nature + technology aesthetic.
> Grid: 30x30 canvas scatter-plot with wealth-coloured rings and emotion-coloured bodies.
> Twin panel system: pre-built + custom.

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│  TOPBAR: Logo (48×48) · SOCIETAS · Dateline · Controls · Bell │
├─────────────────────────────────────────────────────────────┤
│  POLICY BAR: Read-only chips (TAX 15% × / SUBSIDY 0% × …)   │
├──────────────────────────────┬──────────────────────────────┤
│                              │                              │
│  WORLD PANE (scrollable)     │  DOCK PANE (scrollable)      │
│  ┌─ Citizen Census ──────┐   │  ┌─ Panel toolbar ────────┐  │
│  │ ring=wealth · body=emo│   │  │ + Add Panel │ + Custom   │  │
│  ├───────────────────────┤   │  ├────────────────────────┤  │
│  │   30×30 Canvas Grid    │   │  │  panel content …        │  │
│  │   (agents as circles)  │   │  │  panel content …        │  │
│  │   4 gold corner ────── │   │  │  …                      │  │
│  ├───────────────────────┤   │  └────────────────────────┘  │
│  │ Legend: Rings + Body   │   │                              │
│  └───────────────────────┘   │                              │
│                              │                              │
├──────────────────────────────┴──────────────────────────────┤
│  TOAST stack · DOSSIER slide-in                              │
└─────────────────────────────────────────────────────────────┘
```

### Key Metrics
- Grid cells: 30×30 = 900 positions
- Default agent count: 80 (fetched), up to 1000 (backend)
- Panel count: 11 (7 default, 4 addable), plus unlimited custom
- Custom panel metrics: 30 selectable
- Docker services: frontend (Next.js 14) + backend (FastAPI)
- Backend bugs fixed during development: 4

---

## 2. Theme System — Logo-Inspired Palette

Derived from `societas_logo_v2.png` — a circular emblem split vertically:
- **Left half**: Reddish grid (structure, technology)
- **Right half**: Olive-green tree (nature, growth)
- **Outer ring**: Gold/bronze

### Variable Mapping

| CSS Variable | Hex | Logo Element |
|-------------|-----|--------------|
| `--oxblood` | `#78231D` | Deep Brick Red — left grid, outer ring, nodes |
| `--moss` | `#7A7417` | Olive Green — leaves, vines, alternating nodes |
| `--ochre` | `#A86E26` | Bronze/Copper — gradients, highlights |
| `--gold` | `#A86E26` | Bronze accent (same as ochre) |
| `--slate` | `#462612` | Dark Brown — tree branches, outlines |
| `--cream` | `#0A0604` | Near-black background |
| `--parchment` | `#130D08` | Very dark brown panel bg |
| `--parchment-2` | `#1A100A` | Dock pane container (kept brown for contrast) |
| `--ink` | `#E8DCC4` | Warm cream primary text |
| `--ink-soft` | `#A08868` | Medium brown muted text |
| `--rule` | `#2E1A0C` | Dark brown borders |
| `--black` | `#000000` | Pure black |

### Dual-Color System
- **Panels**: `#181810` (olive-tinted — adds a subtle greenish note)
- **Dock container**: `#1A100A` (dark brown — creates contrast)
- **Topbar**: `#0E0C08` (olive-tinted near-black)
- **Navbar**: `#111505` (more greenish tint)
- **Policy bar**: `#141605` (greenish brown)
- **World-head (Citizen Census)**: `#131408` (greenish dark)
- **Grid frame**: `#0A0806` (deep greenish black)

### Wealth Ring Colours

| Class | Hex | Visual |
|-------|-----|--------|
| Poor | `#5C3A28` | Muted brown |
| Middle | `#8B6448` | Medium bronze-brown |
| Rich | `#A86E26` | Bright bronze + thicker ring |
| Owner | `#2A3A18` core + `#A86E26` rim | Dark olive with bronze rim |

### Emotion Body Colours

| Emotion | Hex | Visible on dark bg |
|---------|-----|-------------------|
| Happy | `#7A7417` Olive | ✅ |
| Neutral | `#A08868` Warm cream | ✅ |
| Sad | `#462612` Brown | ✅ (lighter than bg) |
| Angry | `#78231D` Brick red | ✅ |
| Stressed | `#A86E26` Bronze | ✅ |

---

## 3. Home Page (`/`)

### Layout
- Centered hero: Logo (100×100) → "Societas" (title) → "World Ledger" (subtitle)
- Description: "Agent-based civilisation simulation on a 30x30 grid."
- Setup card: Population slider (5–200), Seed slider, AI toggle
- CTA: "start simulation" button
- Stop → redirects back via `Router.push('/')`

### Files
- `frontend/src/pages/index.tsx` — setup screen + logo
- Logo at `/societas_logo_v2.png` in public folder

---

## 4. Dashboard Layout (`/dashboard`)

### Topbar (68px)
- **Logo**: 48×48 raw PNG, no border/ring (just the image)
- **Brand**: "SOCIETAS" in 20px bold Fraunces
- **Dateline**: `YEAR 1 · DAY 1 · 19:00 · DUSK · MARKET`
- **Controls**: Step / Auto Run / Speed (0.5x–4x) / Pause / Stop / Save / Load
- **Bell**: Notification dropdown with unread badge, wired to `crime_committed`/`policy_applied`/`protest`

### Policy Bar (42px)
- Read-only chips: `TAX 15% ×`, `SUBSIDY 0% ×`, `WELFARE OFF ×`
- Custom enacted policies appear as chips with inline × revoke
- All editing happens in the Governance panel (no inline sliders)

### World Pane (left 50%)
- **Citizen Census** header: "Citizen Census" + "ring = wealth · body = emotion"
- **30×30 canvas grid** with 4 gold corner brackets (`.corner.tl/tr/bl/br`)
- **Legend inside frame**: Rings (Poor/Middle/Rich/Owner) + Body (Happy/Neutral/Sad/Angry/Stressed)
- Both columns independently scrollable

### Dock Pane (right 50%)
- **Dock toolbar**: `2 panels open` label + `+ Add Panel` dropdown + `+ Custom Panel` button
- **11 panels**: all visible by default, drag-reorderable, × closable
- **Add Panel dropdown**: categorized (Overview/Citizens/Governance/Economy/Model/Custom), smooth opacity/translateY animation

---

## 5. Agent Grid — 30×30 Canvas Scatter-Plot

### Canvas
- Full-world-frame canvas (fills left column)
- 30×30 logical grid cells
- Grid lines at `var(--rule)` 0.1 opacity, 1px
- DPR-aware rendering (`window.devicePixelRatio`)
- `imageSmoothingEnabled = false` for crisp rendering

### Agent Rendering
Each agent is a **simple coloured circle** — no face features:
- **Outer ring stroke** (1.5–2px) = wealth class colour
- **Body fill** = emotion colour
- Rich/owner get thicker ring (2px) + gold rim stroke

### Positioning
- Agents placed at `(grid_x, grid_y)` from backend
- Fallback for new agents: index-based `col = i % GRID, row = Math.floor(i / GRID)`
- 1000+ agents distributed across 30×30 grid

### Interaction
- Hover: nearest agent within `CELL × 0.5` → tooltip with ID/emotion/wealth/age/job/unlust
- Click: select agent → dashed ring + opens Dossier slide-in
- Selected: dashed gold ring

### Animation
- `breathe-glow`: 4s cycle on world-frame box-shadow
- `pulse-corner`: 3s cycle on corner brackets
- `scanlines`: 8s horizontal line scroll overlay

---

## 6. Panel System

### Pre-Built Panels (11 total)

| ID | Title | Category | Default |
|----|-------|----------|---------|
| metrics | Metrics & Gauges | Overview | ✅ |
| gov | Governance & Policies | Governance | ✅ |
| entrylog | Entry Log · News | Overview | ✅ |
| wealth | Wealth Stratification | Economy | ✅ |
| diagnostics | Diagnostics | Citizens | ❌ |
| environmental | Environmental Events | Overview | ❌ |
| community | Community Status | Citizens | ❌ |
| actualization | Self-Actualization | Citizens | ❌ |
| modellog | Model Log | Model | ❌ |
| explain | Explain | Model | ❌ |
| memory | Memory Browser | Model | ❌ |

### Panel Features
- **Drag-reorder**: HTML5 drag/drop on `panel-head`, drops via `drop` event
- **Close**: `×` button removes from `openPanels` array
- **Re-open**: Add Panel dropdown shows only closed panels, categorized
- **Panel cards**: `height: auto; flex-shrink: 0` — size to content
- **Hover**: `border-color: var(--rule-strong)` subtle glow

### Custom Panel Builder
- `+ Custom Panel` button opens builder form
- Name the panel (text input)
- Pick up to 3 metrics from 30 available
- Each selected metric shows: label + current value + sparkline (gold line)
- Created panels appear in "Custom" category in Add Panel dropdown
- 30 metrics include: population, economic_health, social_cohesion, crime_rate, unlust, unemployment_rate, morality, public_order, innovation_index, food_availability, water_availability, protest_intensity, environmental_quality, tax_rate, welfare_amount, avg_happiness, avg_wealth, gini_coefficient, life_expectancy, birth_rate, death_rate, literacy_rate, avg_education, property_ownership, business_count, avg_trust_govt, good_acts_total, crimes_total, divorce_rate, avg_age

---

## 7. Metrics Panel

### Top Row — 6 Stat Cards
Equally spaced with thin vertical `var(--rule)` dividers.

| Card | Key | Format |
|------|-----|--------|
| POPULATION | population | `{v}` (integer) |
| ECONOMIC HEALTH | economic_health | `(v??0).toFixed(2)` |
| EMPLOYMENT | unemployment_rate (inverted) | `((v??0)*100).toFixed(1)+'%'` |
| CRIME RATE | crime_rate (inverted) | `((v??0)*100).toFixed(1)+'%'` |
| SOCIAL COHESION | social_cohesion | `(v??0).toFixed(2)` |
| MORALITY | morality | `(v??0).toFixed(2)` |

Each card:
- Label (10px, uppercase, `--ink-soft`, `font-variant-numeric: tabular-nums`)
- Value (22px, bold, `--ink`, mono)
- Delta/steady text (moss=up, oxblood=down, ink-soft=steady)
- Sparkline (50×20 gold line, from store history)

### Bottom Row — 4 Ring Gauges

| Label | Key |
|-------|-----|
| ECON | economic_health |
| COHESION | social_cohesion |
| MORALITY | morality |
| SAFETY | public_order |

Gauge spec:
- 96×96 SVG, R=36
- Track: full circle, `var(--rule)` stroke, 5px
- Arc: 260° sweep starting at -130°, colored by threshold (>0.7 moss, >0.4 ochre, else oxblood)
- Center: `(value × 100).toFixed(0) + '%'` in 16px bold
- Label: 10px uppercase `--ink-soft`

---

## 8. Metrics (All Available Backend Fields)

The tick response includes:

```typescript
SimulationStateResponseDTO {
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
  duration_ms: number;
  ai_calls: number;
  ambiguity_count: number;
  state_hash: string;
  action_counts: Record<string, number>;
  wealth_stratified: { poor: number; middle: number; rich: number };
  llm_log: any[];
  news_articles: NewsArticle[];
}
```

Additional computed metrics available through the store:
`avg_happiness, avg_wealth, gini_coefficient, life_expectancy, birth_rate, death_rate, literacy_rate, avg_education, property_ownership, business_count, avg_trust_govt, good_acts_total, crimes_total, divorce_rate, avg_age`

---

## 9. Animations & Interactive Effects

### Background Ambient (z-index: –1)
| Effect | Implementation | Timing |
|--------|---------------|--------|
| Canvas particles | 40 drifting dots (bronze/olive/oxblood), 1–2px | ~8s drift cycle |
| Floating dots | 8 CSS `@keyframes float-up` dots | 8s stagger |
| Grid scanlines | `repeating-linear-gradient` overlay on `.world-frame::after` | 8s linear |
| Background grid | `grid-drift` on `.bg-grid-overlay` | 120s linear |

### Interactive (z-index: 100)
| Effect | Implementation | Trigger |
|--------|---------------|--------|
| Mouse glow | 600px radial gradient spotlight | Mouse move |
| Panel hover | `border-color: var(--rule-strong)` | Hover panel |

### Structural (no z-index change)
| Effect | Timing | Target |
|--------|--------|--------|
| breathe-glow | 4s ease-in-out | `.world-frame` box-shadow |
| pulse-corner | 3s ease-in-out | `.world-frame .corner` |
| subtle-breathe | 6s ease-in-out | `.shell` |
| Toast enter | 0.25s ease | `.toast` |
| Dropdown fade | 0.12s ease | `.add-menu` |
| All transitions | 0.15s ease | Buttons, chips, tabs, panels |
| Panel mount | 0.5s ease fade-in | `.panel` |

### Accessibility
All animations disabled via `prefers-reduced-motion: reduce` media query.

---

## 10. Component Tree

```
pages/dashboard.tsx
├── bg-particles (8 floating dots)
├── bg-particle-canvas (40 drifting dots, canvas)
├── mouse-glow (cursor spotlight)
├── shell
│   ├── topbar (crest img · SOCIETAS · dateline · controls · bell + notif-dropdown)
│   ├── policybar (read-only chips + × revoke)
│   ├── app-body
│   │   ├── world-pane
│   │   │   ├── world-head (Citizen Census title + subtitle)
│   │   │   ├── world-frame
│   │   │   │   ├── AgentGrid (30×30 canvas)
│   │   │   │   └── corner brackets (tl/tr/bl/br)
│   │   │   └── world-legend (Rings + Body colours)
│   │   └── dock-pane
│   │       ├── dock-toolbar (panel count + Add Panel dropdown + Custom Panel button)
│   │       └── dock-content
│   │           ├── panel × N (drag-reorderable)
│   │           ├── custom panel × N (if created)
│   │           └── custom-panel-builder (if open)
│   ├── toast-stack
│   └── dossier (slide-in, if agent selected)
└── AnimatedBackground (CSS only)
```

---

## 11. Agent DTO (`/agents/:id` response)

All fields available through `apiService.getAgent(agentId)`:

```
id, persona, traits (morality/creativity/ambition/resilience/dominance/anger/extraversion/risk),
needs (creativity/autonomy/purpose/food/water/sleep/safety/social/family/romantic/self-esteem/sexual/status),
emotions (intensity map), resources (money, salary, employed, education, property, health, etc.),
employment_status, wealth_class, age, age_bracket, is_alive, location, last_action, last_reasoning,
social_connections, gender, culture, born_tick, unlust, happiness_score, emotion, emotion_timer,
good_acts, crimes_committed, notoriety, trust_in_govt, protest_count, money, base_salary, employed,
education, property, health, job_type, grid_x, grid_y, spouse, enemies, parent_ids, children_ids,
community_id, recent_actions, memories
```

---

## 12. Docker Setup

### Services
| Service | Port | Dockerfile | Notes |
|---------|------|------------|-------|
| frontend | 3000 | `docker/frontend.Dockerfile` | Next.js 14, `node:20-alpine` |
| backend | 8000 | `docker/backend.Dockerfile` | FastAPI, `python:3.14-slim` |
| simulation | — | `docker/simulation.Dockerfile` | Disabled in override |
| vllm | 8001 | `docker/vllm-rocm.Dockerfile` | Disabled in override |

### Commands
```bash
# Build + start
docker compose -f docker/docker-compose.yml -f docker/docker-compose.override.yml -p societas build frontend
docker compose -f docker/docker-compose.yml -f docker/docker-compose.override.yml -p societas up -d

# Rebuild frontend after changes
docker compose -f docker/docker-compose.yml -f docker/docker-compose.override.yml -p societas build frontend
docker compose -f docker/docker-compose.yml -f docker/docker-compose.override.yml -p societas up -d
```

### Health
```bash
curl http://localhost:8000/api/v1/health     → {"status":"healthy","service":"societas-backend"}
curl http://localhost:3000                   → HTTP 200 (Next.js SSR)
```

---

## 13. Backend Service Layer

```
backend/app/services/agent_service.py
  ├── get_agent(id) → AgentDetailDTO
  ├── list_agents(limit, offset) → AgentListResponseDTO
  └── _agent_to_detail(agent) → AgentDetailDTO (all fields)

backend/app/routers/
  ├── health.py        → GET /health
  ├── simulation.py    → GET|POST /simulation/start|stop|tick|state|reset
  ├── policies.py      → CRUD /policies
  ├── governance.py    → POST /governance/apply
  ├── metrics.py       → GET /metrics, /metrics/dashboard
  ├── agents.py        → GET /agents, /agents/:id, /agents/:id/history
  └── explain.py       → POST /explain
```

### Bugs Fixed

| File | Bug | Fix |
|------|-----|-----|
| `agent_service.py:87` | Duplicate `recent_actions=` kwarg in `AgentDetailDTO()` | Removed line 87, kept line 72's `recent_actions=recent_actions` |
| `simulation/events/__init__.py:12` | `MediaState` import doesn't exist | Removed import |
| `simulation/agents/memory_system.py` | `compute_memory_prompt` function missing | Added function returning formatted memory string |
| `shared/dto/agent_dto.py` | Missing fields: `age_bracket`, `debt`, `parent_ids`, `children_ids`, `memories` | Added all 5 fields |

---

## 14. Key CSS Classes Reference

| Class | Purpose | Key properties |
|-------|---------|---------------|
| `.shell` | Root container | `min-height: 100vh` |
| `.topbar` | Header bar | `fixed; 68px; z-index: 60; background: #0E0C08` |
| `.policybar` | Policy strip | `fixed; top: 68px; 42px; z-index: 50; background: #141605` |
| `.app-body` | Main grid | `fixed; top: 110px; bottom: 0; grid: 1fr 1fr` |
| `.world-pane` | Left column | `overflow-y: auto; height: 100%` |
| `.dock-pane` | Right column | `overflow-y: auto; height: 100%; background: #1A100A` |
| `.world-frame` | Grid container | `flex: 1; position: relative; background: #0A0806` |
| `.panel` | Panel card | `background: #181810; height: auto; flex-shrink: 0` |
| `.panel-head` | Panel handle | `flex; padding: 6px 10px; cursor: grab` |
| `.drag-dots` | Drag handle | `3×2 inline-grid; 3px dots; opacity: 0.4` |
| `.mouse-glow` | Cursor spotlight | `600px radial gradient; pointer-events: none; z-index: 100` |
| `.bg-particle-canvas` | Particle field | `fixed; full-viewport; z-index: -1; pointer-events: none` |
| `.add-menu` | Panel dropdown | `position: absolute; op/transform transition` |

---

## 15. Animation Keyframes

```css
@keyframes float-up           /* 8s — floating background dots */
@keyframes scanlines          /* 8s — CRT scanline overlay */
@keyframes breathe-glow       /* 4s — grid border pulsing */
@keyframes pulse-corner       /* 3s — corner bracket opacity */
@keyframes subtle-breathe     /* 6s — dashboard opacity */
@keyframes toastUp            /* 0.25s — toast enter */
@keyframes toastFade          /* 0.3s — toast exit */
@keyframes fade-in            /* 0.5s — panel mount */
@keyframes slide-in-right     /* 0.3s — dossier panel */
@keyframes pulse-glow         /* 2s — stamp dot */
@keyframes grid-drift         /* 120s — background grid */
@keyframes shimmer            /* — loading states */
```

---

## 16. Git History

```
b605d72 feat: alive-simulation animations — floating particles, scanlines, breathe glow, pulse corners
6791b26 feat: home page, dashboard refinements, AgentGrid/SimulationContext/globals.css updates, clipboard assets
5cf95c3 feat: dashboard overhaul with Dune-ledger aesthetic, new panels, wealth-stratified chart, dark imperial theme
e1a347d docs: add MASTER_DESIGN.md — comprehensive system specification for Claude prompt refinement
31a1be3 feat(fe): integrate Sparkline + WorldGauge into dashboard, dark-theme GovernanceCard, gauge strip for KPIs
de842fa feat(fe): dark imperial theme — animated background, gold constellation particles, translucent panels
```

---

## 17. Environment & Dependencies

### Frontend
- Next.js 14.2.35 (pages router)
- React 18
- TypeScript 5
- recharts (wealth stratification chart)
- Zustand (state management)

### Backend
- FastAPI
- Uvicorn
- Pydantic v2
- SQLAlchemy (async)
- numpy

### Infrastructure
- Docker 29.6.1
- Docker Compose v5.2.0
- Node.js 20 (alpine)
- Python 3.14 (slim)
