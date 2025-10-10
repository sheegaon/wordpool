"""WordSet model for voting phase."""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, UTC
from backend.database import Base
from backend.models.base import get_uuid_column


class WordSet(Base):
    """WordSet model for complete sets ready for voting."""
    __tablename__ = "wordsets"

    wordset_id = get_uuid_column(primary_key=True, default=uuid.uuid4)
    prompt_round_id = get_uuid_column(ForeignKey("rounds.round_id"), nullable=False, unique=True, index=True)
    copy_round_1_id = get_uuid_column(ForeignKey("rounds.round_id"), nullable=False, unique=True)
    copy_round_2_id = get_uuid_column(ForeignKey("rounds.round_id"), nullable=False, unique=True)
    
    # Denormalized data for voting display
    prompt_text = Column(String(500), nullable=False)
    original_word = Column(String(15), nullable=False)
    copy_word_1 = Column(String(15), nullable=False)
    copy_word_2 = Column(String(15), nullable=False)
    
    # State tracking
    status = Column(String(20), nullable=False, default="open")  # open, closing, closed
    vote_count = Column(Integer, default=0, nullable=False)
    total_pool = Column(Integer, default=300, nullable=False)  # Cents
    system_contribution = Column(Integer, default=0, nullable=False)  # Cents
    
    # Timing
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    fifth_vote_at = Column(DateTime(timezone=True), nullable=True)  # When 5th vote received
    closed_at = Column(DateTime(timezone=True), nullable=True)

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
