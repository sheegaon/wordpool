"""Application configuration management."""
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = "sqlite+aiosqlite:///./quipflip.db"

    # Redis (optional, falls back to in-memory)
    redis_url: str = ""

    # Application
    environment: str = "development"
    secret_key: str = "dev-secret-key-change-in-production"

    # Game Constants (all values in whole dollars)
    starting_balance: int = 1000
    daily_bonus_amount: int = 100
    prompt_cost: int = 100
    copy_cost_normal: int = 100
    copy_cost_discount: int = 90
    vote_cost: int = 1
    vote_payout_correct: int = 5
    wordset_prize_pool: int = 300
    max_outstanding_prompts: int = 10
    copy_discount_threshold: int = 10  # prompts waiting to trigger discount

    # Timing
    prompt_round_seconds: int = 180
    copy_round_seconds: int = 180
    vote_round_seconds: int = 60
    grace_period_seconds: int = 5

    # Phrase Validation
    phrase_min_words: int = 1
    phrase_max_words: int = 5
    phrase_max_length: int = 100
    phrase_min_char_per_word: int = 2
    phrase_max_char_per_word: int = 15
    significant_word_min_length: int = 4

    # Similarity Checking
    similarity_threshold: float = 0.8  # Cosine similarity threshold for rejecting similar phrases
    similarity_model: str = "all-mpnet-base-v2"  # previously "all-MiniLM-L6-v2"  # Sentence transformer model
    word_similarity_threshold: float = 0.8  # Minimum ratio for considering words too similar

    # AI backup copies
    ai_copy_backup_delay_seconds: int = 600
    ai_copy_backup_batch_size: int = 3
    ai_copy_generation_attempts: int = 3
    ai_copy_provider: str = "openai"
    ai_copy_openai_model: str = "gpt-5-nano"
    ai_copy_gemini_model: str = "gemini-2.5-flash-lite"
    ai_copy_player_username: str = "AI Copycat"

    @model_validator(mode="after")
    def ensure_asyncpg(self):
        """Normalize Postgres URLs so SQLAlchemy uses the asyncpg driver."""
        url = self.database_url
        if url and url.startswith(("postgres://", "postgresql://")):
            scheme, sep, rest = url.partition("://")
            if "+asyncpg" not in scheme:
                self.database_url = f"postgresql+asyncpg://{rest}"
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
