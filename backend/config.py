"""Application configuration management."""
from functools import lru_cache
import json
from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


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

    # Phrase Validation
    phrase_min_words: int = 1
    phrase_max_words: int = 5
    phrase_max_length: int = 100
    phrase_min_char_per_word: int = 2
    phrase_max_char_per_word: int = 15
    significant_word_min_length: int = 4

    # Similarity Checking
    similarity_threshold: float = 0.85  # Cosine similarity threshold for rejecting similar phrases
    similarity_model: str = "all-MiniLM-L6-v2"  # Sentence transformer model
    word_similarity_threshold: float = 0.85  # Minimum ratio for considering words too similar

    # Google OAuth
    google_client_id: str | None = None
    google_client_secret_path: str | None = None

    @model_validator(mode="after")
    def ensure_asyncpg(self):
        """Normalize Postgres URLs so SQLAlchemy uses the asyncpg driver."""
        url = self.database_url
        if url and url.startswith(("postgres://", "postgresql://")):
            scheme, sep, rest = url.partition("://")
            if "+asyncpg" not in scheme:
                self.database_url = f"postgresql+asyncpg://{rest}"
        return self

    @model_validator(mode="after")
    def load_google_client_id(self):
        """Populate Google client ID from client secret file when not provided."""
        if self.google_client_id:
            return self

        candidate_paths: list[Path] = []

        if self.google_client_secret_path:
            candidate_paths.append(Path(self.google_client_secret_path))

        frontend_dir = Path("frontend")
        if frontend_dir.exists():
            candidate_paths.extend(sorted(frontend_dir.glob("client_secret*.json")))

        for path in candidate_paths:
            if not path.exists() or not path.is_file():
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue

            client_id = (
                data.get("web", {}).get("client_id")
                or data.get("installed", {}).get("client_id")
            )

            if client_id:
                self.google_client_id = client_id
                break

        return self

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
