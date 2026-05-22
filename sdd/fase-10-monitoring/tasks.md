# Tasks: fase-10-monitoring — Prometheus + Grafana Monitoring Stack

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~120–180 (1 mod + 5 new) |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | ask-on-risk |
| Chain strategy | pending |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: pending
400-line budget risk: Low

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | Full monitoring stack | PR 1 | All files in one PR; self-contained additive feature |

---

## Phase 1: Infrastructure — Compose & Config Files

- [x] 1.1 Create `docker-compose.monitoring.yml` with `prometheus` (image `prom/prometheus:latest`, port `9090:9090`, volume `./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml`, network `serverpulse_net`) and `grafana` (image `grafana/grafana:latest`, port `3001:3000`, env `GF_SECURITY_ADMIN_PASSWORD=admin`, volumes for provisioning, network `serverpulse_net`)
- [x] 1.2 Create `monitoring/prometheus.yml` with scrape_config targeting `backend:8000/metrics` every 15s
- [x] 1.3 Create `monitoring/grafana/datasources/datasource.yml` — Prometheus datasource auto-provision (name: Prometheus, type: prometheus, access: proxy, url: `http://prometheus:9090`, isDefault: true)
- [x] 1.4 Create `monitoring/grafana/dashboards/dashboard.yml` — dashboard provisioning descriptor pointing to `/etc/grafana/provisioning/dashboards/serverpulse.json`
- [x] 1.5 Create `monitoring/grafana/dashboards/serverpulse.json` — Grafana dashboard with panels: Request Rate (`rate(http_requests_total[5m])`), Latency p50/p95/p99 (`histogram_quantile`), Error Rate 5xx (`rate(http_responses_total{status_code=~"5.."}[5m])`), Uptime

---

## Phase 2: Core Implementation — Backend /metrics Wiring

- [x] 2.1 Add `from prometheus_fastapi_instrumentator import Instrumentator` import to `backend/app/main.py`
- [x] 2.2 Instantiate `instrumentator = Instrumentator()` after `app = FastAPI(...)` in `backend/app/main.py`
- [x] 2.3 Call `instrumentator.instrument(app)` on the app instance (after creation, before lifespan)
- [x] 2.4 Inside `lifespan()` startup: call `instrumentator.expose(app, endpoint="/metrics")` before yield

---

## Phase 3: Testing — Verification Against Spec

- [ ] 3.1 Unit: test `GET /metrics` returns 200, `Content-Type: text/plain`, body contains `http_requests_total`
- [ ] 3.2 Integration: verify Prometheus scrapes backend target as UP (`curl localhost:9090/api/v1/targets`)
- [ ] 3.3 E2E: verify Grafana datasource health and dashboard panels render live data

---

## Phase 4: Cleanup — Documentation

- [x] 4.1 Confirm `.gitkeep` removed from `monitoring/grafana/dashboards/` (replaced by serverpulse.json)
- [x] 4.2 No dead code or temporary artifacts remain