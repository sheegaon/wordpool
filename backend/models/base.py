"""Base utilities for SQLAlchemy models."""
from enum import Enum
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import UUID as PGUUID


class RoundType(str, Enum):
    """Round type enumeration for type safety."""
    PROMPT = "prompt"
    COPY = "copy"
    VOTE = "vote"


class RoundStatus(str, Enum):
    """Round status enumeration for type safety."""
    ACTIVE = "active"
    SUBMITTED = "submitted"
    EXPIRED = "expired"
    ABANDONED = "abandoned"


class WordSetStatus(str, Enum):
    """WordSet status enumeration for type safety."""
    OPEN = "open"
    CLOSING = "closing"
    CLOSED = "closed"
    FINALIZED = "finalized"


def get_uuid_column(*args, **kwargs):
    """Get UUID column type based on database dialect.

    Returns a SQLAlchemy Column configured for UUID storage.
    Uses PostgreSQL UUID type with as_uuid=True for proper UUID handling.

    Args:
        *args: Positional arguments to pass to Column (e.g., ForeignKey)
        **kwargs: Keyword arguments to pass to Column (e.g., primary_key=True)

    Returns:
        Column: Configured SQLAlchemy Column for UUID storage

    Example:
        player_id = get_uuid_column(primary_key=True, default=uuid.uuid4)
        foreign_id = get_uuid_column(ForeignKey("table.id"), nullable=True)
    """
    return Column(
        PGUUID(as_uuid=True),
        *args,
        **kwargs
    )
