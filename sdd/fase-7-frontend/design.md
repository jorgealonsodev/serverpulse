# Design: Fase 7 — Frontend Dashboard

## Technical Approach

Build a Vite + React 18 + TypeScript + TailwindCSS 3 SPA that connects to the existing FastAPI backend (Fases 0-6). The frontend is a thin client: a `fetch`-based API client with JWT interceptor, Zustand stores for auth/server state, a WebSocket hook with polling fallback for realtime metrics, and five pages (Login, Register, Dashboard, ServerNew, ServerDetail) using Recharts for charts, react-hook-form + zod for validation, and lucide-react for icons. Dark theme via TailwindCSS custom tokens matching Grafana palette. All new code lives in `frontend/` — no backend changes.

**Prerequisite**: The WS router (`app/api/ws.py`) exists but is NOT mounted in `app/main.py`. It must be registered at `/api/v1/ws` before the frontend can use realtime updates. This is a one-line backend fix.

## Architecture Decisions

### Decision: SPAs with fetch wrapper (no axios)

| Option | Tradeoff | Decision |
|--------|----------|----------|
| axios | More features, interceptors built-in, larger bundle | ✗ Rejected |
| fetch + thin wrapper | Zero deps, tree-shakeable, native, sufficient | ✓ Chosen |

**Rationale**: The app only needs JWT injection and error coercion. A 15-line `request<T>()` wrapper handles both. No point adding axios for features we don't use.

### Decision: Zustand over Context or Redux

| Option | Tradeoff | Decision |
|--------|----------|----------|
| React Context | Built-in, no deps, but no selectors — all consumers re-render | ✗ Rejected |
| Redux Toolkit | Heavy boilerplate, overkill for 2 stores | ✗ Rejected |
| Zustand | 1KB, selectors, minimal API, WS updates fit naturally | ✓ Chosen |

**Rationale**: Two stores (auth, servers) with fine-grained updates from WS messages. Zustand selectors prevent unnecessary re-renders when a single server's metric updates.

### Decision: localStorage for JWT

| Option | Tradeoff | Decision |
|--------|----------|----------|
| httpOnly cookie | XSS-safe, but requires backend changes (Fase 8+) | ✗ Deferred |
| localStorage | XSS-vulnerable, but no backend changes needed | ✓ Chosen |

**Rationale**: PRD scope accepts this trade-off. No sensitive data beyond the token. Worth re-evaluating when Nginx reverse proxy lands (Fase 8).

### Decision: WebSocket + polling fallback

| Option | Tradeoff | Decision |
|--------|----------|----------|
| SSE | Simpler, unidirectional — matches our read-only use case | ✗ Backend uses WS |
| Pure polling | No WS state, but 15s staleness | ✗ Poor UX |
| WS primary + 15s poll fallback | Realtime when connected, graceful degradation | ✓ Chosen |

**Rationale**: Backend already has Redis pub/sub → WS. The `useLiveMetrics()` hook connects WS first; on close/error it falls back to `setInterval` hitting `GET /servers/{id}/metrics`.

### Decision: TailwindCSS tokens over CSS-in-JS

| Option | Tradeoff | Decision |
|--------|----------|----------|
| styled-components | Runtime cost, bundle size | ✗ Rejected |
| CSS modules | No utility classes, verbose | ✗ Rejected |
| TailwindCSS + CSS variables | Zero runtime, utility-first, theme via `:root` vars | ✓ Chosen |

**Rationale**: PRD mandates TailwindCSS 3. Theme tokens as CSS variables let us swap themes later without touching components.

## Data Flow

```
Login/Register ──→ api.auth.login() ──→ localStorage + authStore
                                              │
AuthGuard ◄────────────────────────────────────┘
  │
Dashboard ──→ api.servers.list() ──→ serversStore
  │               │
  │               useLiveMetrics()
  │               ├── WS ws://host/api/v1/ws?token=<jwt>
  │               │    ├── onmessage → serversStore.updateMetric()
  │               │    └── onmessage → serversStore.updateStatus()
  │               └── onclose → polling fallback (15s interval)
  │
  └── Card click ──→ ServerDetail
                      └── api.servers.get(id)
                      └── api.metrics.query(id, range) → Recharts LineCharts
                      └── regenerate/delete → api.servers.*
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `frontend/package.json` | Create | Vite + React 18 + TS scaffold with deps: react-router-dom, recharts, lucide-react, react-hook-form, @hookform/resolvers, zod, zustand. Dev: vitest, @testing-library/react, @testing-library/jest-dom, jsdom, tailwindcss, postcss, autoprefixer, eslint, prettier |
| `frontend/vite.config.ts` | Create | Proxy `/api` → `http://localhost:8000`, proxy `/api/v1/ws` for WS |
| `frontend/tailwind.config.js` | Create | Dark theme tokens: bg-primary `#0e1116`, bg-card `#1a1c23`, border `#2a2d37`, accent `#3b82f6`, success `#22c55e`, danger `#ef4444` |
| `frontend/postcss.config.js` | Create | TailwindCSS + autoprefixer plugins |
| `frontend/tsconfig.json` | Create | Strict TS config |
| `frontend/index.html` | Create | Vite HTML entry |
| `frontend/src/main.tsx` | Create | React 18 createRoot, render App |
| `frontend/src/App.tsx` | Create | React Router v6: routes for /login, /register, /, /servers/new, /servers/:id. AuthGuard wrapping protected routes |
| `frontend/src/index.css` | Create | Tailwind directives + CSS custom properties for theme |
| `frontend/src/api/client.ts` | Create | `request<T>()` fetch wrapper with JWT from localStorage, `ApiError` class, `api` object with auth/servers/metrics methods |
| `frontend/src/stores/authStore.ts` | Create | Zustand: `token`, `user`, `isAuthenticated`, `login()`, `logout()`, `setUser()` |
| `frontend/src/stores/serversStore.ts` | Create | Zustand: `servers[]`, `setServers()`, `updateMetric()`, `updateStatus()` |
| `frontend/src/stores/uiStore.ts` | Create | Zustand: `theme` (dark) |
| `frontend/src/hooks/useLiveMetrics.ts` | Create | WS hook: connects `/api/v1/ws?token=`, parses `metric`/`status_change` messages, updates serversStore. On close: 15s polling fallback |
| `frontend/src/hooks/useAuth.ts` | Create | Redirect helpers: `useAuth()` returns `{ isAuthenticated, user, login, logout }` |
| `frontend/src/components/Layout.tsx` | Create | Navbar + main content area, responsive sidebar on mobile |
| `frontend/src/components/StatusDot.tsx` | Create | Animated dot: green pulse for online, red for offline |
| `frontend/src/components/Sparkline.tsx` | Create | Tiny Recharts `AreaChart`, 60px height, no axes, just the area line |
| `frontend/src/components/MetricChart.tsx` | Create | Full Recharts `LineChart` with time axis, tooltip, responsive container |
| `frontend/src/components/TimeRangeSelector.tsx` | Create | 3 buttons: 1h, 6h, 24h. Active state styling |
| `frontend/src/components/ConfirmModal.tsx` | Create | Reusable modal with cancel/confirm actions |
| `frontend/src/components/CopyButton.tsx` | Create | Button that copies text to clipboard, shows "Copied!" feedback |
| `frontend/src/pages/Login.tsx` | Create | Login form: email + password, react-hook-form + zod, error display, link to register |
| `frontend/src/pages/Register.tsx` | Create | Register form: email + password, zod validation, redirect to login |
| `frontend/src/pages/Dashboard.tsx` | Create | Grid of server cards (1 col mobile, 2-3 col desktop). Each card: name, hostname, StatusDot, sparklines, uptime, relative time. Click → /servers/:id |
| `frontend/src/pages/ServerNew.tsx` | Create | Create server form. On success: show api_token once + agent install command snippet + CopyButton |
| `frontend/src/pages/ServerDetail.tsx` | Create | Server info, 4 MetricCharts (CPU, RAM, disk, net), TimeRangeSelector, regenerate token (modal), delete (ConfirmModal) |
| `frontend/src/types/index.ts` | Create | TypeScript interfaces matching backend Pydantic schemas: `ServerResponse`, `ServerWithToken`, `MetricResponse`, `UserResponse`, `TokenResponse`, WS message types |
| `docker-compose.dev.yml` | Create | Frontend service: Vite dev server on port 5173, volume mount for hot reload |
| `Makefile` | Modify | Add `dev` target to start backend + frontend concurrently |

## Interfaces / Contracts

```typescript
// types/index.ts — matches backend Pydantic schemas exactly

interface UserResponse { id: string; email: string }
interface TokenResponse { access_token: string; token_type: string }
interface RegisterRequest { email: string; password: string }
interface LoginRequest { email: string; password: string }

interface ServerResponse {
  id: string; name: string; hostname: string | null;
  last_seen_at: string | null; status: "online" | "offline";
  created_at: string;
}
interface ServerWithToken extends ServerResponse { api_token: string }
interface ServerCreate { name: string; hostname?: string }

interface MetricResponse {
  id: number; server_id: string;
  cpu_percent: number; ram_percent: number;
  ram_used_mb: number; ram_total_mb: number;
  disk_percent: number; disk_used_gb: number; disk_total_gb: number;
  net_rx_bytes: number; net_tx_bytes: number;
  uptime_seconds: number;
  load_avg_1: number | null; load_avg_5: number | null; load_avg_15: number | null;
  recorded_at: string; received_at: string;
}

// WS message types
type WsMetricMessage = {
  type: "metric"; server_id: string; data: MetricResponse;
}
type WsStatusMessage = {
  type: "status_change"; server_id: string; status: "online" | "offline";
}
type WsMessage = WsMetricMessage | WsStatusMessage;
```

```typescript
// api/client.ts — API contract

class ApiError extends Error {
  constructor(public status: number, public data: Record<string, unknown>) { super(); }
}

const api = {
  auth: {
    register: (data: RegisterRequest) => request<UserResponse>("/auth/register", { method: "POST", body: JSON.stringify(data) }),
    login: (data: LoginRequest) => request<TokenResponse>("/auth/login", { method: "POST", body: JSON.stringify(data) }),
    me: () => request<UserResponse>("/auth/me"),
  },
  servers: {
    list: () => request<ServerResponse[]>("/servers"),
    get: (id: string) => request<ServerResponse>(`/servers/${id}`),
    create: (data: ServerCreate) => request<ServerWithToken>("/servers", { method: "POST", body: JSON.stringify(data) }),
    delete: (id: string) => request<void>(`/servers/${id}`, { method: "DELETE" }),
    regenerateToken: (id: string) => request<ServerWithToken>(`/servers/${id}/regenerate-token`, { method: "POST" }),
  },
  metrics: {
    query: (serverId: string, from: string, to: string) =>
      request<MetricResponse[]>(`/servers/${serverId}/metrics?from=${encodeURIComponent(from)}&to=${encodeURIComponent(to)}`),
  },
};
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | `api/client.ts` error handling, token injection | Vitest + `vi.fn()` mock fetch |
| Unit | Zustand stores: auth login/logout, server state updates | Vitest, direct store calls |
| Unit | `useLiveMetrics` hook: WS connect, message parse, fallback | `@testing-library/react-hooks`, mock WebSocket |
| Smoke | Each page renders without crash | React Testing Library, mock api module |
| Integration | Login → redirect, Dashboard → cards render, ServerDetail → charts | React Testing Library + MemoryRouter |

Tests are written AFTER components exist (per PRD phase scope: smoke tests only for Fase 7).

## Migration / Rollout

No migration required. Frontend is stateless — `git revert` of the commit reverts cleanly with no data impact. If WS causes issues, the polling fallback runs independently.

## Open Questions

- [ ] **WS router not mounted**: `app/api/ws.py` exists with full implementation but `app/main.py` does NOT `include_router` for it. Backend needs one line: `app.include_router(ws_router, prefix="/api/v1")`. Must be fixed before frontend WS can work.
- [ ] **CORS middleware**: Backend has `CORS_ORIGINS` env var but no `CORSMiddleware` in `main.py`. Vite dev proxy avoids this in dev; production nginx (Fase 8) avoids it in prod. But if anyone runs frontend on a different port without the proxy, CORS blocks will occur. Consider adding middleware in this phase or Fase 8.