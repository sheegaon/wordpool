"""Player service for account management."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from datetime import date
from uuid import UUID
import uuid
import logging

from backend.models.player import Player
from backend.models.daily_bonus import DailyBonus
from backend.models.phraseset import PhraseSet
from backend.models.round import Round
from backend.config import get_settings
from backend.utils.exceptions import DailyBonusNotAvailableError
from backend.services.username_service import (
    UsernameService,
    canonicalize_username,
    is_username_input_valid,
    normalize_username,
)

logger = logging.getLogger(__name__)
settings = get_settings()


class PlayerService:
    """Service for managing players."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_player(self) -> Player:
        """Create new player with starting balance, API key, and generated username."""
        username_service = UsernameService(self.db)

        for attempt in range(6):
            username, username_canonical = await username_service.generate_unique_username()
            player = Player(
                player_id=uuid.uuid4(),
                api_key=str(uuid.uuid4()),
                username=username,
                username_canonical=username_canonical,
                balance=settings.starting_balance,
                last_login_date=date.today(),  # Set to today so no bonus on creation
            )
            self.db.add(player)
            try:
                await self.db.commit()
                await self.db.refresh(player)
                logger.info(
                    "Created player: %s username=%s balance=%s",
                    player.player_id,
                    player.username,
                    player.balance,
                )
                return player
            except IntegrityError as exc:
                await self.db.rollback()
                logger.warning(
                    "Username collision when creating player (attempt %s): %s",
                    attempt + 1,
                    exc,
                )

        raise RuntimeError("Failed to create player after multiple attempts")

    async def get_player_by_api_key(self, api_key: str) -> Player | None:
        """Get player by API key (for authentication)."""
        result = await self.db.execute(
            select(Player).where(Player.api_key == api_key)
        )
        return result.scalar_one_or_none()

    async def get_player_by_id(self, player_id: UUID) -> Player | None:
        """Get player by ID."""
        result = await self.db.execute(
            select(Player).where(Player.player_id == player_id)
        )
        return result.scalar_one_or_none()

    async def get_player_by_username(self, username: str) -> Player | None:
        """Get player by username lookup."""
        if not is_username_input_valid(username):
            return None
        username_service = UsernameService(self.db)
        return await username_service.find_player_by_username(username)

    async def get_player_by_google_sub(self, google_sub: str) -> Player | None:
        """Retrieve a player using their Google subject identifier."""
        result = await self.db.execute(
            select(Player).where(Player.google_sub == google_sub)
        )
        return result.scalar_one_or_none()

    async def login_with_google(
        self,
        google_sub: str,
        *,
        email: str | None = None,
        display_name: str | None = None,
    ) -> Player:
        """Get or create a player based on a verified Google login."""

        player = await self.get_player_by_google_sub(google_sub)
        today = date.today()

        if player:
            updated = False
            if email and player.email != email:
                player.email = email
                updated = True
            if player.last_login_date != today:
                player.last_login_date = today
                updated = True

            if updated:
                await self.db.commit()
                await self.db.refresh(player)

            return player

        return await self._create_google_player(
            google_sub,
            email=email,
            display_name=display_name,
        )

    async def _create_google_player(
        self,
        google_sub: str,
        *,
        email: str | None = None,
        display_name: str | None = None,
    ) -> Player:
        """Create a new player linked to a Google account."""

        username_service = UsernameService(self.db)

        preferred_username: str | None = None
        preferred_canonical: str | None = None

        if display_name and is_username_input_valid(display_name):
            normalized = normalize_username(display_name)
            canonical = canonicalize_username(normalized)
            if canonical:
                preferred_username = normalized
                preferred_canonical = canonical

        created_today = date.today()

        for attempt in range(6):
            if attempt == 0 and preferred_username and preferred_canonical:
                username = preferred_username
                username_canonical = preferred_canonical
            else:
                username, username_canonical = await username_service.generate_unique_username()

            player = Player(
                player_id=uuid.uuid4(),
                api_key=str(uuid.uuid4()),
                username=username,
                username_canonical=username_canonical,
                balance=settings.starting_balance,
                last_login_date=created_today,
                google_sub=google_sub,
                email=email,
            )

            self.db.add(player)

            try:
                await self.db.commit()
                await self.db.refresh(player)
                logger.info(
                    "Created Google player: %s email=%s",
                    player.player_id,
                    player.email,
                )
                return player
            except IntegrityError as exc:
                await self.db.rollback()
                logger.warning(
                    "Google player creation collision (attempt %s): %s",
                    attempt + 1,
                    exc,
                )
                preferred_username = None
                preferred_canonical = None

        raise RuntimeError("Failed to create Google-linked player after multiple attempts")

    async def is_daily_bonus_available(self, player: Player) -> bool:
        """Check if daily bonus can be claimed."""
        today = date.today()

        # No bonus on creation date
        if player.created_at.date() == today:
            return False

        # Bonus available if last_login_date is before today
        return player.last_login_date is None or player.last_login_date < today

    async def claim_daily_bonus(self, player: Player, transaction_service) -> int:
        """
        Claim daily bonus, returns amount.

        Raises:
            DailyBonusNotAvailableError: If bonus not available
        """
        if not await self.is_daily_bonus_available(player):
            raise DailyBonusNotAvailableError("Daily bonus not available")

        today = date.today()

        # Create bonus record
        bonus = DailyBonus(
            bonus_id=uuid.uuid4(),
            player_id=player.player_id,
            amount=settings.daily_bonus_amount,
            date=today,
        )
        self.db.add(bonus)

        # Update last_login_date
        player.last_login_date = today

        # Create transaction
        await transaction_service.create_transaction(
            player.player_id,
            settings.daily_bonus_amount,
            "daily_bonus",
            bonus.bonus_id,
        )

        await self.db.commit()

        logger.info(f"Player {player.player_id} claimed daily bonus: ${settings.daily_bonus_amount}")
        return settings.daily_bonus_amount

    async def get_outstanding_prompts_count(self, player_id: UUID) -> int:
        """Count phrasesets player created that are still open/closing."""
        # Find all rounds where player was the prompt player
        prompt_rounds_subq = (
            select(Round.round_id)
            .where(Round.player_id == player_id)
            .where(Round.round_type == "prompt")
            .where(Round.status == "submitted")
            .subquery()
        )

        # Count phrasesets linked to those rounds that are open/closing
        result = await self.db.execute(
            select(func.count(PhraseSet.phraseset_id))
            .where(PhraseSet.prompt_round_id.in_(select(prompt_rounds_subq)))
            .where(PhraseSet.status.in_(["open", "closing"]))
        )
        count = result.scalar() or 0
        logger.debug(f"Player {player_id} has {count} outstanding prompts")
        return count

    async def can_start_prompt_round(self, player: Player) -> tuple[bool, str]:
        """
        Check if player can start prompt round.

        Returns:
            (can_start, error_code)
        """
        # Check balance
        if player.balance < settings.prompt_cost:
            return False, "insufficient_balance"

        # Check active round
        if player.active_round_id is not None:
            return False, "already_in_round"

        # Check outstanding prompts
        count = await self.get_outstanding_prompts_count(player.player_id)
        if count >= settings.max_outstanding_prompts:
            return False, "max_outstanding_prompts"

        return True, ""

    async def can_start_copy_round(self, player: Player) -> tuple[bool, str]:
        """Check if player can start copy round."""
        from backend.services.queue_service import QueueService

        # Check balance (need to check against current cost)
        copy_cost = QueueService.get_copy_cost()
        if player.balance < copy_cost:
            return False, "insufficient_balance"

        # Check active round
        if player.active_round_id is not None:
            return False, "already_in_round"

        # Check prompts available
        if not QueueService.has_prompts_available():
            return False, "no_prompts_available"

        return True, ""

    async def can_start_vote_round(
        self,
        player: Player,
        vote_service=None,
        available_count: int | None = None,
    ) -> tuple[bool, str]:
        """Check if player can start vote round."""
        from backend.services.queue_service import QueueService

        # Check balance
        if player.balance < settings.vote_cost:
            return False, "insufficient_balance"

        # Check active round
        if player.active_round_id is not None:
            return False, "already_in_round"

        # Check phrasesets available
        if vote_service:
            if available_count is None:
                available_count = await vote_service.count_available_wordsets_for_player(player.player_id)
            if available_count == 0:
                return False, "no_wordsets_available"
        else:
            if not QueueService.has_wordsets_available():
                return False, "no_wordsets_available"

        return True, ""

    async def rotate_api_key(self, player: Player) -> str:
        """Generate new API key for player (security feature).

        Returns:
            str: The new API key
        """
        old_key = player.api_key
        new_key = str(uuid.uuid4())
        player.api_key = new_key
        await self.db.commit()
        await self.db.refresh(player)
        logger.info(f"Rotated API key for player {player.player_id}")
        return new_key
