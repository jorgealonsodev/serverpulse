# Frontend Dashboard Specification

## Purpose

Web SPA for sysadmins to authenticate, manage servers, and view realtime metrics. Backend (Fases 0-6) provides REST API and WebSocket endpoints.

## Requirements

### Requirement: Project Scaffold (FS7-REQ-01)

The system MUST provide a Vite + React 18 + TypeScript + TailwindCSS 3 project. Dependencies: react-router-dom, recharts, lucide-react, react-hook-form, @hookform/resolvers, zod, zustand. `vite.config.ts` MUST proxy `/api` to `localhost:8000`.

#### Scenario: Dev server with proxy

- GIVEN a local backend on port 8000
- WHEN `npm run dev` executes
- THEN Vite starts and proxies `/api` requests to `localhost:8000`

### Requirement: API Client (FS7-REQ-02)

The system MUST provide a fetch-based API client that reads JWT from `localStorage` and adds `Authorization: Bearer <token>` to every request. Base URL MUST be configurable via `VITE_API_BASE_URL`.

#### Scenario: Authenticated request includes JWT

- GIVEN a JWT exists in `localStorage`
- WHEN any API call is made
- THEN `Authorization: Bearer <token>` header is included

#### Scenario: Unauthenticated request redirects

- GIVEN no JWT in `localStorage`
- WHEN a protected API call returns 401
- THEN user is redirected to `/login`

### Requirement: Login Page (FS7-REQ-03)

`/login` MUST present email/password form validated with react-hook-form + zod. On valid submit it MUST call `POST /api/v1/auth/login`, store JWT, redirect to `/`.

#### Scenario: Successful login

- GIVEN valid credentials
- WHEN form is submitted
- THEN JWT is stored and user is redirected to `/`

#### Scenario: Invalid credentials

- GIVEN incorrect credentials
- WHEN form is submitted
- THEN error message displays and user stays on `/login`

### Requirement: Register Page (FS7-REQ-04)

`/register` MUST present email/password/confirm form. On valid submit it MUST call `POST /api/v1/auth/register` and redirect to `/login`.

#### Scenario: Successful registration

- GIVEN a new email and matching passwords
- WHEN form is submitted
- THEN 201 response and redirect to `/login`

#### Scenario: Duplicate email

- GIVEN an already-registered email
- WHEN form is submitted
- THEN validation error is displayed

### Requirement: Dashboard (FS7-REQ-05)

`/` MUST fetch `GET /api/v1/servers` and render a responsive card grid. Each card MUST show: server name, hostname, status dot (green=online, red=offline, animated pulse for online), CPU sparkline, RAM sparkline, formatted uptime ("5d 3h 22m"), relative last update ("hace 12s"). Clicking a card navigates to `/servers/:id`.

#### Scenario: Renders server cards

- GIVEN authenticated user with servers
- WHEN dashboard loads
- THEN card grid displays all server data

#### Scenario: Responsive layout

- GIVEN varying viewport widths
- WHEN rendered on mobile / md / lg
- THEN grid shows 1 / 2 / 3 columns respectively

### Requirement: Server Create Page (FS7-REQ-06)

`/servers/new` MUST present name + hostname form calling `POST /api/v1/servers`. On success, it MUST display `api_token` once with copy-to-clipboard button and agent install command.

#### Scenario: Server created with token

- GIVEN valid form submission
- WHEN server is created (201)
- THEN `api_token` is shown once with copy button and install snippet

### Requirement: Server Detail Page (FS7-REQ-07)

`/servers/:id` MUST display 4 line charts (CPU %, RAM %, disk %, net bytes) from `GET /api/v1/servers/{id}/metrics`, time range selector (1h/6h/24h), regenerate token button, and delete button with confirmation modal.

#### Scenario: Metrics with time range

- GIVEN user navigates to `/servers/:id`
- WHEN page loads
- THEN 4 charts render with 1h data; selecting 6h/24h re-fetches

#### Scenario: Delete with confirmation

- GIVEN user clicks delete
- WHEN confirmation modal appears and is confirmed
- THEN `DELETE /api/v1/servers/{id}` is called and redirect to `/`

### Requirement: WebSocket Hook (FS7-REQ-08)

`useLiveMetrics()` MUST connect to `WS /api/v1/ws?token=<jwt>`, update Zustand store on `metric` and `status_change` messages, and fall back to HTTP polling every 15s on disconnect.

#### Scenario: Real-time update

- GIVEN live WebSocket connection
- WHEN `metric` message arrives
- THEN corresponding server card updates immediately

#### Scenario: Polling fallback

- GIVEN WebSocket disconnects
- THEN HTTP polling begins every 15s until WS reconnects

### Requirement: State Management (FS7-REQ-09)

The system MUST provide three Zustand stores: `authStore` (token, user, login/logout), `serversStore` (server list, updateMetric), `uiStore` (theme, toasts).

#### Scenario: Auth persistence across refresh

- GIVEN JWT in localStorage
- WHEN app reloads
- THEN authStore rehydrates and user remains authenticated

### Requirement: Dark Theme (FS7-REQ-10)

The UI MUST use dark theme: background `#0e1116`, cards `#1a1c23`, blue accent `#3b82f6`, green status `#22c55e`, red status `#ef4444`. Responsive grid: 1 col mobile, 2 md, 3 lg.

#### Scenario: Consistent dark palette

- GIVEN any page renders
- WHEN user views it
- THEN all elements use the dark palette consistently

### Requirement: Tests (FS7-REQ-11)

Vitest + React Testing Library smoke tests MUST verify Login renders and Dashboard renders with mocked data.

#### Scenario: Login smoke test

- GIVEN test environment
- WHEN `Login` component renders
- THEN email and password inputs are present

#### Scenario: Dashboard smoke test

- GIVEN mocked server data
- WHEN `Dashboard` renders
- THEN server cards are displayed