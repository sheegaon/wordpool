"""Vote-related Pydantic schemas."""
from pydantic import BaseModel
from backend.schemas.base import ConfigDict
from datetime import datetime
from uuid import UUID


class VoteDetail(BaseModel):
    """Vote detail."""
    model_config = ConfigDict(from_attributes=True)
    vote_id: UUID
    player_id: UUID
    voted_word: str
    correct: bool
    payout: int
    created_at: datetime
