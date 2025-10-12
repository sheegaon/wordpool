"""Base model utilities and common column types."""
from enum import Enum
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy import String as SQLString
import uuid
from datetime import datetime, UTC
from backend.config import get_settings


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


class GUID(TypeDecorator):
    """Platform-independent GUID type.
    
    Uses PostgreSQL's UUID type when available,
    otherwise uses CHAR(36) storing as stringified hex values.
    """
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PGUUID())
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return str(uuid.UUID(value))
            else:
                return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                return uuid.UUID(value)
            return value


def get_uuid_column(*args, **kwargs):
    """Get a UUID column that works across databases."""
    return Column(GUID(), *args, **kwargs)


def get_datetime_column(timezone_aware=True, **kwargs):
    """Get a DateTime column that works across databases.
    
    Args:
        timezone_aware: Whether to store timezone info (PostgreSQL only)
        **kwargs: Additional Column arguments
    
    Returns:
        Column configured appropriately for the database type
    """
    settings = get_settings()
    
    if settings.is_postgres and timezone_aware:
        # PostgreSQL with timezone support
        return Column(DateTime(timezone=True), **kwargs)
    else:
        # SQLite or PostgreSQL without timezone
        return Column(DateTime, **kwargs)


def get_utc_now():
    """Get current UTC datetime that works across databases.
    
    For PostgreSQL: Returns timezone-aware datetime
    For SQLite: Returns naive datetime (SQLite doesn't support timezones)
    """
    settings = get_settings()
    
    if settings.is_postgres:
        return datetime.now(UTC)
    else:
        # SQLite - store as naive UTC datetime
        return datetime.utcnow()
