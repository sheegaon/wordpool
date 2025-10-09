"""FastAPI dependencies."""
from fastapi import Header, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import get_db
from backend.services.player_service import PlayerService
from backend.models.player import Player
import logging

logger = logging.getLogger(__name__)


async def get_current_player(
    x_api_key: str = Header(..., alias="X-API-Key"),
    db: AsyncSession = Depends(get_db),
) -> Player:
    """
    Get current authenticated player from API key header.

    Raises:
        HTTPException: 401 if API key invalid
    """
    player_service = PlayerService(db)
    player = await player_service.get_player_by_api_key(x_api_key)

    if not player:
        logger.warning(f"Invalid API key attempt: {x_api_key[:8]}...")
        raise HTTPException(status_code=401, detail="Invalid API key")

    logger.debug(f"Authenticated player: {player.player_id}")
    return player
