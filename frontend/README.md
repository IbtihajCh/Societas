# Frontend Dashboard

Next.js 14 real-time dashboard for visualizing simulation state, agent behavior, and policy effects.

## Key Files

- `src/app/dashboard/page.tsx` — Main simulation dashboard
- `src/components/MetricsPanel.tsx` — Key metrics and charts
- `src/components/SimulationControls.tsx` — Start/stop/step controls
- `src/services/api.ts` — Typed Axios client for backend API
- `src/types/api.ts` — TypeScript DTOs (mirrors `shared/dto/`)

## How to Run

```bash
npm install
npm run dev
```

Open http://localhost:3000 (requires backend on :8000).

## How to Test

```bash
npm test
```

## Dependencies

- Next.js 14, React 18, TypeScript
- Zustand, Recharts, Axios
