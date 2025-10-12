"""Phraseset-related Pydantic schemas."""
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from uuid import UUID
from backend.schemas.base import BaseSchema
import re


class VoteRequest(BaseModel):
    """Vote submission request."""
    phrase: str = Field(..., min_length=2, max_length=100)

    @field_validator('phrase')
    @classmethod
    def phrase_must_be_valid(cls, v: str) -> str:
        """Validate phrase contains only letters and spaces."""
        if not re.match(r'^[a-zA-Z\s]+$', v):
            raise ValueError('Phrase must contain only letters A-Z and spaces')
        # Normalize whitespace
        v = re.sub(r'\s+', ' ', v.strip())
        return v.upper()


class VoteResponse(BaseModel):
    """Immediate vote feedback."""
    correct: bool
    payout: int
    original_phrase: str
    your_choice: str


class PhraseVoteCount(BaseModel):
    """Phrase with vote count."""
    phrase: str
    vote_count: int
    is_original: bool


class PhraseSetResults(BaseSchema):
    """Complete phraseset results."""
    prompt_text: str
    votes: list[PhraseVoteCount]
    your_phrase: str
    your_role: str  # "prompt" or "copy"
    your_points: int
    your_payout: int
    total_pool: int
    total_votes: int
    already_collected: bool
    finalized_at: datetime
