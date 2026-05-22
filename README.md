# ServerPulse

[![CI](https://github.com/jorgealonsodev/serverpulse/actions/workflows/ci.yml/badge.svg)](https://github.com/jorgealonsodev/serverpulse/actions)

ServerPulse is an open-source platform for monitoring Linux servers from a single web dashboard.

Register an account, add servers with a one-liner install command, and watch CPU, RAM, disk, network, and load average metrics in real time — all from your browser.

![ServerPulse Dashboard](docs/img/dashboard.png)

## Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Backend API | Python + FastAPI | ≥0.110 |
| ORM | SQLAlchemy (async) | ≥2.0 |
| Validation | Pydantic + pydantic-settings | v2 |
| Database | PostgreSQL | 16 |
| Cache / Real-time | Redis | ≥5 (client) / 7 (server) |
| Auth | python-jose + passlib[bcrypt] | — |
| Frontend | React + Vite + TypeScript | ^18.3 / ^6.0 / ^5.7 |
| Charts | Recharts | ^2.15 |
| State | Zustand | ^5.0 |
| Forms | react-hook-form + zod | ^7.54 / ^3.24 |
| Styles | TailwindCSS | ^3.4 |
| Agent | Python 3.8+ (psutil + requests) | — |
| Containers | Docker + docker compose v2 | — |
| Reverse Proxy | Nginx | — |
| CI/CD | GitHub Actions | — |
| Monitoring | Prometheus + Grafana | — |

## Architecture

See [docs/architecture.md](docs/architecture.md) for the full C4 context diagram and component explanations.

## Quickstart

```bash
git clone https://github.com/jorgealonsodev/serverpulse.git
cd serverpulse
cp .env.example .env
make up
```

Open [http://localhost](http://localhost) in your browser.

## How to Add a Server

1. **Register** a user account at `http://localhost` (email + password, min 8 chars).
2. **Create a server** from the dashboard: click "New Server", give it a name and optional hostname.
3. **Copy the one-liner** install command shown on screen — it includes the server's API token.
4. **Run it on the target server** (requires `sudo` and Python 3.8+ with `psutil` and `requests`).

The agent sends metrics every 30 seconds via `POST /api/v1/metrics/ingest` authenticated with `X-Agent-Token`.

## Technical Decisions

| Decision | Chosen | Rejected | Why |
|----------|--------|----------|-----|
| Backend framework | FastAPI | Flask | Async-native, auto OpenAPI docs, Pydantic validation, better performance for I/O-bound workloads |
| Database | PostgreSQL | InfluxDB | Relational data (users, servers, tokens) is the primary concern; time-series metrics are manageable with proper indexes and a 24h retention policy |
| Real-time transport | WebSocket | Server-Sent Events | Bidirectional communication enables client-side keepalive and fits naturally with Redis pub/sub fan-out |
| ORM | SQLAlchemy 2.0 (async) | raw asyncpg | Type-safe models, Alembic migrations, familiar API; asyncpg used as the underlying driver |
| Agent dependencies | psutil + requests | Go binary | Simpler install on existing Python 3.8+ systems; no cross-compilation or binary distribution needed |
| Password hashing | passlib[bcrypt] | argon2 / plain hash | bcrypt is battle-tested, passlib provides a clean API, and it integrates well with FastAPI |
| Auth mechanism | JWT (HS256) | session cookies | Stateless tokens scale across containers; no shared session store required |
| Agent token auth | X-Agent-Token header | Bearer token | Separates agent identity from user identity; agents don't need JWT, just a per-server token |
| Frontend state | Zustand | Redux / Context API | Minimal boilerplate, no providers needed, perfect for a dashboard with a few stores |
| Container networking | Docker bridge network | host network | Isolation between services, portable across environments, healthcheck-based startup ordering |

## Roadmap

- [x] Fase 0 — Project setup
- [x] Fase 1 — Backend foundation (FastAPI, SQLAlchemy, Alembic)
- [x] Fase 2 — Auth (register, login, JWT)
- [x] Fase 3 — Server management (CRUD, agent tokens)
- [x] Fase 4 — Metrics ingest + query
- [x] Fase 5 — Frontend foundation (React, Vite, routing)
- [x] Fase 6 — Agent script (psutil + requests)
- [x] Fase 7 — Real-time dashboard (WebSocket + Redis pub/sub)
- [x] Fase 8 — Nginx reverse proxy (production-ready)
- [x] Fase 9 — CI/CD (GitHub Actions, lint, test, deploy)
- [x] Fase 10 — Monitoring (Prometheus + Grafana)
- [x] Fase 11 — Documentation and polish

### Future

- [ ] Email alerts for offline servers
- [ ] Multi-tenant support
- [ ] Custom alert thresholds per server
- [ ] Export metrics as CSV
- [ ] Mobile-responsive dashboard improvements
- [ ] Mobile app (React Native)

## License

MIT — see [LICENSE](LICENSE) for details.
