"""FastAPI dependencies."""
import logging

from fastapi import Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from backend.config import get_settings
from backend.database import get_db
from backend.models.player import Player
from backend.services.player_service import PlayerService
from backend.utils.rate_limiter import RateLimiter
from backend.services.auth_service import AuthService, AuthError

logger = logging.getLogger(__name__)


settings = get_settings()
rate_limiter = RateLimiter(settings.redis_url or None)

GENERAL_RATE_LIMIT = 100
VOTE_RATE_LIMIT = 20
RATE_LIMIT_WINDOW_SECONDS = 60
RATE_LIMIT_ERROR_MESSAGE = "Rate limit exceeded. Try again later."


def _mask_api_key(api_key: str) -> str:
    if not api_key:
        return "<missing>"
    if len(api_key) <= 8:
        return f"{api_key[:2]}…{api_key[-2:]}"
    return f"{api_key[:4]}…{api_key[-4:]}"


async def _enforce_rate_limit(scope: str, identifier: str | None, limit: int) -> None:
    """Apply a rate limit for the provided scope and identifier."""

    if not identifier:
        return

    key = f"{scope}:{identifier}"
    allowed, retry_after = await rate_limiter.check(
        key, limit, RATE_LIMIT_WINDOW_SECONDS
    )

    if allowed:
        return

    headers = {}
    if retry_after is not None:
        headers["Retry-After"] = str(retry_after)

    masked_key = _mask_api_key(api_key)
    logger.warning("Rate limit exceeded for scope=%s api_key=%s", scope, masked_key)
    raise HTTPException(status_code=429, detail=RATE_LIMIT_ERROR_MESSAGE, headers=headers or None)


async def get_current_player(
    authorization: str | None = Header(default=None, alias="Authorization"),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    db: AsyncSession = Depends(get_db),
) -> Player:
    """Resolve the current authenticated player via JWT or legacy API key."""

    player_service = PlayerService(db)

    if authorization:
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token:
            raise HTTPException(status_code=401, detail="invalid_authorization_header")
        auth_service = AuthService(db)
        try:
            payload = auth_service.decode_access_token(token)
            player_id_str = payload.get("sub")
            if not player_id_str:
                raise AuthError("invalid_token")
            player_id = UUID(str(player_id_str))
        except (ValueError, AuthError) as exc:
            detail = "token_expired" if isinstance(exc, AuthError) and str(exc) == "token_expired" else "invalid_token"
            raise HTTPException(status_code=401, detail=detail) from exc

        player = await player_service.get_player_by_id(player_id)
        if not player:
            raise HTTPException(status_code=401, detail="invalid_token")

        await _enforce_rate_limit("general", str(player.player_id), GENERAL_RATE_LIMIT)
        logger.debug("Authenticated player via JWT: %s", player.player_id)
        return player

    if not x_api_key:
        raise HTTPException(status_code=401, detail="missing_credentials")

    await _enforce_rate_limit("general", x_api_key, GENERAL_RATE_LIMIT)

    player = await player_service.get_player_by_api_key(x_api_key)

    if not player:
        logger.warning(f"Invalid API key attempt: {x_api_key[:8]}...")
        raise HTTPException(status_code=401, detail="Invalid API key")

    logger.debug(f"Authenticated player via API key: {player.player_id}")
    return player


async def enforce_vote_rate_limit(
    authorization: str | None = Header(default=None, alias="Authorization"),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Enforce tighter limits on vote submissions."""

    identifier = None
    if authorization:
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() == "bearer" and token:
            auth_service = AuthService(db)
            try:
                payload = auth_service.decode_access_token(token)
                sub = payload.get("sub")
                if sub:
                    identifier = str(sub)
            except AuthError:
                identifier = None
    if not identifier and x_api_key:
        identifier = x_api_key

    await _enforce_rate_limit("vote_submit", identifier, VOTE_RATE_LIMIT)
