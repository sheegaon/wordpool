"""Application configuration management."""
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = "sqlite+aiosqlite:///./wordpool.db"

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

    @model_validator(mode="after")
    def ensure_asyncpg(self):
        """Normalize Postgres URLs so SQLAlchemy uses the asyncpg driver."""
        url = self.database_url
        if url and url.startswith(("postgres://", "postgresql://")):
            scheme, sep, rest = url.partition("://")
            if "+asyncpg" not in scheme:
                self.database_url = f"postgresql+asyncpg://{rest}"
        return self

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
