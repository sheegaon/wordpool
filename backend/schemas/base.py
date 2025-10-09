"""Base schemas with common configuration."""
from pydantic import BaseModel, ConfigDict
from datetime import datetime, UTC


def serialize_datetime_utc(dt: datetime) -> str:
    """
    Serialize datetime to ISO 8601 with explicit UTC timezone.

    This ensures JavaScript's Date constructor interprets the timestamp correctly.
    SQLite stores datetimes as naive strings, so we treat them as UTC.
    """
    if dt.tzinfo is None:
        # Treat naive datetimes as UTC
        dt = dt.replace(tzinfo=UTC)
    # Convert to UTC and format with 'Z' suffix
    return dt.astimezone(UTC).isoformat().replace('+00:00', 'Z')


class BaseSchema(BaseModel):
    """Base schema with common configuration for all API responses."""

    model_config = ConfigDict(
        from_attributes=True,
        # Use custom JSON serializers for datetimes
        json_encoders={
            datetime: serialize_datetime_utc,
        }
    )
