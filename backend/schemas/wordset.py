"""Wordset-related Pydantic schemas."""
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from uuid import UUID
from backend.schemas.base import BaseSchema


class VoteRequest(BaseModel):
    """Vote submission request."""
    word: str = Field(..., min_length=2, max_length=15)

    @field_validator('word')
    @classmethod
    def word_must_be_alpha(cls, v: str) -> str:
        """Validate word contains only letters."""
        if not v.isalpha():
            raise ValueError('Word must contain only letters A-Z')
        return v.upper()


class VoteResponse(BaseModel):
    """Immediate vote feedback."""
    correct: bool
    payout: int
    original_word: str
    your_choice: str


class WordVoteCount(BaseModel):
    """Word with vote count."""
    word: str
    vote_count: int
    is_original: bool


class WordSetResults(BaseSchema):
    """Complete wordset results."""
    prompt_text: str
    votes: list[WordVoteCount]
    your_word: str
    your_role: str  # "prompt" or "copy"
    your_points: int
    your_payout: int
    total_pool: int
    total_votes: int
    already_collected: bool
    finalized_at: datetime
