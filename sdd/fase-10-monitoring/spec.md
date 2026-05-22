# Delta Spec: fase-10-monitoring

## ADDED Requirements — monitoring-stack

### Requirement: FS10-REQ-02 — docker-compose.monitoring.yml

The system SHALL provide a `docker-compose.monitoring.yml` override file with `prometheus` and `grafana` services on the `serverpulse_net` external network.

- Prometheus image: `prom/prometheus:latest`, port `9090:9090`, volume-mounted config.
- Grafana image: `grafana/grafana:latest`, port `3001:3000`, admin password via env, provisioning volumes mounted.

#### Scenario: Monitoring stack starts with core compose

- GIVEN the core `docker-compose.yml` stack is running
- WHEN `docker compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d` is executed
- THEN both `prometheus` and `grafana` containers start and join `serverpulse_net`
- AND Prometheus is reachable at `localhost:9090` and Grafana at `localhost:3001`

#### Scenario: Monitoring stack stops cleanly

- GIVEN the monitoring stack is running
- WHEN `docker compose -f docker-compose.monitoring.yml down` is executed
- THEN prometheus and grafana containers stop and are removed
- AND the core backend/database services remain unaffected

### Requirement: FS10-REQ-03 — Prometheus scrape configuration

The system SHALL provide `monitoring/prometheus.yml` that configures Prometheus to scrape `backend:8000/metrics` every 15 seconds.

#### Scenario: Prometheus discovers and scrapes the backend

- GIVEN prometheus and backend are on `serverpulse_net`
- WHEN prometheus starts with the provided config
- THEN prometheus scrapes `http://backend:8000/metrics` at 15-second intervals
- AND the target `backend:8000` appears as UP in the Prometheus targets page

#### Scenario: Backend is temporarily unreachable

- GIVEN prometheus is scraping `backend:8000/metrics`
- WHEN the backend container is temporarily down
- THEN prometheus marks the target as DOWN but continues scrape attempts
- AND existing historical data is preserved

### Requirement: FS10-REQ-04 — Grafana auto-provisioning

The system SHALL auto-provision Grafana with a Prometheus datasource and a pre-built ServerPulse dashboard on first boot.

#### Scenario: Datasource and dashboard provision on first start

- GIVEN the monitoring compose stack starts for the first time
- WHEN Grafana finishes initializing
- THEN a Prometheus datasource pointing to `http://prometheus:9090` exists
- AND a dashboard named "ServerPulse" is available with panels for request rate, latency (p50/p95/p99), error rate (5xx), and uptime

#### Scenario: Dashboard persists across restarts

- GIVEN Grafana has provisioned the dashboard once
- WHEN the Grafana container is restarted
- THEN the dashboard remains available without manual re-import

---

## MODIFIED Requirements — backend-api

### Requirement: FS10-REQ-01 — Prometheus /metrics endpoint

The backend API SHALL expose a `/metrics` endpoint returning Prometheus-format metrics, wired via `prometheus-fastapi-instrumentator`.

(Previously: /metrics endpoint was defined in PRD section 6 but not implemented)

#### Scenario: /metrics returns Prometheus metrics

- GIVEN the FastAPI app is running
- WHEN `GET /metrics` is requested
- THEN the response has status 200 with `Content-Type: text/plain`
- AND the body contains metrics prefixed with `http_` (request count, duration, status codes)

#### Scenario: Metrics track HTTP requests

- GIVEN `/metrics` is exposed and the app handles traffic
- WHEN several API requests are made (e.g., `GET /health`, `POST /api/v1/auth/login`)
- THEN `/metrics` increments request counters and latency histograms for those endpoints

---

## Verification — FS10-REQ-05

### Requirement: End-to-end monitoring verification

The monitoring stack MUST be verifiable with a single compose command producing a working Grafana dashboard with live data.

#### Scenario: Full stack verification

- GIVEN the core stack and monitoring stack are up (`docker compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d`)
- WHEN an operator opens `http://localhost:3001` and logs in with admin/admin
- THEN the ServerPulse dashboard is visible with live metrics from the backend