"""Player model."""
from sqlalchemy import Column, String, Integer, DateTime, Date, ForeignKey
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, UTC, date
from backend.database import Base
from backend.models.base import get_uuid_column


class Player(Base):
    """Player account model."""
    __tablename__ = "players"

    player_id = get_uuid_column(primary_key=True, default=uuid.uuid4)
    api_key = Column(String(36), unique=True, nullable=False, index=True, default=lambda: str(uuid.uuid4()))
    balance = Column(Integer, default=1000, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    last_login_date = Column(Date, default=lambda: date.today(), nullable=True)
    active_round_id = get_uuid_column(ForeignKey("rounds.round_id", ondelete="SET NULL"), nullable=True)

    # Relationships
    active_round = relationship("Round", foreign_keys=[active_round_id], post_update=True)
    rounds = relationship("Round", back_populates="player", foreign_keys="Round.player_id")
    transactions = relationship("Transaction", back_populates="player")
    votes = relationship("Vote", back_populates="player")
    daily_bonuses = relationship("DailyBonus", back_populates="player")
    result_views = relationship("ResultView", back_populates="player")
    abandoned_prompts = relationship("PlayerAbandonedPrompt", back_populates="player")

    def __repr__(self):
        return f"<Player(player_id={self.player_id}, balance={self.balance})>"
