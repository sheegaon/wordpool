"""Tests for backend rate limiting utilities."""
import atexit
import os

import pytest
from fastapi import Depends, FastAPI, Header
from httpx import ASGITransport, AsyncClient

_ORIGINAL_DATABASE_URL = os.environ.get("DATABASE_URL")
_TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_rate_limiting_tests.db"
os.environ["DATABASE_URL"] = _TEST_DATABASE_URL


def _restore_database_url() -> None:
    if _ORIGINAL_DATABASE_URL is None:
        os.environ.pop("DATABASE_URL", None)
    else:
        os.environ["DATABASE_URL"] = _ORIGINAL_DATABASE_URL


atexit.register(_restore_database_url)

from backend.dependencies import (  # noqa: E402
    GENERAL_RATE_LIMIT,
    VOTE_RATE_LIMIT,
    _enforce_rate_limit,
    enforce_vote_rate_limit,
    rate_limiter,
)


test_app = FastAPI()


async def general_limit_dependency(x_api_key: str = Header(..., alias="X-API-Key")) -> None:
    """Apply the same general rate limit used by authenticated endpoints."""

    await _enforce_rate_limit("general", x_api_key, GENERAL_RATE_LIMIT)


@test_app.get("/general", dependencies=[Depends(general_limit_dependency)])
async def general_endpoint():
    return {"status": "ok"}


@test_app.post("/vote", dependencies=[Depends(enforce_vote_rate_limit)])
async def vote_endpoint():
    return {"status": "ok"}


@pytest.fixture(autouse=True)
def reset_rate_limiters():
    """Ensure each test starts with a clean rate limiter state."""

    rate_limiter.reset()
    yield
    rate_limiter.reset()


@pytest.mark.asyncio
async def test_general_rate_limit_per_api_key():
    """General limit allows 100 requests per minute per API key."""

    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
        headers = {"X-API-Key": "key-123"}

        for _ in range(GENERAL_RATE_LIMIT):
            response = await client.get("/general", headers=headers)
            assert response.status_code == 200

        limited_response = await client.get("/general", headers=headers)
        assert limited_response.status_code == 429
        assert limited_response.json()["detail"] == "Rate limit exceeded. Try again later."


@pytest.mark.asyncio
async def test_vote_rate_limit_is_stricter_than_general():
    """Vote submissions enforce the tighter 20 requests per minute limit."""

    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
        headers = {"X-API-Key": "key-456"}

        for _ in range(VOTE_RATE_LIMIT):
            response = await client.post("/vote", headers=headers)
            assert response.status_code == 200

        limited_response = await client.post("/vote", headers=headers)
        assert limited_response.status_code == 429
        assert limited_response.json()["detail"] == "Rate limit exceeded. Try again later."
