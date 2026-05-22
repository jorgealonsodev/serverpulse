# Proposal: Fase 10 — Monitoring (Prometheus + Grafana)

## Intent

Add observability to ServerPulse so operators can monitor backend health, request rates, latency, and error rates via Prometheus metrics and a pre-built Grafana dashboard. The backend already ships `prometheus-fastapi-instrumentator` as a dependency (pyproject.toml) but it is not wired up — `/metrics` does not exist yet.

## Scope

### In Scope
- Wire `prometheus-fastapi-instrumentator` in `backend/app/main.py` to expose `/metrics`
- `docker-compose.monitoring.yml` — Prometheus + Grafana services on `serverpulse_net`
- `monitoring/prometheus.yml` — scrape config targeting `backend:8000/metrics`
- `monitoring/grafana/provisioning/datasources/prometheus.yml` — auto-provisioned datasource
- `monitoring/grafana/dashboards/serverpulse.json` — pre-built dashboard (HTTP metrics, latency, error rate)
- Grafana provisioning: auto-load dashboard + datasource on startup
- Grafana exposed at `localhost:3001` (admin/admin)
- Commit: `feat(monitoring): prometheus and grafana stack`

### Out of Scope
- Alertmanager or alerting rules — deferred
- Agent-level Prometheus metrics — deferred
- Grafana user management or authentication hardening
- Custom application metrics beyond FastAPI instrumentator defaults

## Capabilities

### New Capabilities
- `monitoring-stack`: Prometheus scrapes backend `/metrics`, Grafana auto-provisions datasource + dashboard, accessible at `localhost:3001`

### Modified Capabilities
- `backend-api`: Wire prometheus-fastapi-instrumentator to expose `/metrics` endpoint

## Approach

1. **Backend `/metrics`**: Add `PrometheusFastAPIInstrumentator(app).instrument()` in `main.py` after `FastAPI()` instantiation. This auto-instruments request count, latency histograms, and response status codes.
2. **Prometheus compose**: `docker-compose.monitoring.yml` with `prom/prometheus:latest`, mount `monitoring/prometheus.yml`, expose port `9090`, join `serverpulse_net`. Scrape interval 15s.
3. **Grafana compose**: `grafana/grafana:latest` in same compose file, port `3001`, env `GF_SECURITY_ADMIN_PASSWORD=admin`, mount provisioning dirs for datasources and dashboards.
4. **Provisioning**: Grafana auto-provisions Prometheus datasource (URL `http://prometheus:9090`) and imports the dashboard JSON on first boot.
5. **Dashboard**: Single JSON dashboard with panels for request rate, latency p50/p95/p99, error rate (5xx), and uptime.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `backend/app/main.py` | Modified | Add Prometheus instrumentator wiring |
| `docker-compose.monitoring.yml` | New | Prometheus + Grafana services |
| `monitoring/prometheus.yml` | New | Scrape config for backend:8000 |
| `monitoring/grafana/provisioning/datasources/prometheus.yml` | New | Auto-provisioned datasource |
| `monitoring/grafana/dashboards/serverpulse.json` | New | Pre-built Grafana dashboard |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Backend `/metrics` not reachable by Prometheus | Low | Both on `serverpulse_net`, scrape target uses Docker DNS name `backend` |
| Grafana provisioning fails on first boot | Low | Use standard provisioning format (YAML + JSON), well-documented |
| Prometheus memory usage grows over time | Medium | Default retention is 15d; acceptable for dev/monitoring scope |

## Rollback Plan

1. `docker compose -f docker-compose.monitoring.yml down` — stops and removes monitoring containers
2. `git revert` the commit `feat(monitoring): prometheus and grafana stack`
3. No database changes, no persistent data loss (Prometheus data is in a volume, removed on `down -v`)
4. Backend `/metrics` endpoint removal is safe — it's read-only, no side effects

## Dependencies

- Backend running with `prometheus-fastapi-instrumentator` installed (already in pyproject.toml)
- Docker Compose v2 available
- Phases 0-9 complete (full stack operational)

## Success Criteria

- [ ] `GET /metrics` on backend returns Prometheus-format metrics (200)
- [ ] `docker compose -f docker-compose.monitoring.yml up -d` starts both services
- [ ] Prometheus at `localhost:9090` shows `backend:8000` as UP target
- [ ] Grafana at `localhost:3001` (admin/admin) shows pre-built dashboard with live data
- [ ] Dashboard panels display request rate, latency, and error rate metrics
