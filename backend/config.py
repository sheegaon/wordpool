"""Application configuration management."""
from pydantic import field_validator, ValidationInfo
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
    prompt_round_seconds: int = 60
    copy_round_seconds: int = 60
    vote_round_seconds: int = 15
    grace_period_seconds: int = 5

    @field_validator("database_url", mode='before')
    @classmethod
    def fix_postgres_url(cls, v: str, info: ValidationInfo):
        """Ensure postgres URLs use the async driver required by SQLAlchemy."""
        environment = info.data.get("environment", "development")
        if environment != "development" and v:
            if v.startswith("postgresql+"):
                return v
            if v.startswith("postgres://"):
                return "postgresql+asyncpg://" + v[len("postgres://"):]
            if v.startswith("postgresql://"):
                return "postgresql+asyncpg://" + v[len("postgresql://"):]
        return v

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
