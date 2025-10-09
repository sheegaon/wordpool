"""Round service for managing prompt, copy, and vote rounds."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from backend.models.player import Player
from backend.models.prompt import Prompt
from backend.models.round import Round
from backend.models.wordset import WordSet
from backend.models.player_abandoned_prompt import PlayerAbandonedPrompt
from backend.services.transaction_service import TransactionService
from backend.services.queue_service import QueueService
from backend.services.word_validator import get_word_validator
from backend.config import get_settings
from datetime import datetime, UTC, timedelta
from backend.utils.exceptions import (
    InvalidWordError,
    DuplicateWordError,
    RoundNotFoundError,
    RoundExpiredError,
)
from datetime import datetime, timedelta
from uuid import UUID
import uuid
import random
import logging

logger = logging.getLogger(__name__)
settings = get_settings()


class RoundService:
    """Service for managing game rounds."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.word_validator = get_word_validator()

    async def start_prompt_round(
        self,
        player: Player,
        transaction_service: TransactionService,
    ) -> Round:
        """
        Start a prompt round.

        - Deduct $100 immediately
        - Randomly assign prompt
        - Create round with 60s timer
        """
        # Get random enabled prompt
        result = await self.db.execute(
            select(Prompt)
            .where(Prompt.enabled == True)
            .order_by(func.random())
            .limit(1)
        )
        prompt = result.scalar_one_or_none()

        if not prompt:
            raise ValueError("No prompts available in library")

        # Create transaction (deduct full amount immediately)
        await transaction_service.create_transaction(
            player.player_id,
            -settings.prompt_cost,
            "prompt_entry",
        )

        # Create round
        round = Round(
            round_id=uuid.uuid4(),
            player_id=player.player_id,
            round_type="prompt",
            status="active",
            cost=settings.prompt_cost,
            expires_at=datetime.now(UTC) + timedelta(seconds=settings.prompt_round_seconds),
            # Prompt-specific fields
            prompt_id=prompt.prompt_id,
            prompt_text=prompt.text,
        )

        # Update prompt usage
        prompt.usage_count += 1

        # Set player's active round
        player.active_round_id = round.round_id

        self.db.add(round)
        await self.db.commit()
        await self.db.refresh(round)

        logger.info(f"Started prompt round {round.round_id} for player {player.player_id}")
        return round

    async def submit_prompt_word(
        self,
        round_id: UUID,
        word: str,
        player: Player,
        transaction_service: TransactionService,
    ) -> Round:
        """Submit word for prompt round."""
        # Get round
        round = await self.db.get(Round, round_id)
        if not round or round.player_id != player.player_id:
            raise RoundNotFoundError("Round not found")

        if round.status != "active":
            raise ValueError("Round is not active")

        # Check grace period
        # Make grace_cutoff timezone-aware if expires_at is naive (SQLite stores naive)
        expires_at_aware = round.expires_at.replace(tzinfo=UTC) if round.expires_at.tzinfo is None else round.expires_at
        grace_cutoff = expires_at_aware + timedelta(seconds=settings.grace_period_seconds)
        if datetime.now(UTC) > grace_cutoff:
            raise RoundExpiredError("Round expired past grace period")

        # Validate word
        is_valid, error = self.word_validator.validate(word)
        if not is_valid:
            raise InvalidWordError(error)

        # Update round
        round.submitted_word = word.upper()
        round.status = "submitted"

        # Clear player's active round
        player.active_round_id = None

        # Add to queue
        QueueService.add_prompt_to_queue(round.round_id)

        await self.db.commit()
        await self.db.refresh(round)

        logger.info(f"Submitted word for prompt round {round_id}: {word}")
        return round

    async def start_copy_round(
        self,
        player: Player,
        transaction_service: TransactionService,
    ) -> Round:
        """
        Start a copy round.

        - Get next prompt from queue (FIFO)
        - Check discount (>10 prompts waiting)
        - Deduct cost immediately
        - Prevent same player from getting abandoned prompt (24h)
        """
        # Get next prompt from queue
        prompt_round_id = QueueService.get_next_prompt()
        if not prompt_round_id:
            raise ValueError("No prompts available")

        # Get prompt round
        prompt_round = await self.db.get(Round, prompt_round_id)
        if not prompt_round:
            raise ValueError("Prompt round not found")

        # CRITICAL: Check if player is trying to copy their own prompt
        if prompt_round.player_id == player.player_id:
            # Put back in queue and get another
            QueueService.add_prompt_to_queue(prompt_round_id)
            # For MVP, just fail - in production, retry with next prompt
            raise ValueError("Cannot copy your own prompt")

        # Check if player abandoned this prompt in last 24h
        cutoff = datetime.now(UTC) - timedelta(hours=24)
        result = await self.db.execute(
            select(PlayerAbandonedPrompt)
            .where(PlayerAbandonedPrompt.player_id == player.player_id)
            .where(PlayerAbandonedPrompt.prompt_round_id == prompt_round_id)
            .where(PlayerAbandonedPrompt.abandoned_at > cutoff)
        )
        if result.scalar_one_or_none():
            # Put back in queue and get another
            QueueService.add_prompt_to_queue(prompt_round_id)
            # For MVP, just fail - in production, retry with next prompt
            raise ValueError("Cannot retry abandoned prompt within 24h")

        # Get current copy cost (with discount if applicable)
        copy_cost = QueueService.get_copy_cost()
        is_discounted = copy_cost == settings.copy_cost_discount
        system_contribution = settings.copy_cost_normal - copy_cost if is_discounted else 0

        # Create transaction
        await transaction_service.create_transaction(
            player.player_id,
            -copy_cost,
            "copy_entry",
        )

        # Create round
        round = Round(
            round_id=uuid.uuid4(),
            player_id=player.player_id,
            round_type="copy",
            status="active",
            cost=copy_cost,
            expires_at=datetime.now(UTC) + timedelta(seconds=settings.copy_round_seconds),
            # Copy-specific fields
            prompt_round_id=prompt_round_id,
            original_word=prompt_round.submitted_word,
            system_contribution=system_contribution,
        )

        # Set player's active round
        player.active_round_id = round.round_id

        self.db.add(round)
        await self.db.commit()
        await self.db.refresh(round)

        logger.info(
            f"Started copy round {round.round_id} for player {player.player_id}, "
            f"cost=${copy_cost}, discount={is_discounted}"
        )
        return round

    async def submit_copy_word(
        self,
        round_id: UUID,
        word: str,
        player: Player,
        transaction_service: TransactionService,
    ) -> Round:
        """Submit word for copy round."""
        # Get round
        round = await self.db.get(Round, round_id)
        if not round or round.player_id != player.player_id:
            raise RoundNotFoundError("Round not found")

        if round.status != "active":
            raise ValueError("Round is not active")

        # Check grace period
        # Make grace_cutoff timezone-aware if expires_at is naive (SQLite stores naive)
        expires_at_aware = round.expires_at.replace(tzinfo=UTC) if round.expires_at.tzinfo is None else round.expires_at
        grace_cutoff = expires_at_aware + timedelta(seconds=settings.grace_period_seconds)
        if datetime.now(UTC) > grace_cutoff:
            raise RoundExpiredError("Round expired past grace period")

        # Validate word (including duplicate check)
        is_valid, error = self.word_validator.validate_copy(word, round.original_word)
        if not is_valid:
            if "same word" in error.lower():
                raise DuplicateWordError(error)
            raise InvalidWordError(error)

        # Update round
        round.copy_word = word.upper()
        round.status = "submitted"

        # Clear player's active round
        player.active_round_id = None

        await self.db.commit()

        # Check if we can create wordset
        await self._check_and_create_wordset(round.prompt_round_id)

        await self.db.refresh(round)

        logger.info(f"Submitted word for copy round {round_id}: {word}")
        return round

    async def _check_and_create_wordset(self, prompt_round_id: UUID):
        """Check if we have 2 copies for prompt, create wordset if so."""
        # Get all submitted copy rounds for this prompt
        result = await self.db.execute(
            select(Round)
            .where(Round.prompt_round_id == prompt_round_id)
            .where(Round.round_type == "copy")
            .where(Round.status == "submitted")
        )
        copy_rounds = list(result.scalars().all())

        if len(copy_rounds) >= 2:
            # Get prompt round
            prompt_round = await self.db.get(Round, prompt_round_id)

            # Use first 2 copies
            copy1 = copy_rounds[0]
            copy2 = copy_rounds[1]

            # Calculate total pool (300 + system contributions)
            total_pool = settings.wordset_prize_pool
            system_contribution = copy1.system_contribution + copy2.system_contribution

            # Create wordset
            wordset = WordSet(
                wordset_id=uuid.uuid4(),
                prompt_round_id=prompt_round_id,
                copy_round_1_id=copy1.round_id,
                copy_round_2_id=copy2.round_id,
                prompt_text=prompt_round.prompt_text,
                original_word=prompt_round.submitted_word,
                copy_word_1=copy1.copy_word,
                copy_word_2=copy2.copy_word,
                status="open",
                vote_count=0,
                total_pool=total_pool,
                system_contribution=system_contribution,
            )

            self.db.add(wordset)

            # Add to voting queue
            QueueService.add_wordset_to_queue(wordset.wordset_id)

            await self.db.commit()

            logger.info(f"Created wordset {wordset.wordset_id} from prompt {prompt_round_id}")

    async def handle_timeout(
        self,
        round_id: UUID,
        transaction_service: TransactionService,
    ):
        """
        Handle timeout for abandoned round.

        - Prompt: Refund $90, keep $10 penalty, remove from queue
        - Copy: Refund $90, keep $10 penalty, return prompt to queue, track cooldown
        """
        round = await self.db.get(Round, round_id)
        if not round or round.status != "active":
            return

        # Check if actually expired
        if datetime.now(UTC) <= round.expires_at:
            return

        # Mark as expired/abandoned
        if round.round_type == "prompt":
            round.status = "expired"
            refund_amount = settings.prompt_cost - (settings.prompt_cost // 10)  # Refund $90

            # Create refund transaction
            await transaction_service.create_transaction(
                round.player_id,
                refund_amount,
                "refund",
                round.round_id,
            )

            logger.info(f"Prompt round {round_id} expired, refunded ${refund_amount}")

        elif round.round_type == "copy":
            round.status = "abandoned"
            refund_amount = round.cost - (round.cost // 10)  # Refund 90% of cost

            # Create refund transaction
            await transaction_service.create_transaction(
                round.player_id,
                refund_amount,
                "refund",
                round.round_id,
            )

            # Return prompt to queue
            QueueService.add_prompt_to_queue(round.prompt_round_id)

            # Track abandonment for cooldown
            abandonment = PlayerAbandonedPrompt(
                id=uuid.uuid4(),
                player_id=round.player_id,
                prompt_round_id=round.prompt_round_id,
            )
            self.db.add(abandonment)

            logger.info(
                f"Copy round {round_id} abandoned, refunded ${refund_amount}, "
                f"returned prompt {round.prompt_round_id} to queue"
            )

        # Clear player's active round if still set
        player = await self.db.get(Player, round.player_id)
        if player and player.active_round_id == round_id:
            player.active_round_id = None

        await self.db.commit()
