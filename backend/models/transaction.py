"""Transaction ledger model."""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, UTC
from backend.database import Base


def get_uuid_column(*args, **kwargs):
    return Column(PGUUID(as_uuid=True), *args, **kwargs)


class Transaction(Base):
    """Transaction ledger model."""
    __tablename__ = "transactions"

    transaction_id = get_uuid_column(primary_key=True, default=uuid.uuid4)
    player_id = get_uuid_column(ForeignKey("players.player_id"), nullable=False, index=True)
    amount = Column(Integer, nullable=False)  # Negative for charges, positive for payouts
    type = Column(String(50), nullable=False, index=True)
    # Types: prompt_entry, copy_entry, vote_entry, vote_payout, prize_payout, refund, daily_bonus, system_contribution
    reference_id = get_uuid_column(nullable=True, index=True)  # References round_id, wordset_id, or vote_id
    balance_after = Column(Integer, nullable=False)  # For audit trail
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False, index=True)

    # Relationships
    player = relationship("Player", back_populates="transactions")

    # Indexes
    __table_args__ = (
        Index('ix_transactions_player_created', 'player_id', 'created_at'),
    )

    def __repr__(self):
        return f"<Transaction(transaction_id={self.transaction_id}, amount={self.amount}, type={self.type})>"
