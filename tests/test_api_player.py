"""Tests for player API endpoints."""
import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app
from backend.models.player import Player
from backend.services.player_service import PlayerService


@pytest.mark.asyncio
async def test_create_player(test_app):
    """Test POST /player creates a new player."""
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
        response = await client.post("/player")

    assert response.status_code == 201
    data = response.json()
    assert "player_id" in data
    assert "api_key" in data
    assert "username" in data
    assert data["balance"] == 1000
    assert "message" in data
    assert data["username"]
    assert data["username"] in data["message"]


@pytest.mark.asyncio
async def test_rotate_api_key(test_app):
    """Test POST /player/rotate-key generates new key."""
    # Create player via API (uses real database)
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
        create_response = await client.post("/player")
        assert create_response.status_code == 201
        create_data = create_response.json()
        old_key = create_data["api_key"]
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
async def test_get_balance(test_app):
    """Test GET /player/balance returns player info."""
    # Create player via API (uses real database)
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
        create_response = await client.post("/player")
        assert create_response.status_code == 201
        create_data = create_response.json()

        response = await client.get(
            "/player/balance",
            headers={"X-API-Key": create_data["api_key"]}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["balance"] == 1000
        assert data["starting_balance"] == 1000
        assert data["username"] == create_data["username"]
        assert "daily_bonus_available" in data
        assert "outstanding_prompts" in data


@pytest.mark.asyncio
async def test_authentication_required(test_app):
    """Test endpoints require valid API key."""
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
        # No header
        response = await client.get("/player/balance")
        assert response.status_code == 422  # Missing header

        # Invalid key
        response = await client.get(
            "/player/balance",
            headers={"X-API-Key": "invalid-key"}
        )
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_with_username(test_app):
    """Test logging in via username returns API key."""
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
        create_response = await client.post("/player")
        assert create_response.status_code == 201
        created = create_response.json()

        login_response = await client.post("/player/login", json={"username": created["username"]})
        assert login_response.status_code == 200
        data = login_response.json()
        assert data["api_key"] == created["api_key"]
        assert data["username"] == created["username"]
        assert data["player_id"] == created["player_id"]


@pytest.mark.asyncio
async def test_login_with_unknown_username_returns_404(test_app):
    """Test logging in with unknown username returns 404."""
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
        response = await client.post("/player/login", json={"username": "Nonexistent User"})
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_health_endpoint():
    """Test GET /health works without authentication."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "database" in data
