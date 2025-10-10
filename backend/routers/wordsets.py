"""Wordsets API router."""
from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import get_db
from backend.dependencies import get_current_player
from backend.models.player import Player
from backend.models.round import Round
from backend.models.wordset import WordSet
from backend.schemas.wordset import (
    VoteRequest,
    VoteResponse,
    WordSetResults,
)
from backend.services.transaction_service import TransactionService
from backend.services.vote_service import VoteService
from backend.utils.exceptions import (
    RoundExpiredError,
    AlreadyVotedError,
)
from datetime import datetime, UTC
from uuid import UUID
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


def ensure_utc(dt: datetime) -> datetime:
    """Ensure datetime has UTC timezone for proper JSON serialization."""
    if dt and dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


@router.post("/{wordset_id}/vote", response_model=VoteResponse)
async def submit_vote(
    wordset_id: UUID = Path(...),
    request: VoteRequest = ...,
    player: Player = Depends(get_current_player),
    db: AsyncSession = Depends(get_db),
):
    """Submit vote for a wordset."""
    transaction_service = TransactionService(db)
    vote_service = VoteService(db)

    # Get player's active vote round
    if not player.active_round_id:
        raise HTTPException(status_code=400, detail="No active vote round")

    round = await db.get(Round, player.active_round_id)
    if not round or round.round_type != "vote":
        raise HTTPException(status_code=400, detail="Not in a vote round")

    if round.wordset_id != wordset_id:
        raise HTTPException(status_code=400, detail="Wordset does not match active round")

    # Get wordset
    wordset = await db.get(WordSet, wordset_id)
    if not wordset:
        raise HTTPException(status_code=404, detail="Wordset not found")

    try:
        vote = await vote_service.submit_vote(
            round, wordset, request.word, player, transaction_service
        )

        return VoteResponse(
            correct=vote.correct,
            payout=vote.payout,
            original_word=wordset.original_word,
            your_choice=vote.voted_word,
        )
    except RoundExpiredError as e:
        raise HTTPException(status_code=400, detail={"error": "expired", "message": str(e)})
    except AlreadyVotedError as e:
        raise HTTPException(status_code=400, detail={"error": "already_voted", "message": str(e)})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error submitting vote: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{wordset_id}/results", response_model=WordSetResults)
async def get_wordset_results(
    wordset_id: UUID = Path(...),
    player: Player = Depends(get_current_player),
    db: AsyncSession = Depends(get_db),
):
    """Get voting results for a wordset (triggers prize collection on first view)."""
    transaction_service = TransactionService(db)
    vote_service = VoteService(db)

    try:
        results = await vote_service.get_wordset_results(
            wordset_id, player.player_id, transaction_service
        )

        # Ensure finalized_at has UTC timezone
        if 'finalized_at' in results and results['finalized_at']:
            results['finalized_at'] = ensure_utc(results['finalized_at'])

        return WordSetResults(**results)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting wordset results: {e}")
        raise HTTPException(status_code=500, detail=str(e))
