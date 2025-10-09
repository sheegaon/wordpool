"""Health check endpoint."""
from fastapi import APIRouter
from sqlalchemy import text
from backend.database import engine
from backend.utils import queue_client
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    # Check database
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "error",
            "detail": "Database connection failed"
        }, 503

    # Check queue backend
    queue_status = queue_client.backend

    return {
        "status": "ok",
        "database": db_status,
        "redis": queue_status,
    }
