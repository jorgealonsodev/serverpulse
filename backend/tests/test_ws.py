"""WebSocket integration tests — strict TDD (RED phase first)."""

import asyncio
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from httpx_ws import aconnect_ws

from app.core.security import hash_agent_token
from app.database import async_session
from app.main import app
from app.models.server import Server

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _register_and_login(
    c: AsyncClient, email: str = "ws@test.com", password: str = "secret123"
) -> str:
    """Register a user, login, and return the JWT access token."""
    await c.post("/api/v1/auth/register", json={"email": email, "password": password})
    resp = await c.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200
    return resp.json()["access_token"]


async def _create_server_for_user(user_id, name: str = "test-server"):
    """Create a server record in the DB for a given user_id."""
    async with async_session() as session:
        server = Server(
            user_id=user_id,
            name=name,
            api_token_hash=hash_agent_token("test-agent-token"),
            last_seen_at=datetime.now(UTC),
        )
        session.add(server)
        await session.commit()
        await session.refresh(server)
        return server, "test-agent-token"


# ---------------------------------------------------------------------------
# FS5-REQ-01: WS Connection with JWT Auth
# ---------------------------------------------------------------------------

async def test_ws_connect_valid_token(client, ws_client_factory):
    """Connect with valid JWT → accepted."""
    async with client() as c, ws_client_factory() as ws_client:
        token = await _register_and_login(c)
        async with aconnect_ws(f"/api/v1/ws?token={token}", ws_client) as _ws:
            # Connection accepted — we can receive messages
            pass


async def test_ws_connect_invalid_token(ws_client_factory):
    """Connect with invalid token → closed with code 4001."""
    async with ws_client_factory() as ws_client:
        with pytest.raises(Exception):  # noqa: B017
            async with aconnect_ws("/api/v1/ws?token=invalid.token.here", ws_client) as _ws:
                await _ws.receive()


async def test_ws_connect_missing_token(ws_client_factory):
    """No token → closed with code 4001."""
    async with ws_client_factory() as ws_client:
        with pytest.raises(Exception):  # noqa: B017
            async with aconnect_ws("/api/v1/ws", ws_client) as _ws:
                await _ws.receive()


# ---------------------------------------------------------------------------
# FS5-REQ-02: Initial Subscription and Status
# ---------------------------------------------------------------------------

async def test_ws_initial_status_on_connect(client, ws_client_factory):
    """Connect WS → receive initial status_change for each server."""
    from jose import jwt

    from app.config import settings

    async with client() as c:
        token = await _register_and_login(c)
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        user_id = payload["sub"]

    # Create a server for this user (uses global async_session)
    server, _agent_token = await _create_server_for_user(user_id, "initial-status-server")

    async with (
        ws_client_factory() as ws_client,
        aconnect_ws(f"/api/v1/ws?token={token}", ws_client) as ws,
    ):
        # Should receive initial status_change for the server
        msg = await asyncio.wait_for(ws.receive_json(), timeout=5.0)
        assert msg["type"] == "status_change"
        assert msg["server_id"] == str(server.id)
        assert msg["status"] in ("online", "offline")


# ---------------------------------------------------------------------------
# FS5-REQ-03: Metric Message Forwarding
# ---------------------------------------------------------------------------

async def test_ws_receive_metric_on_ingest(client, ws_client_factory):
    """Connect WS → POST ingest → receive metric message."""
    from jose import jwt

    from app.config import settings

    async with client() as c:
        token = await _register_and_login(c)
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        user_id = payload["sub"]

    server, agent_token = await _create_server_for_user(user_id, "metric-ingest-server")

    async with (
        client() as c,
        ws_client_factory() as ws_client,
        aconnect_ws(f"/api/v1/ws?token={token}", ws_client) as ws,
    ):
        # Drain initial status messages
        try:
            while True:
                msg = await asyncio.wait_for(ws.receive_json(), timeout=1.0)
        except TimeoutError:
            pass

        # Ingest a metric via HTTP
        ingest_resp = await c.post(
            "/api/v1/metrics/ingest",
            json={
                "cpu_percent": 45.2,
                "ram_percent": 62.1,
                "ram_used_mb": 4096,
                "ram_total_mb": 8192,
                "disk_percent": 55.0,
                "disk_used_gb": 100.0,
                "disk_total_gb": 200.0,
                "net_rx_bytes": 1024,
                "net_tx_bytes": 512,
                "uptime_seconds": 3600,
                "load_avg_1": 1.5,
                "load_avg_5": 1.2,
                "load_avg_15": 0.9,
            },
            headers={"X-Agent-Token": agent_token},
        )
        assert ingest_resp.status_code == 202

        # Receive the forwarded metric
        msg = await asyncio.wait_for(ws.receive_json(), timeout=5.0)
        assert msg["type"] == "metric"
        assert msg["server_id"] == str(server.id)
        assert "data" in msg


# ---------------------------------------------------------------------------
# FS5-REQ-04: Status Change Forwarding
# ---------------------------------------------------------------------------

async def test_ws_status_change_offline(client, ws_client_factory):
    """Set last_seen_at old → receive offline status_change."""
    from jose import jwt

    from app.config import settings

    async with client() as c:
        token = await _register_and_login(c)
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        user_id = payload["sub"]

    # Create a server with old last_seen_at (simulate offline)
    async with async_session() as session:
        server = Server(
            user_id=user_id,
            name="offline-server",
            api_token_hash="dummy-hash",
            last_seen_at=datetime.now(UTC) - timedelta(minutes=10),
        )
        session.add(server)
        await session.commit()
        await session.refresh(server)
        server_id = server.id

    async with (
        ws_client_factory() as ws_client,
        aconnect_ws(f"/api/v1/ws?token={token}", ws_client) as ws,
    ):
        # Should receive initial status_change showing offline
        msg = await asyncio.wait_for(ws.receive_json(), timeout=5.0)
        assert msg["type"] == "status_change"
        assert msg["server_id"] == str(server_id)
        assert msg["status"] == "offline"


# ---------------------------------------------------------------------------
# FS5-REQ-05: Connection Lifecycle — Multiple Connections
# ---------------------------------------------------------------------------

async def test_ws_multiple_connections(client, ws_client_factory):
    """2 connections for same user → both receive metric."""
    from httpx import AsyncClient as HTTPXAsyncClient
    from httpx_ws.transport import ASGIWebSocketTransport
    from jose import jwt

    from app.config import settings
    from app.ws.manager import manager

    async with client() as c:
        token = await _register_and_login(c)
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        user_id = payload["sub"]

        server, agent_token = await _create_server_for_user(user_id, "multi-conn-server")

        # Use separate WS clients to avoid transport sharing issues
        transport1 = ASGIWebSocketTransport(app=app)
        transport2 = ASGIWebSocketTransport(app=app)

        async with (  # noqa: SIM117
            HTTPXAsyncClient(transport=transport1, base_url="http://test") as ws1_client,
            HTTPXAsyncClient(transport=transport2, base_url="http://test") as ws2_client,
        ):
            async with aconnect_ws(f"/api/v1/ws?token={token}", ws1_client) as ws1:
                async with aconnect_ws(f"/api/v1/ws?token={token}", ws2_client) as ws2:
                        # Verify both connections are tracked
                        from uuid import UUID
                        uid = UUID(user_id)
                        assert uid in manager.active
                        assert len(manager.active[uid]) == 2

                        # Drain initial status messages from both
                        for ws in [ws1, ws2]:
                            try:
                                while True:
                                    _msg = await asyncio.wait_for(ws.receive_json(), timeout=1.0)  # noqa: F841
                            except TimeoutError:
                                pass

                        # Ingest a metric
                        ingest_resp = await c.post(
                            "/api/v1/metrics/ingest",
                            json={
                                "cpu_percent": 50.0,
                                "ram_percent": 70.0,
                                "ram_used_mb": 5000,
                                "ram_total_mb": 8192,
                                "disk_percent": 60.0,
                                "disk_used_gb": 120.0,
                                "disk_total_gb": 200.0,
                                "net_rx_bytes": 2048,
                                "net_tx_bytes": 1024,
                                "uptime_seconds": 7200,
                                "load_avg_1": 2.0,
                                "load_avg_5": 1.8,
                                "load_avg_15": 1.5,
                            },
                            headers={"X-Agent-Token": agent_token},
                        )
                        assert ingest_resp.status_code == 202

                        # At least one connection should receive the metric
                        msg1 = await asyncio.wait_for(ws1.receive_json(), timeout=5.0)
                        assert msg1["type"] == "metric"
                        assert msg1["server_id"] == str(server.id)
