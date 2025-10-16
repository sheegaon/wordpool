"""FastAPI dependencies."""
from fastapi import Header, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import get_db
from backend.services.player_service import PlayerService
from backend.models.player import Player
from backend.config import get_settings
from backend.utils.rate_limiter import RateLimiter
import logging

logger = logging.getLogger(__name__)


settings = get_settings()
rate_limiter = RateLimiter(settings.redis_url or None)

GENERAL_RATE_LIMIT = 100
VOTE_RATE_LIMIT = 20
RATE_LIMIT_WINDOW_SECONDS = 60
RATE_LIMIT_ERROR_MESSAGE = "Rate limit exceeded. Try again later."


def _enforce_rate_limit(scope: str, api_key: str, limit: int) -> None:
    """Apply a rate limit for the provided scope and API key."""

    if not api_key:
        return

    identifier = f"{scope}:{api_key}"
    allowed, retry_after = rate_limiter.check(identifier, limit, RATE_LIMIT_WINDOW_SECONDS)

    if allowed:
        return

    headers = {}
    if retry_after is not None:
        headers["Retry-After"] = str(retry_after)

    logger.warning("Rate limit exceeded for scope=%s", scope)
    raise HTTPException(status_code=429, detail=RATE_LIMIT_ERROR_MESSAGE, headers=headers or None)


async def get_current_player(
    x_api_key: str = Header(..., alias="X-API-Key"),
    db: AsyncSession = Depends(get_db),
) -> Player:
    """
    Get current authenticated player from API key header.

    Raises:
        HTTPException: 401 if API key invalid
    """
    _enforce_rate_limit("general", x_api_key, GENERAL_RATE_LIMIT)

    player_service = PlayerService(db)
    player = await player_service.get_player_by_api_key(x_api_key)

    if not player:
        logger.warning(f"Invalid API key attempt: {x_api_key[:8]}...")
        raise HTTPException(status_code=401, detail="Invalid API key")

    logger.debug(f"Authenticated player: {player.player_id}")
    return player


async def enforce_vote_rate_limit(
    x_api_key: str = Header(..., alias="X-API-Key"),
) -> None:
    """Enforce tighter limits on vote submissions."""

    _enforce_rate_limit("vote_submit", x_api_key, VOTE_RATE_LIMIT)
