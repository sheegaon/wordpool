"""Daily bonus model."""
from sqlalchemy import Column, Date, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from backend.database import Base
from backend.models.base import get_uuid_column, get_datetime_column, get_utc_now


class DailyBonus(Base):
    """Daily bonus tracking model."""
    __tablename__ = "daily_bonuses"

    id = get_uuid_column(primary_key=True)
    player_id = get_uuid_column(ForeignKey("players.player_id"), nullable=False, index=True)
    bonus_date = Column(Date, nullable=False, index=True)
    amount = Column(Integer, nullable=False, default=100)
    claimed_at = get_datetime_column(default=get_utc_now, nullable=False)

    # Relationships
    player = relationship("Player", back_populates="daily_bonuses")

    # Constraints - one bonus per player per day
    __table_args__ = (
        UniqueConstraint('player_id', 'bonus_date', name='uq_player_daily_bonus'),
    )

    def __repr__(self):
        return f"<DailyBonus(id={self.id}, player_id={self.player_id}, bonus_date={self.bonus_date})>"
