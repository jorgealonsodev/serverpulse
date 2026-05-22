"""Metrics integration tests — strict TDD (RED phase first)."""

from datetime import UTC, datetime, timedelta


async def _create_user_and_login(client, email: str = "metrics-test@example.com") -> str:
    """Register and login, return JWT access token."""
    async with client() as c:
        await c.post(
            "/api/v1/auth/register",
            json={"email": email, "password": "securepass123"},
        )
        login_resp = await c.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "securepass123"},
        )
        return login_resp.json()["access_token"]


async def _create_server_with_token(
    client, token: str, name: str = "test-server"
) -> dict:
    """Create a server using JWT auth, return server data including api_token."""
    async with client() as c:
        resp = await c.post(
            "/api/v1/servers/",
            json={"name": name},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        return resp.json()


def _valid_metric_payload(**overrides: dict) -> dict:
    """Return a valid metric ingest payload with optional overrides."""
    base = {
        "cpu_percent": 45.2,
        "ram_percent": 62.1,
        "ram_used_mb": 4096,
        "ram_total_mb": 8192,
        "disk_percent": 55.0,
        "disk_used_gb": 120.5,
        "disk_total_gb": 256.0,
        "net_rx_bytes": 1024000,
        "net_tx_bytes": 512000,
        "uptime_seconds": 86400,
        "load_avg_1": 1.5,
        "load_avg_5": 1.2,
        "load_avg_15": 0.9,
    }
    base.update(overrides)
    return base


async def test_ingest_valid_metrics_returns_202(client):
    """POST /api/v1/metrics/ingest — 202 with valid agent token and payload."""
    async with client() as c:
        jwt_token = await _create_user_and_login(c)
        server_data = await _create_server_with_token(c, jwt_token)
        api_token = server_data["api_token"]

        resp = await c.post(
            "/api/v1/metrics/ingest",
            json=_valid_metric_payload(),
            headers={"X-Agent-Token": api_token},
        )
        assert resp.status_code == 202


async def test_ingest_invalid_token_returns_401(client):
    """POST /api/v1/metrics/ingest — 401 with invalid agent token."""
    async with client() as c:
        resp = await c.post(
            "/api/v1/metrics/ingest",
            json=_valid_metric_payload(),
            headers={"X-Agent-Token": "nonexistent-token"},
        )
        assert resp.status_code == 401


async def test_ingest_missing_required_field_returns_422(client):
    """POST /api/v1/metrics/ingest — 422 when required field is missing."""
    async with client() as c:
        jwt_token = await _create_user_and_login(c)
        server_data = await _create_server_with_token(c, jwt_token)
        api_token = server_data["api_token"]

        payload = _valid_metric_payload()
        del payload["cpu_percent"]

        resp = await c.post(
            "/api/v1/metrics/ingest",
            json=payload,
            headers={"X-Agent-Token": api_token},
        )
        assert resp.status_code == 422


async def test_ingest_updates_last_seen_at(client):
    """POST /api/v1/metrics/ingest — server.last_seen_at is updated after ingest."""
    async with client() as c:
        jwt_token = await _create_user_and_login(c)
        server_data = await _create_server_with_token(c, jwt_token)
        api_token = server_data["api_token"]
        server_id = server_data["id"]

        # Verify last_seen_at is initially null
        detail_resp = await c.get(
            f"/api/v1/servers/{server_id}",
            headers={"Authorization": f"Bearer {jwt_token}"},
        )
        assert detail_resp.json()["last_seen_at"] is None

        # Ingest a metric
        resp = await c.post(
            "/api/v1/metrics/ingest",
            json=_valid_metric_payload(),
            headers={"X-Agent-Token": api_token},
        )
        assert resp.status_code == 202

        # Check last_seen_at is now set
        detail_resp = await c.get(
            f"/api/v1/servers/{server_id}",
            headers={"Authorization": f"Bearer {jwt_token}"},
        )
        assert detail_resp.json()["last_seen_at"] is not None


async def test_query_metrics_returns_data(client):
    """GET /api/v1/servers/{id}/metrics — 200 with metric data after ingest."""
    async with client() as c:
        jwt_token = await _create_user_and_login(c)
        server_data = await _create_server_with_token(c, jwt_token)
        api_token = server_data["api_token"]
        server_id = server_data["id"]

        # Ingest a metric
        await c.post(
            "/api/v1/metrics/ingest",
            json=_valid_metric_payload(),
            headers={"X-Agent-Token": api_token},
        )

        # Query metrics
        now = datetime.now(UTC)
        from_date = now - timedelta(hours=1)
        resp = await c.get(
            f"/api/v1/servers/{server_id}/metrics",
            headers={"Authorization": f"Bearer {jwt_token}"},
            params={"from": from_date.isoformat(), "to": now.isoformat()},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert data[0]["cpu_percent"] == 45.2


async def test_query_range_exceeds_24h_returns_400(client):
    """GET /api/v1/servers/{id}/metrics — 400 when range > 24 hours."""
    async with client() as c:
        jwt_token = await _create_user_and_login(c)
        server_data = await _create_server_with_token(c, jwt_token)
        server_id = server_data["id"]

        now = datetime.now(UTC)
        from_date = now - timedelta(hours=25)
        resp = await c.get(
            f"/api/v1/servers/{server_id}/metrics",
            headers={"Authorization": f"Bearer {jwt_token}"},
            params={"from": from_date.isoformat(), "to": now.isoformat()},
        )
        assert resp.status_code == 400


async def test_query_user_isolation_returns_404(client):
    """GET /api/v1/servers/{id}/metrics — 404 when querying another user's server."""
    async with client() as c:
        # User A creates a server
        jwt_token_a = await _create_user_and_login(c, email="user-a@example.com")
        server_data = await _create_server_with_token(c, jwt_token_a, name="user-a-server")
        server_id = server_data["id"]

        # User B tries to query User A's server
        await c.post(
            "/api/v1/auth/register",
            json={"email": "user-b@example.com", "password": "securepass123"},
        )
        login_b = await c.post(
            "/api/v1/auth/login",
            json={"email": "user-b@example.com", "password": "securepass123"},
        )
        jwt_token_b = login_b.json()["access_token"]

        now = datetime.now(UTC)
        from_date = now - timedelta(hours=1)
        resp = await c.get(
            f"/api/v1/servers/{server_id}/metrics",
            headers={"Authorization": f"Bearer {jwt_token_b}"},
            params={"from": from_date.isoformat(), "to": now.isoformat()},
        )
        assert resp.status_code == 404


async def test_query_nonexistent_server_returns_404(client):
    """GET /api/v1/servers/{id}/metrics — 404 for nonexistent server."""
    async with client() as c:
        jwt_token = await _create_user_and_login(c)
        nonexistent_id = "00000000-0000-0000-0000-000000000000"

        now = datetime.now(UTC)
        from_date = now - timedelta(hours=1)
        resp = await c.get(
            f"/api/v1/servers/{nonexistent_id}/metrics",
            headers={"Authorization": f"Bearer {jwt_token}"},
            params={"from": from_date.isoformat(), "to": now.isoformat()},
        )
        assert resp.status_code == 404


async def test_ingest_publishes_to_redis(client):
    """POST /api/v1/metrics/ingest — publishes to Redis channel on success."""
    from unittest.mock import AsyncMock, patch

    from app import redis_client

    async with client() as c:
        jwt_token = await _create_user_and_login(c)
        server_data = await _create_server_with_token(c, jwt_token)
        api_token = server_data["api_token"]
        server_id = server_data["id"]

        with patch.object(redis_client.redis_client, "publish", new_callable=AsyncMock) as mock_publish:
            resp = await c.post(
                "/api/v1/metrics/ingest",
                json=_valid_metric_payload(),
                headers={"X-Agent-Token": api_token},
            )
            assert resp.status_code == 202
            mock_publish.assert_called_once()
            call_args = mock_publish.call_args
            assert f"metrics:{server_id}" in str(call_args)
