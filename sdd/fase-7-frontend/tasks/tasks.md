# Tasks: fase-7-frontend — Frontend Dashboard SPA

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~1800–2200 (25+ new frontend files + 2 backend fixes) |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 (scaffold + types + api + stores) → PR 2 (components) → PR 3 (pages + hooks) → PR 4 (backend fixes + tests + Makefile) |
| Delivery strategy | ask-on-risk |
| Chain strategy | stacked-to-main |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: stacked-to-main
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | Project scaffold, types, API client, Zustand stores | PR 1 → main | Base foundation; no backend deps |
| 2 | Reusable UI components (Layout, StatusDot, Sparkline, etc.) | PR 2 → main | Depends on PR 1 types/stores |
| 3 | Pages (Login, Register, Dashboard, ServerNew, ServerDetail) + WS hook | PR 3 → main | Depends on PR 2 components |
| 4 | Backend fixes (WS mount, CORS), smoke tests, Makefile update | PR 4 → main | Small; ties frontend to backend |

---

## Phase 1: Project Scaffold (PR 1)

- [ ] 1.1 Create `frontend/package.json` with dependencies: vite, react 18, react-router-dom, recharts, lucide-react, react-hook-form, @hookform/resolvers, zod, zustand, vitest, @testing-library/react, @testing-library/jest-dom, jsdom, @vitejs/plugin-react, tailwindcss, postcss, autoprefixer
- [ ] 1.2 Create `frontend/vite.config.ts` with `/api` proxy to `localhost:8000` and react plugin
- [ ] 1.3 Create `frontend/tsconfig.json` (strict mode, paths aliases for `@/` → `src/`)
- [ ] 1.4 Create `frontend/tailwind.config.ts` with dark theme tokens: bg `#0e1116`, card `#1a1c23`, accent `#3b82f6`, green `#22c55e`, red `#ef4444`; extend colors, add responsive grid breakpoints
- [ ] 1.5 Create `frontend/postcss.config.js`
- [ ] 1.6 Create `frontend/index.html` with `<div id="root">` and dark body styles
- [ ] 1.7 Create `frontend/index.css` with `@tailwind base/components/utilities` and `:root` CSS vars for theme
- [ ] 1.8 Create `frontend/src/vite-env.d.ts`
- [ ] 1.9 Create `frontend/src/main.tsx` mounting App with React 18 strict mode
- [ ] 1.10 Create `frontend/src/App.tsx` with react-router-dom Routes: `/login`, `/register`, `/` (dashboard), `/servers/new`, `/servers/:id`; protect all except login/register
- [ ] 1.11 Create `frontend/.env.example` with `VITE_API_BASE_URL=http://localhost:8000`
- [ ] 1.12 Create `frontend/src/types/index.ts` — TypeScript types matching backend Pydantic schemas: `ServerResponse`, `ServerWithToken`, `MetricResponse`, `UserResponse`, `TokenResponse`, `WsMessage`

## Phase 2: API Client + Stores (PR 1)

- [ ] 2.1 Create `frontend/src/api/client.ts` — fetch wrapper with JWT from localStorage, `Authorization: Bearer <token>` injection, 401 redirect to `/login`, configurable base URL via `VITE_API_BASE_URL`
- [ ] 2.2 Create `frontend/src/api/auth.ts` — `login(email, password)`, `register(email, password)`, `me()` using client.ts
- [ ] 2.3 Create `frontend/src/api/servers.ts` — `list()`, `get(id)`, `create(name, hostname)`, `delete(id)`, `regenerateToken(id)` using client.ts
- [ ] 2.4 Create `frontend/src/api/metrics.ts` — `query(serverId, range)` with range param (1h/6h/24h) using client.ts
- [ ] 2.5 Create `frontend/src/stores/authStore.ts` — Zustand store: `token`, `user`, `isAuthenticated`, `login(token, user)`, `logout()`, rehydrate from localStorage on init
- [ ] 2.6 Create `frontend/src/stores/serversStore.ts` — Zustand store: `servers[]`, `setServers()`, `addServer()`, `removeServer(id)`, `updateMetric(serverId, metric)`, `updateStatus(serverId, status)`
- [ ] 2.7 Create `frontend/src/stores/uiStore.ts` — Zustand store: `theme`, `toasts[]`, `addToast()`, `removeToast()`

## Phase 3: Components (PR 2)

- [ ] 3.1 Create `frontend/src/components/Layout.tsx` — dark bg shell with sidebar/header; children prop; nav links to dashboard and "new server"
- [ ] 3.2 Create `frontend/src/components/StatusDot.tsx` — green/red dot with animated pulse CSS for online; size prop
- [ ] 3.3 Create `frontend/src/components/Sparkline.tsx` — mini Recharts LineChart (no axes, no tooltip, 60px tall) showing last 20 data points; takes `data: number[]` and `color`
- [ ] 3.4 Create `frontend/src/components/MetricChart.tsx` — Recharts LineChart with XAxis (time), YAxis (%), grid, tooltip; takes `data`, `dataKey`, `color`, `unit`; supports 1h/6h/24h via TimeRangeSelector
- [ ] 3.5 Create `frontend/src/components/TimeRangeSelector.tsx` — button group (1h/6h/24h); selected range highlighted in accent blue; onChange callback
- [ ] 3.6 Create `frontend/src/components/ConfirmModal.tsx` — portal modal with title, message, cancel/confirm buttons; confirm variant destructive (red); ESC to close
- [ ] 3.7 Create `frontend/src/components/CopyButton.tsx` — clipboard copy button with check icon feedback for 2s after copy; takes `text` prop

## Phase 4: Pages + Hooks (PR 3)

- [ ] 4.1 Create `frontend/src/pages/LoginPage.tsx` — email/password form via react-hook-form + zod (email required, password min 8); call `api.auth.login()`; on success store JWT in authStore and redirect to `/`; show inline error on failure; no layout wrapper
- [ ] 4.2 Create `frontend/src/pages/RegisterPage.tsx` — email/password/confirm form via react-hook-form + zod; call `api.auth.register()`; on success redirect to `/login`; show validation errors; no layout wrapper
- [ ] 4.3 Create `frontend/src/pages/DashboardPage.tsx` — fetch `GET /api/v1/servers` on mount; responsive card grid (1/2/3 cols); each card: name, hostname, StatusDot, CPU sparkline, RAM sparkline, uptime, relative last_seen; click navigates to `/servers/:id`; Layout wrapper
- [ ] 4.4 Create `frontend/src/pages/ServerNewPage.tsx` — name + hostname form; call `POST /api/v1/servers`; on 201 display `api_token` once with CopyButton and agent install snippet; Layout wrapper
- [ ] 4.5 Create `frontend/src/pages/ServerDetailPage.tsx` — fetch server and metrics on mount; 4 MetricChart components (CPU %, RAM %, disk %, net bytes/s); TimeRangeSelector above charts; regenerate token button; delete button → ConfirmModal → `DELETE /api/v1/servers/:id` → redirect to `/`; Layout wrapper
- [ ] 4.6 Create `frontend/src/hooks/useLiveMetrics.ts` — connect to `WS /api/v1/ws?token=<jwt>`; on `metric` msg call `serversStore.updateMetric`; on `status_change` call `serversStore.updateStatus`; on disconnect start 15s HTTP polling via `setInterval`; cleanup on unmount; return `{isConnected}`
- [ ] 4.7 Create `frontend/src/hooks/useAuth.ts` — `useAuth()` returning `{ user, isAuthenticated, login, logout }` from authStore

## Phase 5: Backend Fixes (PR 4 — small, fast)

- [ ] 5.1 In `backend/app/main.py`: add `from app.api.ws import router as ws_router` and `app.include_router(ws_router, prefix="/api/v1", tags=["ws"])` after existing routers — mounts the WS endpoint
- [ ] 5.2 In `backend/app/main.py`: add `from fastapi.middleware.cors import CORSMiddleware` and `app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])` after app creation — enables Vite dev server to call API directly

## Phase 6: Tests + Makefile (PR 4)

- [ ] 6.1 Create `frontend/vitest.config.ts` — test environment jsdom, setup files `@testing-library/jest-dom`
- [ ] 6.2 Create `frontend/src/tests/setup.ts` — imports `@testing-library/jest-dom` matchers
- [ ] 6.3 Create `frontend/src/tests/LoginPage.test.tsx` — render LoginPage, assert email+password inputs present; submit with invalid data shows validation
- [ ] 6.4 Create `frontend/src/tests/DashboardPage.test.tsx` — mock `api.servers.list()` with vi.fn(), render DashboardPage, assert server cards displayed
- [ ] 6.5 In `Makefile`: add `frontend-dev`, `frontend-test`, `frontend-lint`, `frontend-format` targets; update `clean` to also `rm -rf frontend/node_modules frontend/dist`

## Phase 7: Verification

- [ ] 7.1 Run `npm install` in frontend and confirm all packages resolve
- [ ] 7.2 Run `npm run dev` (backend running) — confirm Vite starts, proxy works, no console errors
- [ ] 7.3 Manual smoke: register → login → dashboard shows cards → create server → detail page charts render
- [ ] 7.4 Run `npm test` in frontend — all smoke tests pass
- [ ] 7.5 Commit all 4 PRs and push

## Dependency Order

```
PR 1 (scaffold + types + api + stores)
  └── PR 2 (components — depend on types/stores from PR 1)
        └── PR 3 (pages + hooks — depend on components from PR 2)
              └── PR 4 (backend fixes + tests + Makefile — small, independent)
```

Each PR is self-contained, reviewable in under 30 minutes, and can land independently.