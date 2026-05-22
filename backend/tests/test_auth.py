"""Auth integration tests — strict TDD (RED phase first)."""

import pytest


@pytest.fixture
def register_payload():
    return {"email": "test@example.com", "password": "secret123"}


async def test_register_success(client, register_payload: dict):
    """POST /api/v1/auth/register — 201 with id and email."""
    async with client() as c:
        resp = await c.post("/api/v1/auth/register", json=register_payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == register_payload["email"]
        assert "id" in data


async def test_register_duplicate_email(client, register_payload: dict):
    """POST /api/v1/auth/register — 409 on duplicate email."""
    async with client() as c:
        await c.post("/api/v1/auth/register", json=register_payload)
        resp = await c.post("/api/v1/auth/register", json=register_payload)
        assert resp.status_code == 409


async def test_register_short_password(client):
    """POST /api/v1/auth/register — 422 when password < 8 chars."""
    async with client() as c:
        resp = await c.post(
            "/api/v1/auth/register",
            json={"email": "short@example.com", "password": "short"},
        )
        assert resp.status_code == 422


async def test_login_success(client, register_payload: dict):
    """POST /api/v1/auth/login — 200 with access_token."""
    async with client() as c:
        await c.post("/api/v1/auth/register", json=register_payload)
        resp = await c.post(
            "/api/v1/auth/login",
            json={"email": register_payload["email"], "password": register_payload["password"]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"


async def test_login_wrong_password(client, register_payload: dict):
    """POST /api/v1/auth/login — 401 on wrong password."""
    async with client() as c:
        await c.post("/api/v1/auth/register", json=register_payload)
        resp = await c.post(
            "/api/v1/auth/login",
            json={"email": register_payload["email"], "password": "wrongpassword"},
        )
        assert resp.status_code == 401


async def test_me_valid_token(client, register_payload: dict):
    """GET /api/v1/auth/me — 200 with valid Bearer token."""
    async with client() as c:
        await c.post("/api/v1/auth/register", json=register_payload)
        login_resp = await c.post(
            "/api/v1/auth/login",
            json={"email": register_payload["email"], "password": register_payload["password"]},
        )
        token = login_resp.json()["access_token"]
        resp = await c.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == register_payload["email"]
        assert "id" in data


async def test_me_invalid_token(client):
    """GET /api/v1/auth/me — 401 with invalid Bearer token."""
    async with client() as c:
        resp = await c.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid-token-here"},
        )
        assert resp.status_code == 401


async def test_me_missing_token(client):
    """GET /api/v1/auth/me — 401 without Authorization header."""
    async with client() as c:
        resp = await c.get("/api/v1/auth/me")
        assert resp.status_code == 401
