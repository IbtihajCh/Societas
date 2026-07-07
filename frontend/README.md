# SOCIETAS Frontend

**Owner:** Frontend Engineer

## Purpose

React/Next.js dashboard for the SOCIETAS simulation. Provides real-time visualization of simulation state, agent behavior, and policy effects.

## Tech Stack

- **Framework:** Next.js 14 (React 18)
- **Language:** TypeScript
- **State Management:** Zustand
- **Charts:** Recharts
- **HTTP Client:** Axios
- **Styling:** CSS Modules

## Features

- Real-time simulation monitoring via WebSocket
- Dashboard with key metrics and charts
- Agent browser with detail view
- Policy management interface
- News and narrative feed
- Simulation controls (start/stop/step)

## Pages

- `/` - Home page with overview
- `/dashboard` - Main simulation dashboard
- `/policies` - Policy management
- `/agents` - Agent browser

## Components

### Dashboard
- `MetricsPanel` - Key metrics display
- `SimulationControls` - Start/stop/step controls
- `EventLog` - Real-time event feed

### Policies
- `PolicyList` - Active policies display
- `PolicyForm` - Policy creation form

### Agents
- `AgentList` - Agent browser
- `AgentDetail` - Agent detail view

## API Integration

All API calls go through `services/api.ts` which wraps Axios and provides typed methods for each endpoint.

## Development

```bash
npm install
npm run dev
```

Open http://localhost:3000

## Future Work

- Implement WebSocket connection for real-time updates
- Add chart components for metrics visualization
- Implement policy effect visualization
- Add agent behavior timeline
- Add news feed with AI-generated narratives
- Implement responsive design
- Add dark mode support
- Add export/import functionality
