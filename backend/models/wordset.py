"""WordSet model."""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, UTC
from backend.database import Base


def get_uuid_column(*args, **kwargs):
    return Column(PGUUID(as_uuid=True), *args, **kwargs)


class WordSet(Base):
    """WordSet model for voting."""
    __tablename__ = "wordsets"

    wordset_id = get_uuid_column(primary_key=True, default=uuid.uuid4)
    prompt_round_id = get_uuid_column(ForeignKey("rounds.round_id"), nullable=False, index=True)
    copy_round_1_id = get_uuid_column(ForeignKey("rounds.round_id"), nullable=False)
    copy_round_2_id = get_uuid_column(ForeignKey("rounds.round_id"), nullable=False)

    # Denormalized fields for performance
    prompt_text = Column(String(500), nullable=False)
    original_word = Column(String(15), nullable=False)  # Prompt player's word
    copy_word_1 = Column(String(15), nullable=False)
    copy_word_2 = Column(String(15), nullable=False)

    # Vote lifecycle
    status = Column(String(20), nullable=False, default="open")  # open, closing, closed, finalized
    vote_count = Column(Integer, default=0, nullable=False)
    third_vote_at = Column(DateTime, nullable=True)
    fifth_vote_at = Column(DateTime, nullable=True, index=True)
    closes_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    finalized_at = Column(DateTime, nullable=True)

    # Prize pool
    total_pool = Column(Integer, default=300, nullable=False)
    system_contribution = Column(Integer, default=0, nullable=False)  # 0 or 10

    # Relationships
    prompt_round = relationship("Round", foreign_keys=[prompt_round_id])
    copy_round_1 = relationship("Round", foreign_keys=[copy_round_1_id])
    copy_round_2 = relationship("Round", foreign_keys=[copy_round_2_id])
    votes = relationship("Vote", back_populates="wordset")
    vote_rounds = relationship("Round", back_populates="wordset", foreign_keys="Round.wordset_id")
    result_views = relationship("ResultView", back_populates="wordset")

    # Indexes
    __table_args__ = (
        Index('ix_wordsets_status_vote_count', 'status', 'vote_count'),
    )

    def __repr__(self):
        return f"<WordSet(wordset_id={self.wordset_id}, status={self.status}, vote_count={self.vote_count})>"
