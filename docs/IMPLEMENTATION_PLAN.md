# Phase 1 MVP Implementation Plan

## Overview

This document outlines the complete step-by-step implementation plan for the WordPool Phase 1 MVP backend. Each step includes clear deliverables, testing criteria, and dependencies.

---

## Project Structure

```
wordpool/
├── backend/
│   ├── __init__.py
│   ├── main.py                     # FastAPI app entry point
│   ├── config.py                   # Configuration management
│   ├── database.py                 # Database connection setup
│   ├── dependencies.py             # FastAPI dependencies (auth, etc.)
│   ├── models/                     # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── player.py
│   │   ├── prompt.py
│   │   ├── round.py               # Unified round model
│   │   ├── wordset.py
│   │   ├── vote.py
│   │   ├── transaction.py
│   │   ├── daily_bonus.py
│   │   ├── result_view.py
│   │   └── player_abandoned_prompt.py
│   ├── schemas/                    # Pydantic schemas for API
│   │   ├── __init__.py
│   │   ├── player.py
│   │   ├── round.py
│   │   ├── wordset.py
│   │   └── vote.py
│   ├── services/                   # Business logic
│   │   ├── __init__.py
│   │   ├── player_service.py
│   │   ├── round_service.py
│   │   ├── vote_service.py
│   │   ├── word_validator.py
│   │   ├── queue_service.py
│   │   ├── scoring_service.py
│   │   └── transaction_service.py
│   ├── routers/                    # API endpoints
│   │   ├── __init__.py
│   │   ├── player.py
│   │   ├── rounds.py
│   │   ├── wordsets.py
│   │   └── health.py
│   ├── utils/                      # Utilities
│   │   ├── __init__.py
│   │   ├── queue_client.py        # Redis/in-memory queue abstraction
│   │   ├── lock_client.py         # Redis/threading lock abstraction
│   │   └── exceptions.py          # Custom exceptions
│   └── migrations/                 # Alembic migrations
│       ├── env.py
│       ├── script.py.mako
│       └── versions/
├── tests/
│   ├── __init__.py
│   ├── conftest.py                # Pytest fixtures
│   ├── test_player_service.py
│   ├── test_round_service.py
│   ├── test_vote_service.py
│   ├── test_word_validator.py
│   ├── test_queue_service.py
│   ├── test_scoring_service.py
│   ├── test_transaction_service.py
│   ├── test_api_player.py
│   ├── test_api_rounds.py
│   ├── test_api_wordsets.py
│   └── test_integration.py        # End-to-end tests
├── scripts/
│   ├── seed_prompts.py            # Populate prompt library
│   └── download_dictionary.py     # Download word list
├── docker-compose.yml
├── Dockerfile
├── heroku.yml
├── requirements.txt
├── alembic.ini
├── .env.example
├── .gitignore
└── docs/
    ├── ARCHITECTURE.md (updated)
    ├── API.md (new)
    └── MVP_SUMMARY.md (new)
```

---

## Implementation Steps

### **Step 1: Project Setup & Dependencies**

**Goal**: Set up the project structure and install all dependencies

**Tasks**:
1. Create `requirements.txt` with core dependencies:
   - `fastapi`
   - `uvicorn[standard]`
   - `sqlalchemy[asyncio]`
   - `asyncpg` (PostgreSQL async driver)
   - `aiosqlite` (SQLite async fallback)
   - `alembic` (migrations)
   - `redis` (optional, for queue/lock)
   - `pydantic[email]`
   - `python-dotenv`
   - `pytest`
   - `pytest-asyncio`
   - `httpx` (for testing)
   - `faker` (for test data)

2. Create `.env.example`:
   ```
   DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/wordpool
   # DATABASE_URL=sqlite+aiosqlite:///./wordpool.db  # Fallback
   REDIS_URL=redis://localhost:6379  # Optional, falls back to in-memory
   ENVIRONMENT=development
   SECRET_KEY=your-secret-key-here
   ```

3. Create `.gitignore`:
   - `.env`
   - `__pycache__/`
   - `*.pyc`
   - `.pytest_cache/`
   - `wordpool.db`
   - `.vscode/`, `.idea/`

4. Create basic directory structure

**Test Criteria**:
- [ ] `pip install -r requirements.txt` succeeds
- [ ] All directories created
- [ ] `.env` file created from `.env.example`

**Verification**:
```bash
pip install -r requirements.txt
python -c "import fastapi; import sqlalchemy; print('OK')"
```

---

### **Step 2: Docker & Deployment Configuration**

**Goal**: Create containerization and deployment configs

**Tasks**:
1. Create `Dockerfile`:
   ```dockerfile
   FROM python:3.11-slim

   WORKDIR /app

   # Install dependencies
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt

   # Copy application
   COPY . .

   # Run migrations and start server
   CMD alembic upgrade head && uvicorn backend.main:app --host 0.0.0.0 --port $PORT
   ```

2. Create `docker-compose.yml` for local development:
   ```yaml
   version: '3.8'
   services:
     api:
       build: .
       ports:
         - "8000:8000"
       environment:
         - DATABASE_URL=postgresql+asyncpg://wordpool:wordpool@db:5432/wordpool
         - REDIS_URL=redis://redis:6379
       depends_on:
         - db
         - redis
       command: uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

     db:
       image: postgres:15
       environment:
         POSTGRES_USER: wordpool
         POSTGRES_PASSWORD: wordpool
         POSTGRES_DB: wordpool
       ports:
         - "5432:5432"
       volumes:
         - postgres_data:/var/lib/postgresql/data

     redis:
       image: redis:7-alpine
       ports:
         - "6379:6379"

   volumes:
     postgres_data:
   ```

3. Create `heroku.yml`:
   ```yaml
   build:
     docker:
       web: Dockerfile
   run:
     web: alembic upgrade head && uvicorn backend.main:app --host 0.0.0.0 --port $PORT
   ```

**Test Criteria**:
- [ ] `docker-compose up` starts all services
- [ ] Heroku configuration valid

**Verification**:
```bash
docker-compose up -d
curl http://localhost:8000  # Should error (no routes yet) but connect
docker-compose down
```

---

### **Step 3: Configuration Management**

**Goal**: Set up environment-based configuration

**Tasks**:
1. Create `backend/config.py`:
   ```python
   from pydantic_settings import BaseSettings
   from functools import lru_cache

   class Settings(BaseSettings):
       # Database
       database_url: str = "sqlite+aiosqlite:///./wordpool.db"

       # Redis (optional)
       redis_url: str = ""  # Empty = use in-memory fallback

       # App
       environment: str = "development"
       secret_key: str = "dev-secret-key-change-in-production"

       # Game constants
       starting_balance: int = 1000
       daily_bonus_amount: int = 100
       prompt_cost: int = 100
       copy_cost_normal: int = 100
       copy_cost_discount: int = 90
       vote_cost: int = 1
       vote_payout_correct: int = 5
       wordset_prize_pool: int = 300
       max_outstanding_prompts: int = 10
       copy_discount_threshold: int = 10  # prompts waiting

       class Config:
           env_file = ".env"

   @lru_cache()
   def get_settings() -> Settings:
       return Settings()
   ```

**Test Criteria**:
- [ ] Settings load from environment
- [ ] Defaults work when no `.env`
- [ ] Can override via environment variables

**Verification**:
```python
from backend.config import get_settings
settings = get_settings()
assert settings.starting_balance == 1000
print("Config OK")
```

---

### **Step 4: Database Setup**

**Goal**: Configure async SQLAlchemy with Postgres/SQLite fallback

**Tasks**:
1. Create `backend/database.py`:
   ```python
   from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
   from sqlalchemy.orm import declarative_base
   from backend.config import get_settings

   settings = get_settings()

   # Create async engine
   engine = create_async_engine(
       settings.database_url,
       echo=settings.environment == "development",
       future=True,
   )

   # Session factory
   AsyncSessionLocal = async_sessionmaker(
       engine,
       class_=AsyncSession,
       expire_on_commit=False,
   )

   # Base class for models
   Base = declarative_base()

   # Dependency for FastAPI
   async def get_db():
       async with AsyncSessionLocal() as session:
           yield session
   ```

2. Set up Alembic:
   ```bash
   alembic init backend/migrations
   ```

3. Configure `alembic.ini`:
   - Set `script_location = backend/migrations`
   - Set `sqlalchemy.url = ` (will use env var)

4. Update `backend/migrations/env.py`:
   ```python
   from backend.database import Base
   from backend.config import get_settings
   from backend.models import *  # Import all models

   target_metadata = Base.metadata

   config.set_main_option("sqlalchemy.url", get_settings().database_url)
   ```

**Test Criteria**:
- [ ] Database connection works
- [ ] Alembic initialized

**Verification**:
```python
import asyncio
from backend.database import engine

async def test_connection():
    async with engine.begin() as conn:
        await conn.execute("SELECT 1")
    print("Database connection OK")

asyncio.run(test_connection())
```

---

### **Step 5: Queue & Lock Clients (Abstraction Layer)**

**Goal**: Create Redis abstraction with in-memory fallback

**Tasks**:
1. Create `backend/utils/queue_client.py`:
   ```python
   import redis
   from typing import Optional, List
   import json
   from queue import Queue, Empty
   from threading import Lock

   class QueueClient:
       """Abstraction for queues - uses Redis if available, else in-memory"""

       def __init__(self, redis_url: Optional[str] = None):
           self.backend = "memory"
           self._memory_queues: dict[str, Queue] = {}
           self._memory_lock = Lock()

           if redis_url:
               try:
                   self.redis = redis.from_url(redis_url, decode_responses=True)
                   self.redis.ping()
                   self.backend = "redis"
               except Exception:
                   pass  # Fall back to memory

       def push(self, queue_name: str, item: dict):
           if self.backend == "redis":
               self.redis.rpush(queue_name, json.dumps(item))
           else:
               with self._memory_lock:
                   if queue_name not in self._memory_queues:
                       self._memory_queues[queue_name] = Queue()
                   self._memory_queues[queue_name].put(item)

       def pop(self, queue_name: str) -> Optional[dict]:
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
           if self.backend == "redis":
               return self.redis.llen(queue_name)
           else:
               with self._memory_lock:
                   if queue_name not in self._memory_queues:
                       return 0
                   return self._memory_queues[queue_name].qsize()
   ```

2. Create `backend/utils/lock_client.py`:
   ```python
   import redis
   from typing import Optional
   from threading import Lock as ThreadLock
   from contextlib import contextmanager

   class LockClient:
       """Abstraction for distributed locks - uses Redis if available, else threading"""

       def __init__(self, redis_url: Optional[str] = None):
           self.backend = "memory"
           self._memory_locks: dict[str, ThreadLock] = {}

           if redis_url:
               try:
                   self.redis = redis.from_url(redis_url, decode_responses=True)
                   self.redis.ping()
                   self.backend = "redis"
               except Exception:
                   pass

       @contextmanager
       def lock(self, lock_name: str, timeout: int = 10):
           if self.backend == "redis":
               lock = self.redis.lock(lock_name, timeout=timeout)
               lock.acquire()
               try:
                   yield
               finally:
                   lock.release()
           else:
               if lock_name not in self._memory_locks:
                   self._memory_locks[lock_name] = ThreadLock()
               with self._memory_locks[lock_name]:
                   yield
   ```

3. Create singleton instances in `backend/utils/__init__.py`:
   ```python
   from backend.config import get_settings
   from backend.utils.queue_client import QueueClient
   from backend.utils.lock_client import LockClient

   settings = get_settings()

   queue_client = QueueClient(settings.redis_url)
   lock_client = LockClient(settings.redis_url)
   ```

**Test Criteria**:
- [ ] Works without Redis (in-memory mode)
- [ ] Works with Redis if available
- [ ] Queue operations succeed
- [ ] Locks prevent concurrent access

**Verification**:
```python
from backend.utils import queue_client, lock_client

# Test queue
queue_client.push("test", {"data": "value"})
item = queue_client.pop("test")
assert item["data"] == "value"

# Test lock
with lock_client.lock("test_lock"):
    print("Locked!")

print("Queue & Lock clients OK")
```

---

### **Step 6: SQLAlchemy Models**

**Goal**: Create all database models

**Tasks**:
1. Create `backend/models/player.py`:
   ```python
   from sqlalchemy import Column, String, Integer, DateTime, Date, ForeignKey
   from sqlalchemy.dialects.postgresql import UUID
   import uuid
   from datetime import datetime
   from backend.database import Base

   class Player(Base):
       __tablename__ = "players"

       player_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
       api_key = Column(String, unique=True, nullable=False, index=True, default=lambda: str(uuid.uuid4()))
       balance = Column(Integer, default=1000, nullable=False)
       created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
       last_login_date = Column(Date, nullable=True)
       active_round_id = Column(UUID(as_uuid=True), ForeignKey("rounds.round_id"), nullable=True)
   ```

2. Create `backend/models/prompt.py` (prompt library)

3. Create `backend/models/round.py` (unified model for prompt/copy/vote)

4. Create `backend/models/wordset.py`

5. Create `backend/models/vote.py`

6. Create `backend/models/transaction.py`

7. Create `backend/models/daily_bonus.py`

8. Create `backend/models/result_view.py`

9. Create `backend/models/player_abandoned_prompt.py`

10. Create `backend/models/__init__.py` importing all models

11. Generate initial migration:
    ```bash
    alembic revision --autogenerate -m "Initial schema"
    ```

**Test Criteria**:
- [ ] All models defined with proper relationships
- [ ] Indexes created
- [ ] Migration generates successfully
- [ ] Migration applies successfully

**Verification**:
```bash
alembic upgrade head
alembic current
```

---

### **Step 7: Pydantic Schemas**

**Goal**: Create request/response schemas with validation

**Tasks**:
1. Create `backend/schemas/player.py`:
   - `PlayerBalance` (response)
   - `ClaimDailyBonusResponse`
   - `CurrentRoundResponse`
   - `PendingResult`

2. Create `backend/schemas/round.py`:
   - `StartPromptRoundResponse`
   - `StartCopyRoundResponse`
   - `StartVoteRoundResponse`
   - `SubmitWordRequest`
   - `SubmitWordResponse`
   - `RoundAvailability`

3. Create `backend/schemas/wordset.py`:
   - `VoteRequest`
   - `VoteResponse`
   - `WordSetResults`

4. Create `backend/schemas/vote.py`

5. Include validation:
   - Word length 2-15
   - Only A-Z characters
   - Non-empty strings

**Test Criteria**:
- [ ] All schemas defined
- [ ] Validation rules work
- [ ] Serialization/deserialization works

**Verification**:
```python
from backend.schemas.round import SubmitWordRequest

# Valid
req = SubmitWordRequest(word="HELLO")
assert req.word == "HELLO"

# Invalid
try:
    req = SubmitWordRequest(word="TOO-LONG-WORD-HERE-INVALID")
    assert False, "Should have failed validation"
except:
    pass

print("Schemas OK")
```

---

### **Step 8: Word Validation Service**

**Goal**: Validate words against dictionary

**Tasks**:
1. Create `scripts/download_dictionary.py`:
   - Download Word List (NWL2020 or TWL)
   - Save to `backend/data/dictionary.txt`
   - One word per line, uppercase

2. Create `backend/services/word_validator.py`:
   ```python
   import os
   from typing import Set

   class WordValidator:
       def __init__(self):
           self.dictionary: Set[str] = self._load_dictionary()

       def _load_dictionary(self) -> Set[str]:
           path = os.path.join(os.path.dirname(__file__), "../data/dictionary.txt")
           with open(path) as f:
               return {line.strip().upper() for line in f}

       def validate(self, word: str) -> tuple[bool, str]:
           """Returns (is_valid, error_message)"""
           word = word.strip().upper()

           if len(word) < 2 or len(word) > 15:
               return False, "Word must be 2-15 characters"

           if not word.isalpha():
               return False, "Word must contain only letters A-Z"

           if word not in self.dictionary:
               return False, "Word not in dictionary"

           return True, ""

       def validate_copy(self, word: str, original: str) -> tuple[bool, str]:
           """Validate copy word (includes duplicate check)"""
           is_valid, error = self.validate(word)
           if not is_valid:
               return False, error

           if word.strip().upper() == original.strip().upper():
               return False, "Cannot submit the same word as original"

           return True, ""

   # Singleton
   _word_validator = None

   def get_word_validator() -> WordValidator:
       global _word_validator
       if _word_validator is None:
           _word_validator = WordValidator()
       return _word_validator
   ```

3. Create tests in `tests/test_word_validator.py`

**Test Criteria**:
- [ ] Dictionary loads successfully (~190k words)
- [ ] Valid words pass validation
- [ ] Invalid words fail with correct errors
- [ ] Copy validation rejects duplicates

**Verification**:
```python
from backend.services.word_validator import get_word_validator

validator = get_word_validator()

# Valid word
is_valid, error = validator.validate("HELLO")
assert is_valid

# Invalid word
is_valid, error = validator.validate("XYZQPW")
assert not is_valid

# Copy duplicate
is_valid, error = validator.validate_copy("HELLO", "HELLO")
assert not is_valid

print(f"Dictionary loaded: {len(validator.dictionary)} words")
```

---

### **Step 9: Transaction Service**

**Goal**: Atomic balance updates with transaction logging

**Tasks**:
1. Create `backend/services/transaction_service.py`:
   ```python
   from sqlalchemy.ext.asyncio import AsyncSession
   from sqlalchemy import select
   from backend.models.player import Player
   from backend.models.transaction import Transaction
   from backend.utils import lock_client
   from uuid import UUID
   import uuid

   class TransactionService:
       def __init__(self, db: AsyncSession):
           self.db = db

       async def create_transaction(
           self,
           player_id: UUID,
           amount: int,
           type: str,
           reference_id: UUID = None
       ) -> Transaction:
           """
           Create transaction and update player balance atomically.
           Uses distributed lock to prevent race conditions.
           """
           lock_name = f"player_balance:{player_id}"

           with lock_client.lock(lock_name):
               # Get current player
               result = await self.db.execute(
                   select(Player).where(Player.player_id == player_id).with_for_update()
               )
               player = result.scalar_one()

               # Check sufficient balance for negative transactions
               new_balance = player.balance + amount
               if new_balance < 0:
                   raise ValueError(f"Insufficient balance: {player.balance} + {amount} < 0")

               # Update balance
               player.balance = new_balance

               # Create transaction record
               transaction = Transaction(
                   transaction_id=uuid.uuid4(),
                   player_id=player_id,
                   amount=amount,
                   type=type,
                   reference_id=reference_id,
                   balance_after=new_balance,
               )

               self.db.add(transaction)
               await self.db.commit()
               await self.db.refresh(transaction)

               return transaction
   ```

2. Create tests in `tests/test_transaction_service.py`:
   - Test successful transaction
   - Test insufficient balance
   - Test concurrent transactions (race condition)

**Test Criteria**:
- [ ] Transaction creates successfully
- [ ] Balance updates correctly
- [ ] Insufficient balance raises error
- [ ] No race conditions

**Verification**: Run tests

---

### **Step 10: Queue Service**

**Goal**: Manage prompt and wordset queues

**Tasks**:
1. Create `backend/services/queue_service.py`:
   ```python
   from backend.utils import queue_client
   from backend.config import get_settings
   from uuid import UUID

   settings = get_settings()

   PROMPT_QUEUE = "queue:prompts"
   WORDSET_QUEUE = "queue:wordsets"

   class QueueService:
       @staticmethod
       def add_prompt_to_queue(prompt_round_id: UUID):
           """Add prompt to queue waiting for copy players"""
           queue_client.push(PROMPT_QUEUE, {"prompt_round_id": str(prompt_round_id)})

       @staticmethod
       def get_next_prompt() -> UUID | None:
           """Get next prompt from queue (FIFO)"""
           item = queue_client.pop(PROMPT_QUEUE)
           return UUID(item["prompt_round_id"]) if item else None

       @staticmethod
       def get_prompts_waiting() -> int:
           """Get count of prompts waiting for copies"""
           return queue_client.length(PROMPT_QUEUE)

       @staticmethod
       def is_copy_discount_active() -> bool:
           """Check if copy discount should be applied"""
           return QueueService.get_prompts_waiting() > settings.copy_discount_threshold

       @staticmethod
       def get_copy_cost() -> int:
           """Get current copy cost (with discount if applicable)"""
           return settings.copy_cost_discount if QueueService.is_copy_discount_active() else settings.copy_cost_normal

       @staticmethod
       def add_wordset_to_queue(wordset_id: UUID):
           """Add wordset to voting queue"""
           queue_client.push(WORDSET_QUEUE, {"wordset_id": str(wordset_id)})

       @staticmethod
       def get_wordsets_waiting() -> int:
           """Get count of wordsets waiting for votes"""
           return queue_client.length(WORDSET_QUEUE)
   ```

2. Add logic for prioritized vote queue assignment (Step 11)

3. Create tests

**Test Criteria**:
- [ ] Prompts added/retrieved correctly (FIFO)
- [ ] Discount activates at threshold
- [ ] Queue depth tracking works

**Verification**: Run tests

---

### **Step 11: Player Service**

**Goal**: Player account management and constraints

**Tasks**:
1. Create `backend/services/player_service.py`:
   ```python
   from sqlalchemy.ext.asyncio import AsyncSession
   from sqlalchemy import select, func
   from backend.models.player import Player
   from backend.models.daily_bonus import DailyBonus
   from backend.models.wordset import WordSet
   from backend.config import get_settings
   from datetime import date
   import uuid

   settings = get_settings()

   class PlayerService:
       def __init__(self, db: AsyncSession):
           self.db = db

       async def create_player(self) -> Player:
           """Create new player with starting balance and API key"""
           player = Player(
               player_id=uuid.uuid4(),
               api_key=str(uuid.uuid4()),
               balance=settings.starting_balance,
               last_login_date=date.today(),  # Set to today so no bonus on creation
           )
           self.db.add(player)
           await self.db.commit()
           await self.db.refresh(player)
           return player

       async def get_player_by_api_key(self, api_key: str) -> Player | None:
           """Get player by API key (for authentication)"""
           result = await self.db.execute(
               select(Player).where(Player.api_key == api_key)
           )
           return result.scalar_one_or_none()

       async def is_daily_bonus_available(self, player: Player) -> bool:
           """Check if daily bonus can be claimed"""
           today = date.today()

           # No bonus on creation date
           if player.created_at.date() == today:
               return False

           # Bonus available if last_login_date is before today
           return player.last_login_date is None or player.last_login_date < today

       async def claim_daily_bonus(self, player: Player, transaction_service) -> int:
           """Claim daily bonus, returns amount"""
           if not await self.is_daily_bonus_available(player):
               raise ValueError("Daily bonus not available")

           today = date.today()

           # Create bonus record
           bonus = DailyBonus(
               bonus_id=uuid.uuid4(),
               player_id=player.player_id,
               amount=settings.daily_bonus_amount,
               date=today,
           )
           self.db.add(bonus)

           # Update last_login_date
           player.last_login_date = today

           # Create transaction
           await transaction_service.create_transaction(
               player.player_id,
               settings.daily_bonus_amount,
               "daily_bonus",
               bonus.bonus_id,
           )

           await self.db.commit()
           return settings.daily_bonus_amount

       async def get_outstanding_prompts_count(self, player_id: UUID) -> int:
           """Count wordsets player created that are still open/closing"""
           result = await self.db.execute(
               select(func.count(WordSet.wordset_id))
               .where(WordSet.prompt_round.has(player_id=player_id))
               .where(WordSet.status.in_(['open', 'closing']))
           )
           return result.scalar() or 0

       async def can_start_prompt_round(self, player: Player) -> tuple[bool, str]:
           """Check if player can start prompt round"""
           # Check balance
           if player.balance < settings.prompt_cost:
               return False, "insufficient_balance"

           # Check active round
           if player.active_round_id is not None:
               return False, "already_in_round"

           # Check outstanding prompts
           count = await self.get_outstanding_prompts_count(player.player_id)
           if count >= settings.max_outstanding_prompts:
               return False, "max_outstanding_prompts"

           return True, ""
   ```

2. Create tests

**Test Criteria**:
- [ ] Player creation works
- [ ] Daily bonus logic correct (UTC dates, no bonus on creation)
- [ ] Outstanding prompts counted correctly
- [ ] Constraints enforced

**Verification**: Run tests

---

### **Step 12: Round Service - Prompt & Copy**

**Goal**: Implement prompt and copy round lifecycle

**Tasks**:
1. Create `backend/services/round_service.py` with methods:
   - `start_prompt_round(player, transaction_service, prompt_service)`
   - `submit_prompt_word(round_id, word, transaction_service, queue_service)`
   - `start_copy_round(player, transaction_service, queue_service)`
   - `submit_copy_word(round_id, word, transaction_service)`
   - `handle_prompt_timeout(round_id, transaction_service)`
   - `handle_copy_timeout(round_id, transaction_service, queue_service)`

2. Implement logic:
   - Deduct full cost immediately
   - Refund $90 on timeout
   - Random prompt assignment
   - FIFO copy assignment
   - Create wordset when 2 copies completed
   - Return abandoned copies to queue with cooldown

3. Create tests

**Test Criteria**:
- [ ] Prompt round full flow works
- [ ] Copy round full flow works
- [ ] Wordset created with 2 copies
- [ ] Timeouts handled with refunds
- [ ] Copy abandonment returns to queue
- [ ] Discount applied correctly

**Verification**: Run integration test of full flow

---

### **Step 13: Vote Service**

**Goal**: Implement voting lifecycle and timeline

**Tasks**:
1. Create `backend/services/vote_service.py`:
   - `start_vote_round(player, transaction_service)`
   - `submit_vote(player, wordset_id, word, transaction_service)`
   - `update_vote_timeline(wordset)`
   - `check_wordset_closure(wordset)`
   - `finalize_wordset(wordset, scoring_service, transaction_service)`

2. Implement vote timeline state machine:
   - Track 3rd vote (10 min window)
   - Track 5th vote (60 sec window)
   - Handle grace period
   - Trigger finalization

3. Implement immediate voter feedback ($5 if correct)

4. Create tests

**Test Criteria**:
- [ ] Vote flow works
- [ ] Immediate feedback given
- [ ] Timeline states correct
- [ ] Finalization triggered appropriately
- [ ] Self-voting prevented

**Verification**: Run tests with various vote scenarios

---

### **Step 14: Scoring Service**

**Goal**: Calculate points and distribute payouts

**Tasks**:
1. Create `backend/services/scoring_service.py`:
   ```python
   from backend.models.wordset import WordSet
   from backend.models.vote import Vote
   from sqlalchemy.ext.asyncio import AsyncSession
   from sqlalchemy import select

   class ScoringService:
       def __init__(self, db: AsyncSession):
           self.db = db

       async def calculate_payouts(self, wordset: WordSet) -> dict:
           """
           Calculate points and payouts for wordset.
           Returns: {
               "original": {"points": int, "payout": int, "player_id": UUID},
               "copy1": {"points": int, "payout": int, "player_id": UUID},
               "copy2": {"points": int, "payout": int, "player_id": UUID},
           }
           """
           # Get all votes
           result = await self.db.execute(
               select(Vote).where(Vote.wordset_id == wordset.wordset_id)
           )
           votes = result.scalars().all()

           # Count votes per word
           original_votes = sum(1 for v in votes if v.voted_word == wordset.original_word)
           copy1_votes = sum(1 for v in votes if v.voted_word == wordset.copy_word_1)
           copy2_votes = sum(1 for v in votes if v.voted_word == wordset.copy_word_2)

           # Calculate points (1 for original, 2 for copies)
           original_points = original_votes * 1
           copy1_points = copy1_votes * 2
           copy2_points = copy2_votes * 2
           total_points = original_points + copy1_points + copy2_points

           # Calculate prize pool (300 - correct votes * 5)
           correct_votes = original_votes
           prize_pool = wordset.total_pool - (correct_votes * 5)

           # Distribute proportionally (rounded down)
           if total_points == 0:
               # No votes, split evenly
               original_payout = prize_pool // 3
               copy1_payout = prize_pool // 3
               copy2_payout = prize_pool // 3
           else:
               original_payout = (original_points * prize_pool) // total_points
               copy1_payout = (copy1_points * prize_pool) // total_points
               copy2_payout = (copy2_points * prize_pool) // total_points

           return {
               "original": {
                   "points": original_points,
                   "payout": original_payout,
                   "player_id": wordset.prompt_round.player_id,
               },
               "copy1": {
                   "points": copy1_points,
                   "payout": copy1_payout,
                   "player_id": wordset.copy_round_1.player_id,
               },
               "copy2": {
                   "points": copy2_points,
                   "payout": copy2_payout,
                   "player_id": wordset.copy_round_2.player_id,
               },
           }
   ```

2. Create tests with various vote distributions

**Test Criteria**:
- [ ] Points calculated correctly (1 for original, 2 for copy)
- [ ] Prize pool calculated correctly (300 - correct votes * 5)
- [ ] Payouts distributed proportionally
- [ ] Rounding handled correctly
- [ ] Edge cases work (no votes, all same, etc.)

**Verification**: Run tests with example scenarios from docs

---

### **Step 15: Authentication Dependency**

**Goal**: Create FastAPI authentication dependency

**Tasks**:
1. Create `backend/dependencies.py`:
   ```python
   from fastapi import Header, HTTPException, Depends
   from sqlalchemy.ext.asyncio import AsyncSession
   from backend.database import get_db
   from backend.services.player_service import PlayerService
   from backend.models.player import Player

   async def get_current_player(
       x_api_key: str = Header(..., alias="X-API-Key"),
       db: AsyncSession = Depends(get_db),
   ) -> Player:
       """Get current authenticated player from API key header"""
       player_service = PlayerService(db)
       player = await player_service.get_player_by_api_key(x_api_key)

       if not player:
           raise HTTPException(status_code=401, detail="Invalid API key")

       return player
   ```

2. Create tests

**Test Criteria**:
- [ ] Valid API key returns player
- [ ] Invalid API key returns 401
- [ ] Missing header returns 422

**Verification**: Test with FastAPI test client

---

### **Step 16: API Router - Player Endpoints**

**Goal**: Implement player-related API endpoints

**Tasks**:
1. Create `backend/routers/player.py`:
   - `GET /player/balance`
   - `POST /player/claim-daily-bonus`
   - `GET /player/current-round`
   - `GET /player/pending-results`

2. Use authentication dependency

3. Implement error handling

4. Create tests in `tests/test_api_player.py`

**Test Criteria**:
- [ ] All endpoints work
- [ ] Authentication required
- [ ] Responses match schema
- [ ] Errors handled correctly

**Verification**: Run API tests

---

### **Step 17: API Router - Round Endpoints**

**Goal**: Implement round-related API endpoints

**Tasks**:
1. Create `backend/routers/rounds.py`:
   - `POST /rounds/prompt`
   - `POST /rounds/copy`
   - `POST /rounds/vote`
   - `POST /rounds/{round_id}/submit`
   - `GET /rounds/available`
   - `GET /rounds/{round_id}`

2. Implement grace period checking

3. Create tests in `tests/test_api_rounds.py`

**Test Criteria**:
- [ ] All endpoints work
- [ ] Grace period honored
- [ ] One-round-at-a-time enforced
- [ ] Errors handled correctly

**Verification**: Run API tests

---

### **Step 18: API Router - Wordset Endpoints**

**Goal**: Implement wordset/voting endpoints

**Tasks**:
1. Create `backend/routers/wordsets.py`:
   - `POST /wordsets/{wordset_id}/vote`
   - `GET /wordsets/{wordset_id}/results`

2. Implement idempotent prize collection

3. Implement word randomization per voter

4. Create tests in `tests/test_api_wordsets.py`

**Test Criteria**:
- [ ] Voting works
- [ ] Results viewable
- [ ] Prize collected once only
- [ ] Word order randomized
- [ ] Only contributors can view results

**Verification**: Run API tests

---

### **Step 19: Health Check Endpoint**

**Goal**: Add health check for monitoring

**Tasks**:
1. Create `backend/routers/health.py`:
   ```python
   from fastapi import APIRouter
   from backend.database import engine
   from backend.utils import queue_client

   router = APIRouter()

   @router.get("/health")
   async def health_check():
       # Check database
       try:
           async with engine.begin() as conn:
               await conn.execute("SELECT 1")
           db_status = "connected"
       except:
           return {"status": "error", "detail": "Database connection failed"}, 503

       # Check queue backend
       queue_status = queue_client.backend

       return {
           "status": "ok",
           "database": db_status,
           "redis": queue_status,
       }
   ```

2. No authentication required

3. Create test

**Test Criteria**:
- [ ] Returns 200 when healthy
- [ ] Returns 503 when DB down
- [ ] Shows Redis status

**Verification**: `curl http://localhost:8000/health`

---

### **Step 20: Main Application**

**Goal**: Initialize FastAPI app and register routers

**Tasks**:
1. Create `backend/main.py`:
   ```python
   from fastapi import FastAPI
   from fastapi.middleware.cors import CORSMiddleware
   from backend.routers import player, rounds, wordsets, health
   from backend.config import get_settings

   settings = get_settings()

   app = FastAPI(
       title="WordPool API",
       description="Phase 1 MVP",
       version="1.0.0",
   )

   # CORS
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["*"],  # Configure for production
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )

   # Register routers
   app.include_router(health.router, tags=["health"])
   app.include_router(player.router, prefix="/player", tags=["player"])
   app.include_router(rounds.router, prefix="/rounds", tags=["rounds"])
   app.include_router(wordsets.router, prefix="/wordsets", tags=["wordsets"])

   @app.get("/")
   async def root():
       return {"message": "WordPool API - Phase 1 MVP"}
   ```

2. Test app starts

**Test Criteria**:
- [ ] App starts without errors
- [ ] All routes registered
- [ ] Docs available at `/docs`

**Verification**:
```bash
uvicorn backend.main:app --reload
curl http://localhost:8000
curl http://localhost:8000/docs
```

---

### **Step 21: Seed Data**

**Goal**: Populate database with initial data

**Tasks**:
1. Create `scripts/seed_prompts.py`:
   - Load prompts from `PROMPT_LIBRARY.md`
   - Insert into database
   - ~100 prompts across all categories

2. Create a few test players

3. Create script runner:
   ```bash
   python scripts/seed_prompts.py
   ```

**Test Criteria**:
- [ ] Prompts loaded successfully
- [ ] Can query random prompts
- [ ] Test players created

**Verification**:
```python
from backend.database import AsyncSessionLocal
from backend.models.prompt import Prompt
from sqlalchemy import select

async def check():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Prompt))
        prompts = result.scalars().all()
        print(f"Loaded {len(prompts)} prompts")

import asyncio
asyncio.run(check())
```

---

### **Step 22: Integration Tests**

**Goal**: End-to-end testing of complete game flow

**Tasks**:
1. Create `tests/test_integration.py`:
   - Test complete flow: prompt → copy → copy → votes → results
   - Test queue discount activation
   - Test one-round-at-a-time enforcement
   - Test daily bonus claiming
   - Test grace period handling
   - Test abandoned round handling

2. Use pytest fixtures for setup/teardown

3. Test both with and without Redis

**Test Criteria**:
- [ ] Full game flow works end-to-end
- [ ] All constraints enforced
- [ ] Timings and costs correct
- [ ] Payouts calculated correctly

**Verification**: Run full test suite

---

### **Step 23: Documentation**

**Goal**: Document the API and implementation

**Tasks**:
1. Create `docs/API.md`:
   - Document all endpoints
   - Include request/response examples
   - Document error codes
   - Include authentication info
   - Add curl examples

2. Update `docs/ARCHITECTURE.md`:
   - Add backend file structure section
   - Document design decisions made
   - Add notes on Redis fallback

3. Create `docs/MVP_SUMMARY.md`:
   - Summarize what was implemented
   - List all features included
   - Document what was deferred to Phase 2
   - Include deployment instructions
   - Add testing instructions

**Test Criteria**:
- [ ] API.md comprehensive
- [ ] ARCHITECTURE.md updated
- [ ] MVP_SUMMARY.md complete

**Verification**: Review documentation for completeness

---

## Testing Strategy

### Unit Tests
- Each service tested in isolation
- Mock database and queue interactions
- Test edge cases and error conditions

### Integration Tests
- Test API endpoints with real database
- Test service interactions
- Test full game flows

### Test Coverage Goals
- Services: >90%
- Routers: >80%
- Overall: >80%

### Test Execution
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=backend --cov-report=html

# Run specific test file
pytest tests/test_player_service.py -v

# Run integration tests only
pytest tests/test_integration.py -v
```

---

## Deployment Checklist

### Local Development
- [ ] Clone repository
- [ ] Create `.env` from `.env.example`
- [ ] `pip install -r requirements.txt`
- [ ] `alembic upgrade head`
- [ ] `python scripts/seed_prompts.py`
- [ ] `uvicorn backend.main:app --reload`

### Docker Local
- [ ] `docker-compose up -d`
- [ ] Access at `http://localhost:8000`

### Heroku Deployment
- [ ] Create Heroku app
- [ ] Add PostgreSQL addon
- [ ] Add Redis addon (optional)
- [ ] Set environment variables
- [ ] Push code: `git push heroku main`
- [ ] Run migrations: `heroku run alembic upgrade head`
- [ ] Seed data: `heroku run python scripts/seed_prompts.py`

---

## Success Criteria

### Phase 1 MVP is complete when:
1. ✅ All 23 steps completed
2. ✅ All tests passing (>80% coverage)
3. ✅ Full game flow works end-to-end
4. ✅ Deployed to Heroku successfully
5. ✅ API documentation complete
6. ✅ Can play full game via API calls
7. ✅ No critical bugs
8. ✅ Performance acceptable (<500ms p95 response time)

---

## Next Steps (Phase 2+)

After MVP completion:
1. Frontend development (React/Vue/Svelte)
2. AI backup for copies/votes
3. Enhanced player statistics
4. JWT authentication
5. Advanced monitoring/analytics
6. Performance optimization
7. Additional game features

---

## Notes

- **Development First**: Build everything to work without Redis first, then test Redis integration
- **Test as You Go**: Write tests immediately after implementing each service
- **Commit Often**: Commit after each step completion
- **Document Decisions**: Update docs when making design decisions
- **Ask When Stuck**: Clarify ambiguities before implementing
