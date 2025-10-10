"""Round-related Pydantic schemas."""
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from uuid import UUID
from backend.schemas.base import BaseSchema


class StartPromptRoundResponse(BaseSchema):
    """Start prompt round response."""
    round_id: UUID
    prompt_text: str
    expires_at: datetime
    cost: int


class StartCopyRoundResponse(BaseSchema):
    """Start copy round response."""
    round_id: UUID
    original_word: str
    prompt_round_id: UUID
    expires_at: datetime
    cost: int
    discount_active: bool


class StartVoteRoundResponse(BaseSchema):
    """Start vote round response."""
    round_id: UUID
    wordset_id: UUID
    prompt_text: str
    words: list[str]
    expires_at: datetime


class SubmitWordRequest(BaseModel):
    """Submit word request."""
    word: str = Field(..., min_length=2, max_length=15)

    @field_validator('word')
    @classmethod
    def word_must_be_alpha(cls, v: str) -> str:
        """Validate word contains only letters."""
        if not v.isalpha():
            raise ValueError('Word must contain only letters A-Z')
        return v.upper()


class SubmitWordResponse(BaseModel):
    """Submit word response."""
    success: bool
    word: str


class RoundAvailability(BaseModel):
    """Round availability status."""
    can_prompt: bool
    can_copy: bool
    can_vote: bool
    prompts_waiting: int
    wordsets_waiting: int
    copy_discount_active: bool
    copy_cost: int
    current_round_id: UUID | None


class RoundDetails(BaseSchema):
    """Round details response."""
    round_id: UUID
    type: str
    status: str
    expires_at: datetime
    prompt_text: str | None = None
    original_word: str | None = None
    submitted_word: str | None = None
    cost: int
