"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import get_settings
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="WordPool API",
    description="Phase 1 MVP - Word association game backend",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and register routers
from backend.routers import health, player, rounds, wordsets

app.include_router(health.router, tags=["health"])
app.include_router(player.router, prefix="/player", tags=["player"])
app.include_router(rounds.router, prefix="/rounds", tags=["rounds"])
app.include_router(wordsets.router, prefix="/wordsets", tags=["wordsets"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "WordPool API - Phase 1 MVP",
        "version": "1.0.0",
        "environment": settings.environment,
        "docs": "/docs",
    }


@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    logger.info("=" * 60)
    logger.info("WordPool API Starting")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Database: {settings.database_url.split('@')[-1] if '@' in settings.database_url else 'SQLite'}")
    logger.info(f"Redis: {'Enabled' if settings.redis_url else 'In-Memory Fallback'}")
    logger.info("=" * 60)

    # Initialize word validator
    from backend.services import get_word_validator
    try:
        validator = get_word_validator()
        logger.info(f"Word validator initialized with {len(validator.dictionary)} words")
    except Exception as e:
        logger.error(f"Failed to initialize word validator: {e}")
        logger.error("Run: python3 scripts/download_dictionary.py")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    logger.info("WordPool API Shutting Down")
