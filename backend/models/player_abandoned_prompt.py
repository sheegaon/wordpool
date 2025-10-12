"""Player abandoned prompt tracking model."""
from sqlalchemy import Column, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
import uuid
from backend.database import Base
from backend.models.base import get_uuid_column, get_datetime_column, get_utc_now


class PlayerAbandonedPrompt(Base):
    """Track when players abandon copy rounds to prevent immediate retry."""
    __tablename__ = "player_abandoned_prompts"

    id = get_uuid_column(primary_key=True, default=uuid.uuid4)
    player_id = get_uuid_column(ForeignKey("players.player_id"), nullable=False, index=True)
    prompt_round_id = get_uuid_column(ForeignKey("rounds.round_id"), nullable=False)
    abandoned_at = get_datetime_column(default=get_utc_now, nullable=False)

    # Relationships
    player = relationship("Player", back_populates="abandoned_prompts")

    # Constraints
    __table_args__ = (
        UniqueConstraint('player_id', 'prompt_round_id', name='uq_player_abandoned_prompt'),
    )

    def __repr__(self):
        return f"<PlayerAbandonedPrompt(player_id={self.player_id}, abandoned_at={self.abandoned_at})>"
