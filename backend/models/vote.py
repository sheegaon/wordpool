"""Vote model."""
from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, UTC
from backend.database import Base


def get_uuid_column(*args, **kwargs):
    return Column(PGUUID(as_uuid=True), *args, **kwargs)


class Vote(Base):
    """Vote model."""
    __tablename__ = "votes"

    vote_id = get_uuid_column(primary_key=True, default=uuid.uuid4)
    wordset_id = get_uuid_column(ForeignKey("wordsets.wordset_id"), nullable=False, index=True)
    player_id = get_uuid_column(ForeignKey("players.player_id"), nullable=False, index=True)
    voted_word = Column(String(15), nullable=False)
    correct = Column(Boolean, nullable=False)
    payout = Column(Integer, nullable=False)  # 5 or 0
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False, index=True)

    # Relationships
    wordset = relationship("WordSet", back_populates="votes")
    player = relationship("Player", back_populates="votes")

    # Constraints
    __table_args__ = (
        UniqueConstraint('player_id', 'wordset_id', name='uq_player_wordset_vote'),
    )

    def __repr__(self):
        return f"<Vote(vote_id={self.vote_id}, correct={self.correct}, payout={self.payout})>"
