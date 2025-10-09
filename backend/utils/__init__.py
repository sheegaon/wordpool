"""Utilities module - queue and lock clients."""
from backend.config import get_settings
from backend.utils.queue_client import QueueClient
from backend.utils.lock_client import LockClient

settings = get_settings()

# Create singleton instances
queue_client = QueueClient(settings.redis_url if settings.redis_url else None)
lock_client = LockClient(settings.redis_url if settings.redis_url else None)

__all__ = ["queue_client", "lock_client"]
