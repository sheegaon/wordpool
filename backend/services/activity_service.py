"""Service for recording and querying phraseset activity."""
from __future__ import annotations

from datetime import datetime, UTC
from typing import Iterable, Optional
from uuid import UUID, uuid4

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.phraseset_activity import PhrasesetActivity


class ActivityService:
    """Business logic for phraseset activity tracking."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def record_activity(
        self,
        *,
        activity_type: str,
        phraseset_id: Optional[UUID] = None,
        prompt_round_id: Optional[UUID] = None,
        player_id: Optional[UUID] = None,
        metadata: Optional[dict] = None,
        created_at: Optional[datetime] = None,
    ) -> PhrasesetActivity:
        """Persist a new activity entry."""
        if phraseset_id is None and prompt_round_id is None:
            raise ValueError("phraseset_id or prompt_round_id is required")

        activity = PhrasesetActivity(
            activity_id=uuid4(),
            phraseset_id=phraseset_id,
            prompt_round_id=prompt_round_id,
            activity_type=activity_type,
            player_id=player_id,
            payload=metadata or {},
            created_at=created_at or datetime.now(UTC),
        )
        self.db.add(activity)
        await self.db.flush()
        return activity

    async def attach_phraseset_id(
        self,
        prompt_round_id: UUID,
        phraseset_id: UUID,
    ) -> None:
        """Update existing prompt-level activity rows once a phraseset exists."""
        await self.db.execute(
            update(PhrasesetActivity)
            .where(PhrasesetActivity.prompt_round_id == prompt_round_id)
            .where(PhrasesetActivity.phraseset_id.is_(None))
            .values(phraseset_id=phraseset_id)
        )
        await self.db.flush()

    async def get_phraseset_activity(
        self,
        phraseset_id: UUID,
    ) -> list[PhrasesetActivity]:
        """Load ordered activity timeline for a phraseset."""
        result = await self.db.execute(
            select(PhrasesetActivity)
            .where(PhrasesetActivity.phraseset_id == phraseset_id)
            .order_by(PhrasesetActivity.created_at.asc())
        )
        return list(result.scalars().all())

    async def get_activity_counts(
        self,
        phraseset_ids: Iterable[UUID],
        since: Optional[datetime] = None,
    ) -> dict[UUID, int]:
        """Return total (or recent) activity counts for a collection of phrasesets."""
        ids = list(phraseset_ids)
        if not ids:
            return {}

        stmt = (
            select(PhrasesetActivity.phraseset_id, func.count())
            .where(PhrasesetActivity.phraseset_id.in_(ids))
            .group_by(PhrasesetActivity.phraseset_id)
        )
        if since:
            stmt = stmt.where(PhrasesetActivity.created_at > since)

        result = await self.db.execute(stmt)
        return {row[0]: row[1] for row in result.all()}
