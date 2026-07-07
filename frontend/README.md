# Frontend — Dashboard & Visualization

**Owner:** Frontend Engineer

Provides the user interface for monitoring and interacting with the SOCIETAS simulation. Renders real-time agent activity, economic charts, policy impact reports, and the news feed.

## Responsibilities

- Real-time simulation dashboard
- Agent state visualization and exploration
- Economic charts and metrics (time-series, distributions)
- News feed and narrative display
- Policy configuration interface
- Policy impact reports
- Spotlight agent story viewer

## Technology

- TypeScript + React (or Next.js)
- Charting library for real-time data
- WebSocket client for live updates
- Component library consistent with project design system

## Dependencies

- `backend/` — consumes REST + WebSocket APIs

## Conventions

- Components in `src/components/`
- Pages in `src/pages/`
- Hooks in `src/hooks/`
- Tests co-located with components (`Component.test.tsx`)

## Related

- [Coding Standards](../docs/guides/coding-standards.md)
- [Architecture Overview](../docs/references/architecture-overview.md)
- [Feature Specs](../vault/060-Features/)
