# Design: fase-10-monitoring

## Technical Approach

Wire `prometheus-fastapi-instrumentator` into the FastAPI lifespan, add a `docker-compose.monitoring.yml` overlay with Prometheus and Grafana services, and provide Grafana provisioning files for zero-config datasource + dashboard. Prometheus scrapes `backend:8000/metrics`; Grafana auto-provisions on first boot.

## Architecture Decisions

| Decision | Choice | Alternative | Rationale |
|----------|--------|-------------|-----------|
| Instrumentation library | `prometheus-fastapi-instrumentator` | Custom Prometheus client | Already in pyproject.toml; auto-instruments request count, latency, status codes |
| Compose overlay | Separate `docker-compose.monitoring.yml` | Add to main compose | Keeps monitoring optional; dev/prod can opt in with `-f` flag |
| Grafana port | `3001:3000` (host 3001) | Default 3000 | Avoids conflict with frontend dev server on 3000 |
| Dashboard provisioning | File-based JSON | Provision via API | File-based survives container recreation; zero config on boot |
| Prometheus retention | Default 15d | Custom 30d+ | Acceptable for scope; defers storage sizing |

## Data Flow

```
Agent ──POST──→ Backend :8000 ──/metrics──→ Prometheus :9090 ──PromQL──→ Grafana :3001
                                              │
                                              └─ scrape_interval: 15s
```

1. Agent posts metrics → backend (existing flow)
2. `prometheus-fastapi-instrumentator` auto-instruments all FastAPI endpoints
3. `/metrics` exposes `http_requests_total`, `http_request_duration_seconds`, `http_responses_total`
4. Prometheus scrapes `/metrics` every 15s via Docker DNS `backend:8000`
5. Grafana queries Prometheus via internal URL `http://prometheus:9090`

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `backend/app/main.py` | Modify | Add instrumentator setup + expose `/metrics` in lifespan startup |
| `docker-compose.monitoring.yml` | Create | Prometheus + Grafana services on `serverpulse_net` |
| `monitoring/prometheus.yml` | Create | Scrape config: `backend:8000/metrics` every 15s |
| `monitoring/grafana/datasources/datasource.yml` | Create | Auto-provision Prometheus datasource |
| `monitoring/grafana/dashboards/dashboard.yml` | Create | Dashboard provisioning: load from `/etc/grafana/provisioning/dashboards` |
| `monitoring/grafana/dashboards/serverpulse.json` | Create | Pre-built dashboard: request rate, latency p50/p95/p99, 5xx rate, uptime |

## Interfaces / Contracts

### main.py instrumentation wiring

```python
from prometheus_fastapi_instrumentator import Instrumentator

# After app creation, before lifespan:
instrumentator = Instrumentator().instrument(app)

# Inside lifespan startup:
@asynccontextmanager
async def lifespan(app: FastAPI):
    instrumentator.expose(app, endpoint="/metrics")
    # ... existing startup logic ...
    yield
    # ... existing shutdown logic ...
```

The instrumentator must be created **after** `app = FastAPI(...)` but `.expose()` called inside the lifespan startup to guarantee `/health` checks can succeed before metrics collection begins.

### Grafana datasource

```yaml
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
```

### Dashboard panels

| Panel | Metric | Legend |
|-------|--------|--------|
| Request Rate | `rate(http_requests_total[5m])` | per-endpoint |
| Latency p50 | `histogram_quantile(0.5, rate(http_request_duration_seconds_bucket[5m]))` | — |
| Latency p95 | `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))` | — |
| Latency p99 | `histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))` | — |
| Error Rate (5xx) | `rate(http_responses_total{status_code=~"5.."}[5m])` | — |

## Testing Strategy

| Layer | What | Approach |
|-------|------|----------|
| Unit | `/metrics` endpoint returns 200 with metrics body | httpx `TestClient` against app, assert `http_requests_total` present |
| Integration | Prometheus scrapes backend | `docker compose -f ... up`, curl `localhost:9090/api/v1/targets`, assert UP |
| E2E | Grafana dashboard shows data | `docker compose -f ... up`, curl Grafana datasource health, query dashboard API |

## Migration / Rollout

No migration required. Monitoring is an additive overlay:
- `docker compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d` to enable
- `docker compose -f docker-compose.monitoring.yml down` to disable
- `/metrics` endpoint on backend is read-only, no side effects on existing flow

## Open Questions

- None. All decisions resolved in proposal phase.