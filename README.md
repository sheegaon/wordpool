# WordPool

A multiplayer phrase association game with monetary stakes. Players respond to prompts with brief phrases, copy them, and vote to identify originals.

## 🎮 Game Overview

WordPool is a three-phase game where players:
1. **Prompt** - Submit a phrase for a creative prompt (\$100)
2. **Copy** - Submit a similar phrase without seeing the prompt (\$100 or \$90)
3. **Vote** - Identify the original phrase from three options (\$1)

Winners split a prize pool based on vote performance. See full game rules below.

## 🚀 Quick Start

### Backend (Production Ready)

```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Seed prompts
python3 scripts/seed_prompts.py

# Start server
uvicorn backend.main:app --reload
```

Server runs at **http://localhost:8000**
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

### Frontend (MVP Complete)

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend runs at **http://localhost:5173**
- See [frontend/README.md](frontend/README.md) for detailed documentation

## 🧑‍🚀 Accounts & Login

- New players click **Create New Account** to receive a themed username and API key.
- The username is all you need to return later—enter it on the landing page and the backend will re-issue your API key.
- Keep the API key secret if you plan to call the API directly; the web client handles it automatically.

## 📚 Documentation

**For Developers:**
- **[API.md](docs/API.md)** - Complete REST API reference with TypeScript types
- **[FRONTEND_PLAN.md](docs/FRONTEND_PLAN.md)** - Frontend implementation guide (NEW)
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - System architecture and backend logic
- **[DATA_MODELS.md](docs/DATA_MODELS.md)** - Database schema reference
- **[MVP_SUMMARY.md](docs/MVP_SUMMARY.md)** - Project status and completion checklist

**For Game Design:**
- **[README.md](README.md)** - This file (complete game rules)
- **[PROJECT_PLAN.md](docs/PROJECT_PLAN)** - Implementation phases and roadmap
- **[PROMPT_LIBRARY.md](docs/PROMPT_LIBRARY.md)** - Game prompts collection

## ⚡ Features

**✅ Phase 1 MVP Complete (100%)**

*Backend:*
- Pseudonymous player accounts with auto-generated usernames
- API key authentication (surfaced via username login)
- Three round types (Prompt, Copy, Vote)
- Queue management with dynamic pricing
- NASPA dictionary validation (191k words)
- Proportional prize distribution
- Daily login bonuses
- Transaction audit trail
- 15+ REST API endpoints
- 88% test coverage

*Frontend:*
- React 18 + TypeScript with Vite 5 (stable, production-ready)
- Responsive UI with Tailwind CSS 3
- Real-time countdown timers
- Dashboard with balance & round selection
- All three round types implemented
- Results viewing with vote breakdown
- Automatic state polling with request cancellation
- Error handling & notifications
- 22% smaller bundle size vs bleeding-edge versions

**🔜 Phase 2 (Planned)**
- Transaction history endpoint
- Enhanced statistics
- JWT authentication
- Admin API for testing

**🎯 Phase 3+ (Future)**
- AI backup players
- Real-time WebSocket updates
- Leaderboards & achievements
- Social features

## 🛠️ Tech Stack

**Backend:**
- FastAPI (async Python web framework)
- SQLAlchemy (async ORM)
- PostgreSQL / SQLite
- Redis (with in-memory fallback)
- Alembic (migrations)
- Pydantic (validation)

**Deployment:**
- Docker / docker-compose
- Heroku ready (heroku.yml)
- Environment-based configuration

## 🧪 Testing

### Unit Tests (Backend Logic)
```bash
# Run backend unit tests
pytest tests/test_game_flow.py tests/test_api_player.py tests/test_phrase_validator.py -v

# Current status: 15/17 passing (88%)
# Known issues: 2 tests debugging timezone edge cases
```

### Integration Tests (Localhost API)
**NEW:** Comprehensive integration test suite for testing the live API

```bash
# Start backend server first
uvicorn backend.main:app --reload

# Run all integration tests
./run_localhost_tests.sh all
# OR
python run_localhost_tests.py all

# Run specific test suites
./run_localhost_tests.sh integration  # Core API tests
./run_localhost_tests.sh scenarios    # Game flow scenarios
./run_localhost_tests.sh stress       # Load & performance tests
./run_localhost_tests.sh quick        # Fast subset (integration + scenarios)
```

**Test Coverage:**
- ✅ Player creation & authentication (API keys, rotation)
- ✅ Balance tracking & daily bonuses
- ✅ Prompt/Copy/Vote round lifecycles
- ✅ Complete game flows (end-to-end)
- ✅ Queue dynamics & copy discounts
- ✅ Error handling & validation
- ✅ Concurrent operations (multi-player)
- ✅ Load testing (100+ players)
- ✅ Rate limiting behavior

**Documentation:** See [tests/README_LOCALHOST_TESTS.md](tests/README_LOCALHOST_TESTS.md) for detailed information

---

# Complete Game Rules

---

## Round Types

### 1. Prompt Round
- **Cost**: \$100 (full amount deducted immediately, \$90 refunded on timeout)
- **Process**: Player receives a randomly-assigned prompt (e.g., "my deepest desire is to be (a)") and submits a short phrase
- **Phrase Requirements**:
  - 1-5 words (2-100 characters total)
  - Letters A-Z and spaces only (case insensitive)
  - Each word must exist in the NASPA dictionary (except common connectors like “a”, “an”, “the”, “I”)
- **Timing**: 3-minute (180-second) submission window
- **Abandonment**: If expired, round cancelled, forfeit \$10 entry fee (\$90 refunded), prompt removed from queue
- **Queue**: Prompt enters queue waiting for 2 copy players
  - AI will provide necessary copies after 10 minutes of inactivity (Phase 3+)

### 2. Copy Round
- **Cost**: \$100 or \$90 (full amount deducted immediately, \$90 refunded on timeout)
- **Dynamic Pricing**: When prompts waiting for copies exceeds 10, copy rounds cost \$90 total (system contributes \$10 to maintain \$300 prize pool per phraseset)
- **Process**: Player receives ONLY the phrase submitted by a prompt player (without the original prompt) and must submit a similar/related phrase
- **Phrase Requirements**: Same as Prompt Round, plus no duplicate of the original phrase
- **Duplicate Handling**: If submitted phrase matches the original, submission is rejected and the player must choose a different phrase (timer continues)
- **Timing**: 3-minute (180-second) submission window
- **Abandonment**: If expired, round cancelled, forfeit \$10 entry fee (\$90 or \$81 refunded). Associated prompt_round returned to queue for another player to attempt (same player blocked from retry for 24 hours).
- **Queue**: Once 2 different copy players successfully submit, the phrase set (1 original + 2 copies) moves to voting queue

### 3. Vote Round
- **Cost**: \$1 (deducted immediately)
- **Process**: Player sees the original prompt and three phrases (1 original + 2 copies in randomized order per voter) and votes for which they believe is the original
- **Timing**: 60-second hard limit (frontend enforces, backend has 5-second grace period)
- **Abandonment**: No vote = forfeit \$1
- **Voting Pool**:
  - Minimum 3 votes before finalization (AI will provide necessary votes after 10 minutes of inactivity - Phase 3+)
  - Maximum 20 votes per phrase set
  - After 3rd vote received: phrase set remains open for 10 minutes OR until 5th vote received, whichever comes first
  - After 5th vote received: accept additional voters for 60 seconds only
  - After 20th vote OR (5+ votes AND 60 seconds elapsed since 5th vote), phrase set closes
- **Restrictions**: The 3 contributors (1 prompt + 2 copy players) cannot vote on their own phrase set (filtered at assignment). Voters can vote once per phrase set.

---

## Player Constraints

### One Round At A Time
- A player can only have one active round (prompt, copy, or vote) at any given time
- Must submit or abandon current round before starting a new one
- Viewing results does not count as an "active" round
- This prevents exploitation and reduces UI complexity

### Ten Outstanding Prompts
- A player can have up to 10 outstanding prompts where the associated phrasesets have not been finalized (status 'open' or 'closing')
- Viewing results does not affect this count
- Enforced when calling POST /rounds/prompt

---

## Scoring & Payouts

### Prize Pool Formation
- **Contributions**: \$100 each from 3 players = \$300 total pool (system contributes \$10 when copy discount active)
- **Vote Payments Deducted**: \$5 per correct vote (max \$100 for 20 votes)
- **Rake**: Vote entry fees (\$1 per voter) are rake and don't enter prize pool
- **Remaining Prize Pool**: \$300 - (correct votes × \$5) = distributed to contributors proportionally to points earned, rounded down to nearest \$1 and remainder is raked

### Points Distribution
- **Vote for Original**: 1 point to original (prompt) player
- **Vote for Copy**: 2 points to that copy player
- **Example**: 10 votes total
  - 4 votes for original = 4 points to original player
  - 3 votes for copy A = 6 points to copy A player
  - 3 votes for copy B = 6 points to copy B player
  - Total: 16 points

### Payout Calculation
- Prize pool split proportionally by points earned, rounded down to nearest \$1 (remainder is raked)
- **Example** (continuing above with \$250 remaining pool after \$50 in vote payments):
  - Original player: 4/16 × \$250 = \$62
  - Copy A player: 6/16 × \$250 = \$93
  - Copy B player: 6/16 × \$250 = \$93

### Voter Payouts
- **Correct vote**: \$5 gross (\$4 net after \$1 entry fee)
- **Incorrect vote**: \$0 (lose \$1 entry fee)

---

## Player Economics

### Starting Balance
- New players begin with **\$1000**

### Daily Login Bonus
- **\$100** credited once per UTC calendar date, excluding player creation date
- First bonus available the day after account creation
- Automatically tracks via `last_login_date` field

### Transaction Costs
- Prompt round: -\$100 (deducted immediately, \$90 refunded on timeout)
- Copy round: -\$100 or -\$90 (deducted immediately, \$90 or \$81 refunded on timeout)
- Vote round: -\$1 (deducted immediately)

### Revenue Opportunities
- Correct votes: +\$4 net (+\$5 gross - \$1 entry)
- Prize pool earnings: Variable based on performance and votes received
- Daily login bonus: +\$100
- *Future Ideas:* Correct voter bonus upon 5 correct votes in a row: +\$10

---

## Game Flow & Matchmaking

### Player Choice
At any time (if not already in an active round), players can choose to:
1. **Start Prompt Round** - Only if player has enough balance and fewer than 10 outstanding prompts (phrasesets in 'open' or 'closing' status)
2. **Start Copy Round** - Only if prompts are waiting for copies in queue
3. **Start Vote Round** - Only if complete phrase sets (1 original + 2 copies) are waiting for votes (excluding own phrasesets)

### Queue System
- **Prompt Queue**: Submitted prompts waiting for copy players (FIFO)
- **Copy Assignment**: FIFO from prompt queue when player calls POST /rounds/copy
- **Copy Queue Discount**: When prompts_waiting > 10, copy rounds cost \$90 (system contributes \$10 per phraseset)
- **Vote Queue**: Complete phrase sets waiting for voters
- **Vote Assignment Priority**:
  1. Phrasesets with ≥5 votes (FIFO by 5th vote time)
  2. Phrasesets with 3-4 votes (FIFO by 3rd vote time)
  3. Phrasesets with <3 votes (random selection)

### Anti-Gaming Measures
- Contributors cannot vote on their own phrase sets (filtered at assignment)
- Phrase order randomized per voter in the voting display (not stored)
- Rate limit: Maximum 10 outstanding prompts per player (phrasesets in 'open'/'closing' status)
- One vote per phrase set per player (enforced via unique composite index), no vote changes allowed
- Grace period: 5 seconds past timer expiry (backend only, not shown to users)
- API rate limiting: Prevent abuse/brute force attempts

---

## Timing Rules

### Submission Windows
- **Prompt/Copy submission**: 3 minutes (180 seconds) (frontend enforces, backend has 5-second grace period)
- **Voting**: 60 seconds (frontend enforces, backend has 5-second grace period)

### Grace Period Implementation
- **Frontend**: Disables submit button and shows "Time's up" message when timer reaches 0
- **Backend**: Accepts submissions up to 5 seconds after expires_at timestamp
- **Purpose**: Accounts for network latency and ensures fair play

### Voting Finalization Timeline
- **After 3rd vote**: Word set remains open for the earlier of:
  - 10 minutes, OR
  - Until 5th vote is received
- **After 5th vote received**: Accept new voters (POST /rounds/vote) for 60 seconds
- **Closure**: After 20th vote OR (60 seconds elapsed since 5th vote received + all pending voters submitted)
- **Grace period**: Voters who called POST /rounds/vote within the 60-second window get their full 60 seconds to vote, even if this extends past 60 seconds

### Abandonment Handling
- **Prompt abandonment**: Round cancelled, \$10 penalty forfeited (\$90 refunded), prompt removed from queue
- **Copy abandonment**: Round cancelled, \$10 or \$9 penalty forfeited (rest refunded), prompt_round returned to queue for other players (original player blocked 24h)
- **Vote abandonment**: Player loses \$1, vote not counted
- **Implementation**: Backend timeout cleanup job processes expired rounds periodically
