"""Transaction model for financial operations."""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, UTC
from backend.database import Base
from backend.models.base import get_uuid_column


class Transaction(Base):
    """Financial transaction model."""
    __tablename__ = "transactions"

    transaction_id = get_uuid_column(primary_key=True, default=uuid.uuid4)
    player_id = get_uuid_column(ForeignKey("players.player_id"), nullable=False, index=True)
    amount = Column(Integer, nullable=False)  # Cents, can be negative
    transaction_type = Column(String(20), nullable=False)  # prompt_entry, copy_entry, vote_entry, vote_win, prize, refund, daily_bonus
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, index=True)
    
    # Optional reference to related round/wordset
    related_round_id = get_uuid_column(ForeignKey("rounds.round_id"), nullable=True)
    related_wordset_id = get_uuid_column(ForeignKey("wordsets.wordset_id"), nullable=True)

    # Relationships
    player = relationship("Player", back_populates="transactions")

    # Indexes
    __table_args__ = (
        Index('ix_transactions_player_created', 'player_id', 'created_at'),
    )

    def __repr__(self):
        return f"<Transaction(transaction_id={self.transaction_id}, amount={self.amount}, transaction_type={self.transaction_type})>"
