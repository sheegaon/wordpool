"""Scoring and payout calculation service."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
import logging

from backend.models.wordset import WordSet
from backend.models.vote import Vote
from backend.models.round import Round

logger = logging.getLogger(__name__)


class ScoringService:
    """Service for calculating scores and payouts."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def calculate_payouts(self, wordset: WordSet) -> dict:
        """
        Calculate points and payouts for wordset.

        Returns:
            {
                "original": {"points": int, "payout": int, "player_id": UUID},
                "copy1": {"points": int, "payout": int, "player_id": UUID},
                "copy2": {"points": int, "payout": int, "player_id": UUID},
            }
        """
        # Get all votes
        result = await self.db.execute(
            select(Vote).where(Vote.wordset_id == wordset.wordset_id)
        )
        votes = list(result.scalars().all())

        # Count votes per word
        original_votes = sum(1 for v in votes if v.voted_word == wordset.original_word)
        copy1_votes = sum(1 for v in votes if v.voted_word == wordset.copy_word_1)
        copy2_votes = sum(1 for v in votes if v.voted_word == wordset.copy_word_2)

        # Calculate points (1 for original, 2 for copies)
        original_points = original_votes * 1
        copy1_points = copy1_votes * 2
        copy2_points = copy2_votes * 2
        total_points = original_points + copy1_points + copy2_points

        # Calculate prize pool (total_pool - correct votes * 5)
        correct_votes = original_votes
        prize_pool = wordset.total_pool - (correct_votes * 5)

        # Distribute proportionally (rounded down)
        if total_points == 0:
            # No votes, split evenly
            original_payout = prize_pool // 3
            copy1_payout = prize_pool // 3
            copy2_payout = prize_pool // 3
        else:
            original_payout = (original_points * prize_pool) // total_points
            copy1_payout = (copy1_points * prize_pool) // total_points
            copy2_payout = (copy2_points * prize_pool) // total_points

        # Get player IDs
        prompt_round = await self.db.get(Round, wordset.prompt_round_id)
        copy1_round = await self.db.get(Round, wordset.copy_round_1_id)
        copy2_round = await self.db.get(Round, wordset.copy_round_2_id)

        logger.info(
            f"Calculated payouts for wordset {wordset.wordset_id}: "
            f"original={original_payout}, copy1={copy1_payout}, copy2={copy2_payout}"
        )

        return {
            "original": {
                "points": original_points,
                "payout": original_payout,
                "player_id": prompt_round.player_id,
                "word": wordset.original_word,
            },
            "copy1": {
                "points": copy1_points,
                "payout": copy1_payout,
                "player_id": copy1_round.player_id,
                "word": wordset.copy_word_1,
            },
            "copy2": {
                "points": copy2_points,
                "payout": copy2_payout,
                "player_id": copy2_round.player_id,
                "word": wordset.copy_word_2,
            },
        }
