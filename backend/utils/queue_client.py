"""Queue client abstraction - Redis or in-memory fallback."""
import json
from typing import Optional, List
from queue import Queue, Empty
from threading import Lock
import logging

logger = logging.getLogger(__name__)


class QueueClient:
    """Abstraction for queues - uses Redis if available, else in-memory."""

    def __init__(self, redis_url: Optional[str] = None):
        self.backend = "memory"
        self._memory_queues: dict[str, Queue] = {}
        self._memory_lock = Lock()

        if redis_url:
            try:
                import redis
                self.redis = redis.from_url(redis_url, decode_responses=True)
                self.redis.ping()
                self.backend = "redis"
                logger.info("Using Redis for queues")
            except Exception as e:
                logger.warning(f"Redis not available, using in-memory queues: {e}")
        else:
            logger.info("Using in-memory queues (Redis URL not provided)")

    def push(self, queue_name: str, item: dict):
        """Add item to end of queue."""
        if self.backend == "redis":
            self.redis.rpush(queue_name, json.dumps(item))
        else:
            with self._memory_lock:
                if queue_name not in self._memory_queues:
                    self._memory_queues[queue_name] = Queue()
                self._memory_queues[queue_name].put(item)

    def pop(self, queue_name: str) -> Optional[dict]:
        """Remove and return item from front of queue."""
        if self.backend == "redis":
            result = self.redis.lpop(queue_name)
            return json.loads(result) if result else None
        else:
            with self._memory_lock:
                if queue_name not in self._memory_queues:
                    return None
                try:
                    return self._memory_queues[queue_name].get_nowait()
                except Empty:
                    return None

    def length(self, queue_name: str) -> int:
        """Get queue length."""
        if self.backend == "redis":
            return self.redis.llen(queue_name)
        else:
            with self._memory_lock:
                if queue_name not in self._memory_queues:
                    return 0
                return self._memory_queues[queue_name].qsize()

    def peek(self, queue_name: str, index: int = 0) -> Optional[dict]:
        """View item at index without removing it."""
        if self.backend == "redis":
            result = self.redis.lindex(queue_name, index)
            return json.loads(result) if result else None
        else:
            # In-memory doesn't support peek efficiently, return None
            return None

    def remove(self, queue_name: str, item: dict) -> bool:
        """Remove specific item from queue (for abandoned rounds)."""
        if self.backend == "redis":
            # Redis LREM removes all occurrences
            removed = self.redis.lrem(queue_name, 1, json.dumps(item))
            return removed > 0
        else:
            # In-memory doesn't support remove efficiently
            # For MVP, we'll just skip this functionality
            return False
