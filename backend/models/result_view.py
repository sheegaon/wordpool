"""Result view tracking for idempotent prize collection."""
from sqlalchemy import Column, Integer, DateTime, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, UTC
from backend.database import Base
from backend.models.base import get_uuid_column


class ResultView(Base):
    """Track when players view wordset results to prevent re-showing."""
    __tablename__ = "result_views"

    view_id = get_uuid_column(primary_key=True, default=uuid.uuid4)
    wordset_id = get_uuid_column(ForeignKey("wordsets.wordset_id"), nullable=False, index=True)
    player_id = get_uuid_column(ForeignKey("players.player_id"), nullable=False, index=True)
    payout_collected = Column(Boolean, default=False, nullable=False, index=True)
    payout_amount = Column(Integer, nullable=False)
    viewed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    # Relationships
    wordset = relationship("WordSet", back_populates="result_views")
    player = relationship("Player", back_populates="result_views")

    # Constraints - one view per player per wordset
    __table_args__ = (
        UniqueConstraint('player_id', 'wordset_id', name='uq_player_wordset_result'),
    )

    def __repr__(self):
        return f"<ResultView(view_id={self.view_id}, collected={self.payout_collected})>"
