# Complete Game Specification: Wordpool

## Game Overview
Wordpool is a multiplayer word association game with three round types: Prompt, Copy, and Vote. Players compete to match words with prompts or identify original vs. copied words, with monetary stakes and payouts.

---

## Round Types

### 1. Prompt Round
- **Cost**: $100 (10% immediately, remainder deducted upon submission)
- **Process**: Player receives a prompt (e.g., "my deepest desire is to be (a)") and submits a single word
- **Word Requirements**:
  - Must be in NASPA Word List (North American Scrabble dictionary)
  - 2-15 letters
  - No proper nouns, abbreviations, or capitalized words
- **Timing**: 60-second submission window
- **Abandonment**: If expired, round cancelled and forfeit initial 10%
- **Queue**: Prompt enters queue waiting for 2 copy players
  - AI will provide necessary copies after 10 minutes of inactivity

### 2. Copy Round
- **Cost**: $100 (or $90 when queue discount active) (10% immediately, remainder deducted upon submission)
- **Dynamic Pricing**: When prompts waiting for copies exceeds 10, copy rounds cost $90 total (system contributes $10 to maintain $300 prize pool)
- **Process**: Player receives ONLY the word submitted by a prompt player (without the original prompt) and must submit a similar/related word
- **Word Requirements**: Same as Prompt Round, plus no duplicate of the original word
- **Duplicate Handling**: If submitted word matches the original, submission is rejected and player must choose a different word (timer continues)
- **Timing**: 60-second submission window
- **Abandonment**: If expired, round cancelled and forfeit initial 10%. Copy round is returned to queue for another player to attempt.
- **Queue**: Once 2 different copy players successfully submit, the word set (1 original + 2 copies) moves to voting queue

### 3. Vote Round
- **Cost**: $1
- **Process**: Player sees the original prompt and three words (1 original + 2 copies in random order) and votes for which they believe is the original
- **Timing**: 15-second hard limit (frontend enforces, backend has 5-second grace period)
- **Abandonment**: No vote = forfeit $1
- **Voting Pool**: 
  - Minimum 3 votes before finalization (AI will provide necessary votes to get to 3 votes after 10 minutes of inactivity)
  - Maximum 20 votes per word set
  - After 3rd vote received: word set remains open for 10 minutes OR until 5th vote received, whichever comes first
  - After 5th vote received: accept additional voters for 60 seconds only
  - After 20th vote OR (5+ votes AND 80 seconds elapsed since 5th vote), word set closes
- **Restrictions**: The 3 contributors (1 prompt + 2 copy players) cannot vote on their own word set. Voters can vote once per word set.

---

## Player Constraints

### One Round At A Time
- A player can only have one active round (prompt, copy, or vote) at any given time
- Must submit or abandon current round before starting a new one
- Viewing results does not count as an "active" round
- This prevents exploitation and reduces UI complexity

### Ten Outstanding Prompts
- A player can have up to 10 outstanding prompts which have not been voted on and finalized

---

## Scoring & Payouts

### Prize Pool Formation
- **Contributions**: $100 each from 3 players = $300 total pool (system contributes $10 when copy discount active)
- **Vote Payments Deducted**: $5 per correct vote (max $100 for 20 votes)
- **Rake**: Vote entry fees ($1 per voter) are rake and don't enter prize pool
- **Remaining Prize Pool**: $300 - (correct votes × $5) = distributed to contributors proportionally to points earned, rounded down to nearest integer and remainder is raked

### Points Distribution
- **Vote for Original**: 1 point to original (prompt) player
- **Vote for Copy**: 2 points to that copy player
- **Example**: 10 votes total
  - 4 votes for original = 4 points to original player
  - 3 votes for copy A = 6 points to copy A player
  - 3 votes for copy B = 6 points to copy B player
  - Total: 16 points

### Payout Calculation
- Prize pool split proportionally by points earned, rounded down to nearest $1 (remainder is raked)
- **Example** (continuing above with $250 remaining pool after $50 in vote payments):
  - Original player: 4/16 × $250 = $62
  - Copy A player: 6/16 × $250 = $93
  - Copy B player: 6/16 × $250 = $93

### Voter Payouts
- **Correct vote**: $5 gross ($4 net after $1 entry fee)
- **Incorrect vote**: $0 (lose $1 entry fee)

---

## Player Economics

### Starting Balance
- New players begin with **$1000**

### Daily Login Bonus
- **$100** credited once per 24-hour period from player creation time, excluding on player creation date

### Transaction Costs
- Prompt round: -$100 (10% deducted immediately, remainder deducted upon submission)
- Copy round: -$100 (or -$90 when discount active) (10% deducted immediately, remainder deducted upon submission)
- Vote round: -$1

### Revenue Opportunities
- Correct votes: +$4 net (+$5 gross - $1 entry)
- Prize pool earnings: Variable based on performance and votes received
- Daily login bonus: +$100
- *Future Ideas:* Correct voter bonus upon 5 correct votes in a row: +$10

---

## Game Flow & Matchmaking

### Player Choice
At any time (if not already in an active round), players can choose to:
1. **Start Prompt Round** - Only if players has enough balance and fewer than 10 outstanding completed prompts
2. **Start Copy Round** - Only if prompts are waiting for copies
3. **Start Vote Round** - Only if complete word sets (1 original + 2 copies) are waiting for votes

### Queue System
- **Prompt Queue**: Prompts waiting for copy players
- **Copy Assignment**: FIFO from copy player queue to waiting prompts
- **Copy Queue Discount**: When prompts_waiting > 10, copy rounds cost $90 (display prominently)
- **Vote Queue**: Complete word sets waiting for voters
- **Vote Assignment**: FIFO over word sets with >= 5 votes, random assignment if all word sets have < 5 votes

### Anti-Gaming Measures
- Contributors cannot vote on their own word sets
- Word order randomized in voting display
- Rate limit: Maximum 10 active prompts per player simultaneously (across all time, not concurrent due to one-at-a-time rule)
- One vote per word set per player, no vote changes allowed

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
- **After 5th vote received**: Accept additional voters for 60 seconds
- **Closure**: After 20th vote OR (5+ votes AND 60 seconds elapsed since 5th vote received)
- **Grace period**: Voters who call the vote endpoint within the 60-second window get their full 15 seconds to vote, even if this extends slightly past 60 seconds

### Abandonment Handling
- **Prompt abandonment**: Round cancelled, $10 penalty forfeited
- **Copy abandonment**: Round cancelled, 10% penalty forfeited. Copy round returned to queue for other copy players.
- **Vote abandonment**: Player loses $1, vote not counted