"""Player-related Pydantic schemas."""
from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional
from uuid import UUID
from backend.schemas.base import BaseSchema


class PlayerBalance(BaseSchema):
    """Player balance response."""
    balance: int
    starting_balance: int
    daily_bonus_available: bool
    daily_bonus_amount: int
    last_login_date: Optional[date]
    outstanding_prompts: int


class ClaimDailyBonusResponse(BaseModel):
    """Daily bonus claim response."""
    success: bool
    amount: int
    new_balance: int


class CurrentRoundResponse(BaseSchema):
    """Current active round response."""
    round_id: Optional[UUID]
    round_type: Optional[str]
    state: Optional[dict]
    expires_at: Optional[datetime]


class PendingResult(BaseSchema):
    """Pending result item."""
    wordset_id: UUID
    prompt_text: str
    completed_at: datetime
    role: str  # "prompt" or "copy"
    payout_collected: bool


class PendingResultsResponse(BaseModel):
    """List of pending results."""
    pending: list[PendingResult]


class CreatePlayerResponse(BaseModel):
    """Create player response with API key."""
    player_id: UUID
    api_key: str
    balance: int
    message: str


class RotateKeyResponse(BaseModel):
    """Rotate API key response."""
    new_api_key: str
    message: str
