"""Prompt feedback Pydantic schemas."""
from pydantic import BaseModel, Field
from backend.schemas.base import ConfigDict
from datetime import datetime
from uuid import UUID
from typing import Literal


class SubmitPromptFeedbackRequest(BaseModel):
    """Request to submit feedback on a prompt."""
    feedback_type: Literal['like', 'dislike'] = Field(
        ...,
        description="Type of feedback: 'like' for thumbs up, 'dislike' for thumbs down"
    )


class PromptFeedbackResponse(BaseModel):
    """Response after submitting feedback."""
    success: bool
    feedback_type: Literal['like', 'dislike']
    message: str = "Feedback submitted successfully"


class GetPromptFeedbackResponse(BaseModel):
    """Response when retrieving feedback for a round."""
    model_config = ConfigDict(from_attributes=True)
    feedback_type: Literal['like', 'dislike'] | None
    feedback_id: UUID | None = None
    created_at: datetime | None = None
