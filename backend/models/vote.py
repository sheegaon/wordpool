"""Vote model."""
from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, UTC
from backend.database import Base
from backend.models.base import get_uuid_column


class Vote(Base):
    """Vote model for player voting on wordsets."""
    __tablename__ = "votes"

    vote_id = get_uuid_column(primary_key=True, default=uuid.uuid4)
    wordset_id = get_uuid_column(ForeignKey("wordsets.wordset_id"), nullable=False, index=True)
    player_id = get_uuid_column(ForeignKey("players.player_id"), nullable=False, index=True)
    
    # Which word they voted for (matches one of: original_word, copy_word_1, copy_word_2)
    voted_word = Column(String(15), nullable=False)
    
    # Whether their vote was correct (voted for original_word)
    is_correct = Column("is_correct", Boolean, nullable=False)
    
    payout = Column(Integer, nullable=False)  # 5 or 0
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, index=True)

    # Relationships
    wordset = relationship("WordSet", back_populates="votes")
    player = relationship("Player", back_populates="votes")

    # Constraints
    __table_args__ = (
        UniqueConstraint('player_id', 'wordset_id', name='uq_player_wordset_vote'),
    )

    def __repr__(self):
        return f"<Vote(vote_id={self.vote_id}, correct={self.correct}, payout={self.payout})>"
