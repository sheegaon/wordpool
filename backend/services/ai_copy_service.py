"""AI-powered copy generation service leveraging GPT as a backup player."""
from __future__ import annotations

import logging
import os
from datetime import UTC, datetime, timedelta
from typing import Iterable, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import get_settings
from backend.models.player import Player
from backend.models.round import Round
from backend.services.phrase_validator import get_phrase_validator
from backend.services.queue_service import QueueService

try:
    from backend.services.gemini_api import (
        GeminiError,
        build_copy_prompt,
        generate_copy_phrase,
    )
    _GEMINI_AVAILABLE = True
except ModuleNotFoundError:  # pragma: no cover - optional Gemini dependency
    class GeminiError(RuntimeError):
        """Fallback Gemini error when dependency not installed."""

    def build_copy_prompt(original_phrase: str, prompt_text: str) -> str:
        return (
            "You are playing a word game. Given an original phrase for a prompt, "
            "create a similar but different phrase that could fool voters.\n\n"
            "Rules:\n"
            "- 1-15 characters per word\n"
            "- 1-5 words total\n"
            "- Letters and spaces only\n"
            "- Must pass dictionary validation\n"
            "- Should be similar enough to be believable as the original\n"
            "- But different enough to not be identical\n\n"
            f"Original phrase: \"{original_phrase}\"\n"
            f"Prompt context: \"{prompt_text}\"\n\n"
            "Generate ONE alternative phrase only:"
        )

    async def generate_copy_phrase(*_: object, **__: object) -> str:
        raise GeminiError("Gemini support is not available")

    _GEMINI_AVAILABLE = False

try:  # pragma: no cover - optional dependency during tests
    from openai import AsyncOpenAI
except Exception:  # pragma: no cover - handled gracefully when OpenAI unavailable
    AsyncOpenAI = None  # type: ignore[assignment]


logger = logging.getLogger(__name__)


class AICopyServiceError(RuntimeError):
    """Raised when AI copy generation fails irrecoverably."""


class AICopyService:
    """Generate backup copy phrases using GPT when queues stall."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.settings = get_settings()
        self.phrase_validator = get_phrase_validator()
        self._client: Optional[AsyncOpenAI] = None
        self._ai_player_id: Optional[UUID] = None
        self._provider = (self.settings.ai_copy_provider or "").strip().lower() or "openai"

    async def run_backup_cycle(self) -> List[UUID]:
        """Generate AI copies for stale prompts.

        Returns a list of prompt round IDs that now have two submitted copies
        and are ready for phraseset creation.
        """

        client = self._get_client()
        if client is None:
            return []

        cutoff = datetime.now(UTC) - timedelta(seconds=self.settings.ai_copy_backup_delay_seconds)
        prompt_rounds = await self._load_stale_prompts(cutoff)
        if not prompt_rounds:
            return []

        ai_player = await self._get_or_create_ai_player()
        ready_prompt_ids: List[UUID] = []
        created_any = False

        for prompt_round in prompt_rounds:
            if not prompt_round.submitted_phrase:
                continue

            copies = await self._load_submitted_copies(prompt_round.round_id)
            if len(copies) >= 2:
                continue

            phrase = await self._generate_valid_phrase(
                client,
                prompt_round,
                copies,
            )
            if not phrase:
                continue

            previously_submitted = len(copies)
            copy_round = await self._persist_ai_copy(prompt_round, ai_player, phrase)
            if copy_round is None:
                continue

            copies.append(copy_round)
            created_any = True

            # When the AI provides the second copy, remove the prompt from the queue.
            if previously_submitted == 1:
                removed = QueueService.remove_prompt_from_queue(prompt_round.round_id)
                if not removed:
                    logger.debug(
                        "Prompt %s not found in queue during AI cleanup",
                        prompt_round.round_id,
                    )
                ready_prompt_ids.append(prompt_round.round_id)

        if created_any:
            await self.db.flush()
            await self.db.commit()

        return ready_prompt_ids

    def _get_client(self) -> Optional[object]:
        """Return configured AI client or readiness sentinel if available."""

        if self._provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if AsyncOpenAI is None or not api_key:
                return None

            if self._client is None:
                try:
                    self._client = AsyncOpenAI(api_key=api_key)
                except Exception as exc:  # pragma: no cover - defensive guard
                    logger.warning("Failed to initialize OpenAI client: %s", exc)
                    return None

            return self._client

        if self._provider == "gemini":
            if not _GEMINI_AVAILABLE:
                logger.warning("Gemini provider requested but dependency unavailable")
                return None

            if not os.getenv("GEMINI_API_KEY"):
                logger.warning("GEMINI_API_KEY environment variable must be set for Gemini provider")
                return None

            # Gemini client construction happens inside the helper function.
            return True

        logger.warning("Unknown AI copy provider '%s'", self._provider)
        return None

    async def _get_or_create_ai_player(self) -> Player:
        """Ensure there is a dedicated AI player record."""

        if self._ai_player_id:
            player = await self.db.get(Player, self._ai_player_id)
            if player:
                return player
            self._ai_player_id = None

        username = self.settings.ai_copy_player_username
        result = await self.db.execute(select(Player).where(Player.username == username))
        player = result.scalar_one_or_none()
        if player:
            self._ai_player_id = player.player_id
            return player

        player = Player(
            player_id=uuid4(),
            api_key=f"AI-{uuid4()}",
            username=username,
            username_canonical=username.lower(),
            balance=0,
        )
        self.db.add(player)
        await self.db.commit()
        await self.db.refresh(player)
        self._ai_player_id = player.player_id
        logger.info("Created AI copy player %s", player.player_id)
        return player

    async def _load_stale_prompts(self, cutoff: datetime) -> List[Round]:
        """Fetch prompt rounds waiting on copies past the configured cutoff."""

        stmt = (
            select(Round)
            .where(Round.round_type == "prompt")
            .where(Round.status == "submitted")
            .where(Round.phraseset_status.in_(["waiting_copies", "waiting_copy1"]))
            .where(Round.created_at <= cutoff)
            .order_by(Round.created_at.asc())
            .limit(self.settings.ai_copy_backup_batch_size)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().unique().all())

    async def _load_submitted_copies(self, prompt_round_id: UUID) -> List[Round]:
        """Load submitted copy rounds for a prompt."""

        stmt = (
            select(Round)
            .where(Round.round_type == "copy")
            .where(Round.prompt_round_id == prompt_round_id)
            .where(Round.status == "submitted")
            .order_by(Round.created_at.asc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def _generate_valid_phrase(
        self,
        client: object,
        prompt_round: Round,
        copies: Iterable[Round],
    ) -> Optional[str]:
        """Generate and validate a phrase, retrying on validation errors."""

        other_copy_phrase = next((copy.copy_phrase for copy in copies), None)
        attempts = self.settings.ai_copy_generation_attempts

        for attempt in range(attempts):
            try:
                candidate = await self._request_phrase(
                    client,
                    prompt_round.submitted_phrase or "",
                    prompt_round.prompt_text or "",
                )
            except Exception as exc:  # pragma: no cover - network errors
                logger.warning("GPT copy generation failed: %s", exc)
                return None

            if not candidate:
                continue

            cleaned = candidate.strip().upper()
            is_valid, error = self.phrase_validator.validate_copy(
                cleaned,
                prompt_round.submitted_phrase or "",
                other_copy_phrase,
                prompt_round.prompt_text or "",
            )
            if is_valid:
                return cleaned

            logger.info(
                "AI copy attempt rejected (%s/%s) for prompt %s: %s",
                attempt + 1,
                attempts,
                prompt_round.round_id,
                error,
            )

        return None

    async def _request_phrase(
        self,
        client: object,
        original_phrase: str,
        prompt_text: str,
    ) -> Optional[str]:
        """Call GPT to request a deceptive copy phrase."""

        if self._provider == "gemini":
            try:
                return await generate_copy_phrase(
                    original_phrase,
                    prompt_text,
                    model=self.settings.ai_copy_gemini_model,
                )
            except GeminiError as exc:  # pragma: no cover - network errors
                logger.warning("Gemini copy generation failed: %s", exc)
                return None

        if self._provider != "openai":
            logger.warning("Unsupported AI copy provider '%s'", self._provider)
            return None

        response = await client.chat.completions.create(
            model=self.settings.ai_copy_openai_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You help with a social deduction word game. "
                        "Provide a single short phrase that follows all rules."
                    ),
                },
                {
                    "role": "user",
                    "content": build_copy_prompt(original_phrase, prompt_text),
                },
            ],
            temperature=0.8,
            max_tokens=40,
        )

        if not response.choices:
            return None

        message = response.choices[0].message
        if message is None:
            return None

        content = message.content
        if isinstance(content, list):
            # Newer OpenAI SDKs can return a list of content parts.
            content = "".join(part.get("text", "") if isinstance(part, dict) else str(part) for part in content)

        return content.strip() if isinstance(content, str) else None

    async def _persist_ai_copy(
        self,
        prompt_round: Round,
        ai_player: Player,
        phrase: str,
    ) -> Optional[Round]:
        """Create a submitted copy round owned by the AI player."""

        if prompt_round.copy1_player_id and prompt_round.copy2_player_id:
            return None

        copy_round = Round(
            round_id=uuid4(),
            player_id=ai_player.player_id,
            round_type="copy",
            status="submitted",
            cost=0,
            expires_at=datetime.now(UTC),
            prompt_round_id=prompt_round.round_id,
            original_phrase=prompt_round.submitted_phrase,
            copy_phrase=phrase,
        )
        self.db.add(copy_round)

        if not prompt_round.copy1_player_id:
            prompt_round.copy1_player_id = ai_player.player_id
            prompt_round.phraseset_status = "waiting_copy1"
        elif not prompt_round.copy2_player_id:
            prompt_round.copy2_player_id = ai_player.player_id

        logger.info(
            "AI copy submitted for prompt %s by %s",
            prompt_round.round_id,
            ai_player.player_id,
        )

        return copy_round
