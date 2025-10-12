"""Result view tracking model."""
from sqlalchemy import Column, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
import uuid
from backend.database import Base
from backend.models.base import get_uuid_column, get_datetime_column, get_utc_now


class ResultView(Base):
    """Track when players view wordset results to prevent re-showing."""
    __tablename__ = "result_views"

    id = get_uuid_column(primary_key=True, default=uuid.uuid4)
    player_id = get_uuid_column(ForeignKey("players.player_id"), nullable=False, index=True)
    wordset_id = get_uuid_column(ForeignKey("wordsets.wordset_id"), nullable=False, index=True)
    viewed_at = get_datetime_column(default=get_utc_now, nullable=False)

    # Relationships
    player = relationship("Player", back_populates="result_views")
    wordset = relationship("WordSet", back_populates="result_views")

    # Constraints
    __table_args__ = (
        UniqueConstraint('player_id', 'wordset_id', name='uq_player_wordset_view'),
    )

    def __repr__(self):
        return f"<ResultView(player_id={self.player_id}, wordset_id={self.wordset_id})>"
