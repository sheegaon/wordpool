"""Pytest configuration and fixtures."""
import os
import asyncio
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config as AlembicConfig


# Ensure the application uses a dedicated SQLite database during tests
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"

from backend.config import get_settings


BASE_DIR = Path(__file__).resolve().parent.parent
TEST_DB_PATH = BASE_DIR / "test.db"
settings = get_settings()


@pytest.fixture(scope="session", autouse=True)
def apply_migrations():
    """Apply database migrations against the test database."""
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()

    alembic_cfg = AlembicConfig(str(BASE_DIR / "alembic.ini"))
    alembic_cfg.set_main_option("sqlalchemy.url", settings.database_url)
    command.upgrade(alembic_cfg, "head")

    yield

    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
