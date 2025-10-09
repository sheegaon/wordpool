"""Vote-related Pydantic schemas."""
from pydantic import BaseModel
from datetime import datetime
from uuid import UUID


class VoteDetail(BaseModel):
    """Vote detail."""
    vote_id: UUID
    player_id: UUID
    voted_word: str
    correct: bool
    payout: int
    created_at: datetime

    class Config:
        from_attributes = True
