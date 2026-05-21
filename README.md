## ServerPulse

[![CI](https://github.com/<user>/serverpulse/actions/workflows/ci.yml/badge.svg)](https://github.com/<user>/serverpulse/actions)

## Description

Monitor multiple Linux servers from a single web dashboard.

<!-- TODO: Fase 11 -- Add dashboard screenshot here -->
<!-- ![ServerPulse Dashboard](docs/screenshot.png) -->

## Stack

<!-- TODO: Fase 1 -- Fill with actual versions once dependencies are set -->

| Layer | Technology |
|-------|-----------|
| Backend API | Python 3.11 + FastAPI |
| Database | PostgreSQL 16 |
| Cache / Real-time | Redis 7 |
| Migrations | Alembic |
| ORM | SQLAlchemy 2.0 (async) |
| Frontend | React 18 + Vite + TypeScript |
| Charts | Recharts |
| Styles | TailwindCSS 3 |
| Agent | Python 3.8+ (psutil + requests) |
| Containers | Docker + docker compose v2 |
| Reverse Proxy | Nginx |
| CI/CD | GitHub Actions |
| Monitoring | Prometheus + Grafana |

## Architecture

See [docs/architecture.md](docs/architecture.md) for the full architecture diagram and explanation.

<!-- TODO: Fase 11 -- Complete architecture.md -->

## Quickstart

```bash
make up
```

Open [http://localhost](http://localhost) in your browser.

<!-- TODO: Fase 8 -- Add production quickstart with HTTPS/certbot -->

## How to Add a Server

1. Register a user account in the dashboard.
2. Go to "New Server", give it a name, and create it.
3. Copy the one-liner install command shown on screen.
4. Run it on the target server (requires sudo).

<!-- TODO: Fase 6 -- Document the agent install one-liner -->

## Technical Decisions

<!-- TODO: Fase 11 -- Complete with real justifications -->

| Decision | Chosen | Rejected | Why |
|----------|--------|----------|-----|
| Backend framework | FastAPI | Flask | Async-native, auto OpenAPI docs, Pydantic validation |
| Database | PostgreSQL | InfluxDB | Relational data (users, servers) + time-series is manageable with indexes |
| Real-time | WebSocket | SSE | Bidirectional, better fit for pub/sub via Redis |
| ORM | SQLAlchemy 2.0 | raw asyncpg | Type-safe, migration support, familiar API |
| Agent deps | psutil + requests | Go binary | Simpler install on existing Python 3.8+ systems |

## Roadmap

<!-- TODO: Fase 11 -- Update roadmap as features are completed -->

- [ ] Email alerts for offline servers
- [ ] Multi-tenant support
- [ ] Custom alert thresholds per server
- [ ] Export metrics as CSV
- [ ] Mobile-responsive dashboard improvements

## License

MIT — see [LICENSE](LICENSE) for details.
