# API Reference

Base URL: `http://localhost` (via Nginx proxy) or `http://localhost:8000` (direct backend).

All timestamps are ISO 8601 UTC. All IDs are UUIDs (v4).

---

## Auth

### Register

```
POST /api/v1/auth/register
```

**Body:**
```json
{
  "email": "admin@example.com",
  "password": "securepassword"
}
```

| Field | Type | Constraints |
|-------|------|-------------|
| `email` | string | Valid email format |
| `password` | string | Min 8 characters |

**Response (201):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "admin@example.com"
}
```

**Status codes:**
- `201` — User created
- `409` — Email already registered
- `422` — Validation error

### Login

```
POST /api/v1/auth/login
```

**Body:**
```json
{
  "email": "admin@example.com",
  "password": "securepassword"
}
```

**Response (200):**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

**Status codes:**
- `200` — Login successful
- `401` — Invalid email or password
- `422` — Validation error

### Get Current User

```
GET /api/v1/auth/me
```

**Auth:** `Authorization: Bearer <jwt>`

**Response (200):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "admin@example.com"
}
```

**Status codes:**
- `200` — User data returned
- `401` — Not authenticated

---

## Servers

All server endpoints require JWT authentication via `Authorization: Bearer <jwt>`.

### Create Server

```
POST /api/v1/servers
```

**Body:**
```json
{
  "name": "web-prod-01",
  "hostname": "192.168.1.10"
}
```

| Field | Type | Constraints |
|-------|------|-------------|
| `name` | string | 1–100 characters |
| `hostname` | string \| null | Optional |

**Response (201):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "web-prod-01",
  "hostname": "192.168.1.10",
  "last_seen_at": null,
  "status": "offline",
  "created_at": "2025-01-15T10:30:00Z",
  "api_token": "sp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
}
```

The `api_token` is returned **only once** at creation time. Store it securely — it is needed for the agent to authenticate.

**Status codes:**
- `201` — Server created
- `401` — Not authenticated
- `422` — Validation error

### List Servers

```
GET /api/v1/servers
```

**Auth:** `Authorization: Bearer <jwt>`

**Response (200):**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "web-prod-01",
    "hostname": "192.168.1.10",
    "last_seen_at": "2025-01-15T10:32:00Z",
    "status": "online",
    "created_at": "2025-01-15T10:30:00Z"
  }
]
```

Status is computed from `last_seen_at`: `online` if last seen within 2 minutes, `offline` otherwise.

**Status codes:**
- `200` — List of servers
- `401` — Not authenticated

### Get Server Detail

```
GET /api/v1/servers/{id}
```

**Auth:** `Authorization: Bearer <jwt>`

**Response (200):** Same schema as list item.

**Status codes:**
- `200` — Server detail
- `401` — Not authenticated
- `404` — Server not found

### Delete Server

```
DELETE /api/v1/servers/{id}
```

**Auth:** `Authorization: Bearer <jwt>`

**Response:** No content (204).

**Status codes:**
- `204` — Server deleted
- `401` — Not authenticated
- `404` — Server not found

### Regenerate Token

```
POST /api/v1/servers/{id}/regenerate-token
```

**Auth:** `Authorization: Bearer <jwt>`

**Response (200):** Same as create, with a new `api_token`. The previous token is immediately invalidated.

**Status codes:**
- `200` — Token regenerated
- `401` — Not authenticated
- `404` — Server not found

---

## Metrics

### Ingest Metrics

```
POST /api/v1/metrics/ingest
```

**Auth:** `X-Agent-Token: <agent-token>` (header, not JWT)

**Body:**
```json
{
  "cpu_percent": 45.2,
  "ram_percent": 72.1,
  "ram_used_mb": 5832,
  "ram_total_mb": 8192,
  "disk_percent": 65.0,
  "disk_used_gb": 130.0,
  "disk_total_gb": 200.0,
  "net_rx_bytes": 1048576,
  "net_tx_bytes": 524288,
  "uptime_seconds": 86400,
  "load_avg_1": 1.25,
  "load_avg_5": 1.10,
  "load_avg_15": 0.95,
  "recorded_at": "2025-01-15T10:32:00Z"
}
```

| Field | Type | Constraints |
|-------|------|-------------|
| `cpu_percent` | float | 0–100 |
| `ram_percent` | float | 0–100 |
| `ram_used_mb` | int | ≥ 0 |
| `ram_total_mb` | int | ≥ 0 |
| `disk_percent` | float | 0–100 |
| `disk_used_gb` | float | ≥ 0 |
| `disk_total_gb` | float | ≥ 0 |
| `net_rx_bytes` | int | ≥ 0 |
| `net_tx_bytes` | int | ≥ 0 |
| `uptime_seconds` | int | ≥ 0 |
| `load_avg_1` | float \| null | Optional |
| `load_avg_5` | float \| null | Optional |
| `load_avg_15` | float \| null | Optional |
| `recorded_at` | datetime \| null | Optional; defaults to server time |

**Response (202):** No body.

**Status codes:**
- `202` — Metric accepted
- `401` — Missing or invalid agent token
- `422` — Validation error

### Query Server Metrics

```
GET /api/v1/servers/{id}/metrics?from=2025-01-15T00:00:00Z&to=2025-01-15T23:59:59Z
```

**Auth:** `Authorization: Bearer <jwt>`

**Query parameters:**
| Param | Type | Description |
|-------|------|-------------|
| `from` | datetime | Start of time range (required) |
| `to` | datetime | End of time range (required) |

Max range: 24 hours. Max results: 2880 points.

**Response (200):**
```json
[
  {
    "id": 1,
    "server_id": "550e8400-e29b-41d4-a716-446655440000",
    "cpu_percent": 45.2,
    "ram_percent": 72.1,
    "ram_used_mb": 5832,
    "ram_total_mb": 8192,
    "disk_percent": 65.0,
    "disk_used_gb": 130.0,
    "disk_total_gb": 200.0,
    "net_rx_bytes": 1048576,
    "net_tx_bytes": 524288,
    "uptime_seconds": 86400,
    "load_avg_1": 1.25,
    "load_avg_5": 1.10,
    "load_avg_15": 0.95,
    "recorded_at": "2025-01-15T10:32:00Z",
    "received_at": "2025-01-15T10:32:01Z"
  }
]
```

**Status codes:**
- `200` — Metrics returned
- `400` — Time range exceeds 24 hours
- `401` — Not authenticated
- `404` — Server not found

---

## WebSocket

```
WS /api/v1/ws?token=<jwt>
```

**Auth:** JWT passed as `token` query parameter.

**Connection flow:**
1. Client connects with `?token=<jwt>`
2. Server validates token, loads user and all their servers
3. Server subscribes to Redis pub/sub channels for each server
4. Server sends initial `status_change` for each server
5. Server forwards real-time messages from Redis

**Message types received by client:**

```json
// Metric update
{
  "type": "metric",
  "server_id": "550e8400-e29b-41d4-a716-446655440000",
  "data": { /* MetricResponse payload */ }
}

// Status change
{
  "type": "status_change",
  "server_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "online"
}
```

**Close codes:**
- `4001` — Missing or invalid token

---

## Health

### Health Check

```
GET /health
```

No authentication required.

**Response (200):**
```json
{
  "status": "ok",
  "db": "ok",
  "redis": "ok"
}
```

**Status codes:**
- `200` — All dependencies healthy
- `503` — One or more dependencies unhealthy (db or redis shows `"error"`)

### Prometheus Metrics

```
GET /metrics
```

No authentication required. Returns Prometheus-format metrics instrumented by `prometheus-fastapi-instrumentator`. Includes HTTP request counts, latencies, and application-level metrics.

**Status codes:**
- `200` — Metrics returned
