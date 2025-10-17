"""Tests for player API endpoints."""
import pytest
import pytest
from uuid import uuid4

from httpx import AsyncClient, ASGITransport

from backend.main import app
from backend.models.player import Player
from backend.services.player_service import PlayerService


@pytest.mark.asyncio
async def test_create_player():
    """Test POST /player creates a new player."""
    payload = {
        "username": f"testuser_{uuid4().hex[:6]}",
        "email": f"test_{uuid4().hex[:6]}@example.com",
        "password": "SecurePass123!",
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/player", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert "player_id" in data
    assert "access_token" in data
    assert "refresh_token" in data
    assert "legacy_api_key" in data
    assert "username" in data
    assert data["balance"] == 1000
    assert "message" in data
    assert data["username"]
    assert "Player created!" in data["message"]


@pytest.mark.asyncio
async def test_rotate_api_key():
    """Test POST /player/rotate-key generates new key."""
    # Create player via API (uses real database)
    payload = {
        "username": f"rotate_user_{uuid4().hex[:6]}",
        "email": f"rotate_{uuid4().hex[:6]}@example.com",
        "password": "RotatePass123!",
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        create_response = await client.post("/player", json=payload)
        assert create_response.status_code == 201
        create_data = create_response.json()
        old_key = create_data["legacy_api_key"]
        username = create_data["username"]

        # Rotate key
        response = await client.post(
            "/player/rotate-key",
            headers={"X-API-Key": old_key}
        )

        assert response.status_code == 200
        data = response.json()
        assert "new_api_key" in data
        assert data["new_api_key"] != old_key

        # Verify old key no longer works
        response = await client.get(
            "/player/balance",
            headers={"X-API-Key": old_key}
        )
        assert response.status_code == 401

        # Verify username unchanged after rotation
        balance_response = await client.get(
            "/player/balance",
            headers={"X-API-Key": data["new_api_key"]}
        )
        assert balance_response.status_code == 200
        balance_data = balance_response.json()
        assert balance_data["username"] == username


@pytest.mark.asyncio
async def test_get_balance():
    """Test GET /player/balance returns player info."""
    # Create player via API (uses real database)
    payload = {
        "username": f"balance_user_{uuid4().hex[:6]}",
        "email": f"balance_{uuid4().hex[:6]}@example.com",
        "password": "BalancePass123!",
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        create_response = await client.post("/player", json=payload)
        assert create_response.status_code == 201
        create_data = create_response.json()

        response = await client.get(
            "/player/balance",
            headers={"Authorization": f"Bearer {create_data['access_token']}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["balance"] == 1000
        assert data["starting_balance"] == 1000
        assert data["username"] == create_data["username"]
        assert "daily_bonus_available" in data
        assert "outstanding_prompts" in data


@pytest.mark.asyncio
async def test_authentication_required():
    """Test endpoints require valid authentication."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # No header
        response = await client.get("/player/balance")
        assert response.status_code == 401

        # Invalid key
        response = await client.get(
            "/player/balance",
            headers={"X-API-Key": "invalid-key"}
        )
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_with_credentials():
    """Test logging in via credentials returns JWT tokens."""
    payload = {
        "username": f"login_user_{uuid4().hex[:6]}",
        "email": f"login_{uuid4().hex[:6]}@example.com",
        "password": "LoginPass123!",
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        create_response = await client.post("/player", json=payload)
        assert create_response.status_code == 201

        login_response = await client.post("/auth/login", json={
            "username": payload["username"],
            "password": payload["password"],
        })
        assert login_response.status_code == 200
        data = login_response.json()
        assert data["username"] == payload["username"]
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["player_id"] == create_response.json()["player_id"]


@pytest.mark.asyncio
async def test_login_with_unknown_username_returns_401():
    """Test logging in with unknown username returns 401."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/auth/login",
            json={"username": "Nonexistent User", "password": "WrongPass1!"},
        )
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_health_endpoint():
    """Test GET /health works without authentication."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "database" in data
