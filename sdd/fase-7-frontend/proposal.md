# Proposal: Fase 7 — Frontend Dashboard

## Intent

Build the ServerPulse web dashboard so a sysadmin can register, log in, manage servers, and view realtime metrics. Backend (Fases 0-6) is complete; the frontend directory exists but is empty scaffolding.

## Scope

### In Scope
- Vite + React 18 + TypeScript + TailwindCSS 3 project scaffold
- Pages: `/login`, `/register`, `/` (Dashboard), `/servers/new`, `/servers/:id`
- API client with JWT interceptor (fetch-based, no axios dependency)
- `useLiveMetrics()` WebSocket hook with polling fallback (15s)
- Dark theme (Grafana palette: bg `#0e1116`, blue/green accents)
- Recharts for line charts, sparklines on dashboard cards
- react-hook-form + zod for form validation
- React Router v6 for routing
- Zustand for auth state + server list state
- Vite dev proxy to `localhost:8000`
- Mobile-responsive layout (1 col mobile, 2-3 col desktop)

### Out of Scope
- Component libraries (MUI, Ant Design, etc.)
- E2E tests (Playwright) — deferred to later phase
- Unit tests for components — smoke tests only per PRD
- Nginx production build — Fase 8
- CI/CD frontend jobs — Fase 9

## Capabilities

### New Capabilities
- `frontend-dashboard`: Vite + React SPA with auth, server CRUD UI, realtime metrics via WS, dark theme, responsive layout

### Modified Capabilities
- None

## Approach

1. **Scaffold**: `npm create vite@latest` with React + TS, install TailwindCSS 3, Recharts, lucide-react, react-router-dom, react-hook-form, @hookform/resolvers, zod, zustand
2. **API Client**: thin `fetch` wrapper in `src/api/client.ts` with JWT interceptor reading from `localStorage`. Base URL proxied via `vite.config.ts`
3. **Auth Flow**: JWT stored in `localStorage` (per PRD scope). Zustand store holds `token`, `user`, `isAuthenticated`. Protected route wrapper redirects to `/login`
4. **WebSocket Hook**: `useLiveMetrics()` connects to `WS /api/v1/ws?token=<jwt>`, listens for `metric` and `status_change` messages, updates Zustand store. On disconnect, retries with exponential backoff, falls back to HTTP polling every 15s
5. **Pages**:
   - Login/Register: forms with react-hook-form + zod validation, error display
   - Dashboard: fetches server list, renders grid of cards with status indicator, CPU/RAM sparklines (Recharts AreaChart), formatted uptime, relative timestamp
   - ServerNew: create form → shows `api_token` once with copy button + agent install command snippet
   - ServerDetail: 4 Recharts line charts (CPU, RAM, disk, net), time range selector (1h/6h/24h), regenerate token, delete with confirmation
6. **Theme**: TailwindCSS config with custom colors matching Grafana palette, dark mode by default

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `frontend/` | New | Full Vite + React project with all pages, components, hooks, types |
| `frontend/vite.config.ts` | New | Dev server with proxy to backend `localhost:8000` |
| `frontend/tailwind.config.js` | New | TailwindCSS config with Grafana dark theme colors |
| `docker-compose.dev.yml` | Modified | Add frontend service with Vite dev server |
| `Makefile` | Modified | Add `make dev` target for frontend + backend hot reload |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| WS connection failures in dev | Medium | Polling fallback every 15s, clear error UI |
| JWT in localStorage XSS risk | Low | Acceptable per PRD scope; no sensitive data beyond token |
| Recharts performance with many data points | Medium | Limit query to 2880 points (backend already enforces), downsample if needed |
| TailwindCSS 3 vs 4 confusion | Low | Explicitly pin v3 in package.json |

## Rollback Plan

1. `git revert` the single commit `feat(frontend): dashboard with realtime charts`
2. No database changes — frontend is stateless, safe to revert without data impact
3. If WS hook causes issues, disable it temporarily — polling fallback is always available

## Dependencies

- Backend API running on `localhost:8000` (Fases 0-6 complete)
- Node.js 20+ and npm/pnpm installed locally
- All backend endpoints verified: auth, servers CRUD, metrics query, WebSocket

## Success Criteria

- [ ] `npm run dev` starts Vite, proxy forwards to backend
- [ ] User can register → login → see authenticated dashboard
- [ ] User can create a server, see token once with copy button
- [ ] User can view server detail with 4 charts and time range selector
- [ ] WebSocket delivers realtime metric updates to dashboard cards
- [ ] WS disconnect triggers polling fallback (verified by stopping backend)
- [ ] Layout is responsive: 1 col on mobile, 2-3 col on desktop
- [ ] Dark theme applied consistently across all pages
