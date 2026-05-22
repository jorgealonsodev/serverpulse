"""Servers CRUD integration tests — strict TDD (RED phase first)."""

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import generate_agent_token, hash_agent_token
from app.database import get_db
from app.models.server import Server

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def register_user(c: AsyncClient, email: str, password: str = "secret123") -> dict:
    """Register a user and return the response JSON."""
    resp = await c.post("/api/v1/auth/register", json={"email": email, "password": password})
    assert resp.status_code == 201
    return resp.json()


async def login_user(c: AsyncClient, email: str, password: str = "secret123") -> str:
    """Login and return the access_token."""
    resp = await c.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert resp.status_code == 200
    return resp.json()["access_token"]


async def auth_headers(c: AsyncClient, email: str, password: str = "secret123") -> dict:
    """Register + login and return Authorization headers."""
    await register_user(c, email, password)
    token = await login_user(c, email, password)
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Security utility tests (unit-level, no DB needed)
# ---------------------------------------------------------------------------


def test_generate_agent_token_returns_urlsafe_nonempty():
    """generate_agent_token returns a non-empty url-safe string."""
    token = generate_agent_token()
    assert isinstance(token, str)
    assert len(token) > 0
    # urlsafe base64 uses only [A-Za-z0-9_-]
    assert all(c.isalnum() or c in "-_" for c in token)


def test_generate_agent_token_unique():
    """Successive calls return different tokens."""
    t1 = generate_agent_token()
    t2 = generate_agent_token()
    assert t1 != t2


def test_hash_agent_token_deterministic():
    """Same token always produces the same hash."""
    token = "some-token"
    h1 = hash_agent_token(token)
    h2 = hash_agent_token(token)
    assert h1 == h2


def test_hash_agent_token_different_tokens():
    """Different tokens produce different hashes."""
    h1 = hash_agent_token("token-a")
    h2 = hash_agent_token("token-b")
    assert h1 != h2


# ---------------------------------------------------------------------------
# CRUD integration tests
# ---------------------------------------------------------------------------


async def test_create_server_success(client):
    """POST /api/v1/servers/ — 201 with id, name, api_token."""
    async with client() as c:
        headers = await auth_headers(c, "create@test.com")
        resp = await c.post("/api/v1/servers/", json={"name": "web-01"}, headers=headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "web-01"
        assert data["hostname"] is None
        assert "id" in data
        assert "api_token" in data
        assert len(data["api_token"]) > 0


async def test_create_server_with_hostname(client):
    """POST /api/v1/servers — 201 includes hostname."""
    async with client() as c:
        headers = await auth_headers(c, "hostname@test.com")
        resp = await c.post(
            "/api/v1/servers/",
            json={"name": "web-01", "hostname": "web01.example.com"},
            headers=headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["hostname"] == "web01.example.com"


async def test_create_server_empty_name(client):
    """POST /api/v1/servers — 422 when name is empty."""
    async with client() as c:
        headers = await auth_headers(c, "emptyname@test.com")
        resp = await c.post("/api/v1/servers/", json={"name": ""}, headers=headers)
        assert resp.status_code == 422


async def test_list_servers(client):
    """GET /api/v1/servers — 200 with list of own servers."""
    async with client() as c:
        headers = await auth_headers(c, "list@test.com")
        # Create two servers
        await c.post("/api/v1/servers/", json={"name": "srv-1"}, headers=headers)
        await c.post("/api/v1/servers/", json={"name": "srv-2"}, headers=headers)

        resp = await c.get("/api/v1/servers/", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        names = {s["name"] for s in data}
        assert names == {"srv-1", "srv-2"}


async def test_list_servers_user_isolation(client):
    """GET /api/v1/servers — user A cannot see user B's servers."""
    async with client() as c:
        # User A creates 2 servers
        headers_a = await auth_headers(c, "user-a@test.com")
        await c.post("/api/v1/servers/", json={"name": "a-srv-1"}, headers=headers_a)
        await c.post("/api/v1/servers/", json={"name": "a-srv-2"}, headers=headers_a)

        # User B creates 1 server
        headers_b = await auth_headers(c, "user-b@test.com")
        await c.post("/api/v1/servers/", json={"name": "b-srv-1"}, headers=headers_b)

        # User A should only see their own servers
        resp = await c.get("/api/v1/servers/", headers=headers_a)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        for s in data:
            assert s["name"].startswith("a-srv-")


async def test_get_server_detail(client):
    """GET /api/v1/servers/{id} — 200 with server detail, no api_token."""
    async with client() as c:
        headers = await auth_headers(c, "detail@test.com")
        create_resp = await c.post(
            "/api/v1/servers/",
            json={"name": "detail-srv"},
            headers=headers,
        )
        server_id = create_resp.json()["id"]

        resp = await c.get(f"/api/v1/servers/{server_id}", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "detail-srv"
        assert "api_token" not in data
        assert "id" in data
        assert "status" in data


async def test_get_server_other_user_404(client):
    """GET /api/v1/servers/{id} — 404 for other user's server."""
    async with client() as c:
        # User A creates a server
        headers_a = await auth_headers(c, "owner@test.com")
        create_resp = await c.post(
            "/api/v1/servers/",
            json={"name": "owner-srv"},
            headers=headers_a,
        )
        server_id = create_resp.json()["id"]

        # User B tries to access it
        headers_b = await auth_headers(c, "other@test.com")
        resp = await c.get(f"/api/v1/servers/{server_id}", headers=headers_b)
        assert resp.status_code == 404


async def test_delete_server(client):
    """DELETE /api/v1/servers/{id} — 204, server gone."""
    async with client() as c:
        headers = await auth_headers(c, "delete@test.com")
        create_resp = await c.post("/api/v1/servers/", json={"name": "del-srv"}, headers=headers)
        server_id = create_resp.json()["id"]

        resp = await c.delete(f"/api/v1/servers/{server_id}", headers=headers)
        assert resp.status_code == 204

        # Verify it's gone
        resp = await c.get(f"/api/v1/servers/{server_id}", headers=headers)
        assert resp.status_code == 404


async def test_delete_server_other_user_404(client):
    """DELETE /api/v1/servers/{id} — 404 for other user's server, server still exists."""
    async with client() as c:
        # User A creates a server
        headers_a = await auth_headers(c, "del-owner@test.com")
        create_resp = await c.post(
            "/api/v1/servers/",
            json={"name": "del-owner-srv"},
            headers=headers_a,
        )
        server_id = create_resp.json()["id"]

        # User B tries to delete it
        headers_b = await auth_headers(c, "del-other@test.com")
        resp = await c.delete(f"/api/v1/servers/{server_id}", headers=headers_b)
        assert resp.status_code == 404

        # User A can still access it
        resp = await c.get(f"/api/v1/servers/{server_id}", headers=headers_a)
        assert resp.status_code == 200


async def test_regenerate_token(client):
    """POST /api/v1/servers/{id}/regenerate-token — 200 with new api_token."""
    async with client() as c:
        headers = await auth_headers(c, "regen@test.com")
        create_resp = await c.post("/api/v1/servers/", json={"name": "regen-srv"}, headers=headers)
        server_id = create_resp.json()["id"]
        old_token = create_resp.json()["api_token"]

        resp = await c.post(
            f"/api/v1/servers/{server_id}/regenerate-token",
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "api_token" in data
        assert data["api_token"] != old_token


async def test_regenerate_token_invalidates_old(client, test_engine):
    """Regenerating a token replaces the hash in DB; old token no longer matches."""
    async with client() as c:
        headers = await auth_headers(c, "regen-old@test.com")
        create_resp = await c.post(
            "/api/v1/servers/",
            json={"name": "regen-old-srv"},
            headers=headers,
        )
        server_id = create_resp.json()["id"]
        old_token = create_resp.json()["api_token"]
        old_hash = hash_agent_token(old_token)

        # Regenerate
        await c.post(
            f"/api/v1/servers/{server_id}/regenerate-token",
            headers=headers,
        )

        # Get the server from DB and check hash changed
        async with test_engine.connect() as conn:
            from sqlalchemy import select as sa_select

            result = await conn.execute(sa_select(Server.api_token_hash).where(Server.id == server_id))
            new_hash = result.scalar_one()
            assert new_hash != old_hash


async def test_regenerate_token_other_user_404(client):
    """POST /api/v1/servers/{id}/regenerate-token — 404 for other user's server."""
    async with client() as c:
        # User A creates a server
        headers_a = await auth_headers(c, "regen-owner@test.com")
        create_resp = await c.post(
            "/api/v1/servers/",
            json={"name": "regen-owner-srv"},
            headers=headers_a,
        )
        server_id = create_resp.json()["id"]

        # User B tries to regenerate
        headers_b = await auth_headers(c, "regen-other@test.com")
        resp = await c.post(
            f"/api/v1/servers/{server_id}/regenerate-token",
            headers=headers_b,
        )
        assert resp.status_code == 404
