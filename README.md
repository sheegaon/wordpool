# Complete Game Specification: Wordpool

## Game Overview
Wordpool is a multiplayer word association game with three round types: Prompt, Copy, and Vote. Players compete to match words with prompts or identify original vs. copied words, with monetary stakes and payouts.

---

## Round Types

### 1. Prompt Round
- **Cost**: \$100 (full amount deducted immediately, \$90 refunded on timeout)
- **Process**: Player receives a randomly-assigned prompt (e.g., "my deepest desire is to be (a)") and submits a single word
- **Word Requirements**:
  - Must be in OWL2 Word List
  - 2-15 letters
  - No proper nouns, abbreviations, or capitalized words
- **Timing**: 60-second submission window
- **Abandonment**: If expired, round cancelled, forfeit \$10 entry fee (\$90 refunded), prompt removed from queue
- **Queue**: Prompt enters queue waiting for 2 copy players
  - AI will provide necessary copies after 10 minutes of inactivity (Phase 2+)

### 2. Copy Round
- **Cost**: \$100 or \$90 (full amount deducted immediately, \$90 refunded on timeout)
- **Dynamic Pricing**: When prompts waiting for copies exceeds 10, copy rounds cost \$90 total (system contributes \$10 to maintain \$300 prize pool per wordset)
- **Process**: Player receives ONLY the word submitted by a prompt player (without the original prompt) and must submit a similar/related word
- **Word Requirements**: Same as Prompt Round, plus no duplicate of the original word
- **Duplicate Handling**: If submitted word matches the original, submission is rejected and player must choose a different word (timer continues)
- **Timing**: 60-second submission window
- **Abandonment**: If expired, round cancelled, forfeit \$10 entry fee (\$90 refunded). Associated prompt_round returned to queue for another player to attempt (same player blocked from retry for 24 hours).
- **Queue**: Once 2 different copy players successfully submit, the word set (1 original + 2 copies) moves to voting queue

### 3. Vote Round
- **Cost**: \$1 (deducted immediately)
- **Process**: Player sees the original prompt and three words (1 original + 2 copies in randomized order per voter) and votes for which they believe is the original
- **Timing**: 15-second hard limit (frontend enforces, backend has 5-second grace period)
- **Abandonment**: No vote = forfeit \$1
- **Voting Pool**: 
  - Minimum 3 votes before finalization (AI will provide necessary votes to get to 3 votes after 10 minutes of inactivity)
  - Maximum 20 votes per word set
  - After 3rd vote received: word set remains open for 10 minutes OR until 5th vote received, whichever comes first
  - After 5th vote received: accept additional voters for 60 seconds only
  - After 20th vote OR (5+ votes AND 80 seconds elapsed since 5th vote), word set closes
- **Restrictions**: The 3 contributors (1 prompt + 2 copy players) cannot vote on their own word set (filtered at assignment). Voters can vote once per word set.

---

## Player Constraints

### One Round At A Time
- A player can only have one active round (prompt, copy, or vote) at any given time
- Must submit or abandon current round before starting a new one
- Viewing results does not count as an "active" round
- This prevents exploitation and reduces UI complexity

### Ten Outstanding Prompts
- A player can have up to 10 outstanding prompts where the associated wordsets have not been finalized (status 'open' or 'closing')
- Viewing results does not affect this count
- Enforced when calling POST /rounds/prompt

---

## Scoring & Payouts

### Prize Pool Formation
- **Contributions**: \$100 each from 3 players = \$300 total pool (system contributes \$10 when copy discount active)
- **Vote Payments Deducted**: \$5 per correct vote (max \$100 for 20 votes)
- **Rake**: Vote entry fees (\$1 per voter) are rake and don't enter prize pool
- **Remaining Prize Pool**: \$300 - (correct votes × \$5) = distributed to contributors proportionally to points earned, rounded down to nearest integer and remainder is raked

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
- New players begin with **$1000**

### Daily Login Bonus
- **$100** credited once per UTC calendar date, excluding player creation date
- First bonus available the day after account creation
- Automatically tracks via `last_login_date` field

### Transaction Costs
- Prompt round: -\$100 (deducted immediately, \$90 refunded on timeout)
- Copy round: -\$100 or -\$90 (deducted immediately, \$90 or \$81 refunded on timeout)
- Vote round: -\$1 (deducted immediately)

### Revenue Opportunities
- Correct votes: +$4 net (+$5 gross - \$1 entry)
- Prize pool earnings: Variable based on performance and votes received
- Daily login bonus: +$100
- *Future Ideas:* Correct voter bonus upon 5 correct votes in a row: +$10

---

## Game Flow & Matchmaking

### Player Choice
At any time (if not already in an active round), players can choose to:
1. **Start Prompt Round** - Only if player has enough balance and fewer than 10 outstanding prompts (wordsets in 'open' or 'closing' status)
2. **Start Copy Round** - Only if prompts are waiting for copies in queue
3. **Start Vote Round** - Only if complete word sets (1 original + 2 copies) are waiting for votes (excluding own wordsets)

### Queue System
- **Prompt Queue**: Submitted prompts waiting for copy players (FIFO)
- **Copy Assignment**: FIFO from prompt queue when player calls POST /rounds/copy
- **Copy Queue Discount**: When prompts_waiting > 10, copy rounds cost \$90 (system contributes \$10 per wordset)
- **Vote Queue**: Complete word sets waiting for voters
- **Vote Assignment Priority**:
  1. Wordsets with ≥5 votes (FIFO by 5th vote time)
  2. Wordsets with 3-4 votes (FIFO by 3rd vote time)
  3. Wordsets with <3 votes (random selection)

### Anti-Gaming Measures
- Contributors cannot vote on their own word sets (filtered at assignment)
- Word order randomized per-voter in voting display (not stored)
- Rate limit: Maximum 10 outstanding prompts per player (wordsets in 'open'/'closing' status)
- One vote per word set per player (enforced via unique composite index), no vote changes allowed
- Grace period: 5 seconds past timer expiry (backend only, not shown to users)
- API rate limiting: Prevent abuse/brute force attempts

---

## Timing Rules

### Submission Windows
- **Prompt/Copy submission**: 60 seconds (frontend enforces, backend has 5-second grace period)
- **Voting**: 15 seconds (frontend enforces, backend has 5-second grace period)

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
- **Grace period**: Voters who called POST /rounds/vote within the 60-second window get their full 15 seconds to vote, even if this extends past 60 seconds

### Abandonment Handling
- **Prompt abandonment**: Round cancelled, \$10 penalty forfeited (\$90 refunded), prompt removed from queue
- **Copy abandonment**: Round cancelled, \$10 penalty forfeited (\$90 refunded), prompt_round returned to queue for other players (original player blocked 24h)
- **Vote abandonment**: Player loses \$1, vote not counted
- **Implementation**: Backend timeout cleanup job processes expired rounds periodically