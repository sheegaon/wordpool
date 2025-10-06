# Technical Architecture and Overview

## Results & UI

### Results Display
- **Status Area**: Shows all active and completed rounds, split by type (prompt, copy, vote)
- **Visual Cue**: Small notification when results are ready
- **Deferred Collection**: Prizes not collected until player views results
- **Results Content**:
  - For contributors: All votes shown, reveal which word was original, points earned, payout amount
  - For voters: Correct answer revealed immediately after vote submission, $5 credited if correct. Show voters vote tally thus far and add to status area so players can check back to see final vote tally.

### Result Timing
- **For Voters**: Immediate feedback after vote submission (correct/incorrect, original word revealed, $5 gross/$4 net if correct)
- **For Contributors**: Results available immediately after voting period closes
- **Prize Collection**: Requires viewing results screen to credit account

---

## Frontend/Backend Technical Architecture

### Frontend Responsibilities
- UI for all three round types (prompt input, copy input, voting selection)
- Countdown timer display (calculated from expires_at, purely client-side)
- Player dashboard (balance, active rounds, history, daily bonus status)
- Round type selection with availability indicators
- Queue depth display (prompts waiting, wordsets waiting)
- Copy discount notification when active
- Status bar with result notifications
- Results viewing screens
- Basic input validation (length, non-empty)
- Polling for round availability and results (idle state only)
- Timer enforcement: disable submit after timer expires (backend has grace period)

### Backend Responsibilities
- Player accounts and wallet management
- Daily login bonus tracking and distribution
- Word validation against NASPA Word List
- Duplicate detection (copy vs. original)
- Queue management (prompt, copy, vote queues)
- Copy discount activation when prompts_waiting > 10
- Matchmaking logic
- Round lifecycle state machine
- Timer enforcement with 5-second grace period
- Vote counting and finalization triggers
- Voting timeline management (3-vote 10-min window, 5-vote 60-sec window)
- Scoring calculations
- Payout distribution (including system contribution for discounted copies)
- Transaction logging
- Anti-cheat enforcement (self-voting prevention, rate limits)
- Results preparation and storage
- One-round-at-a-time constraint enforcement

### Communication Protocol
- **REST API only**
- Backend maintains all game state
- Frontend is stateless presentation layer

---

## REST API Endpoints

### Player Actions

**POST /rounds/prompt** - Start prompt round (-$10)
- Body: `{prompt_id: string}` (optional, for selecting specific prompt)
- Returns: `{round_id, prompt_text, expires_at}` 
- Errors: `{error: "already_in_round" | "insufficient_balance"}`

**POST /rounds/copy** - Request copy round (-$10 or -$9)
- Returns: `{round_id, original_word, expires_at, cost: 9|10, discount_active: boolean}` 
- Errors: `{error: "no_prompts_available" | "already_in_round" | "insufficient_balance"}`

**POST /rounds/vote** - Request vote round (-$1)
- Returns: `{wordset_id, prompt_text, words: [word1, word2, word3], expires_at}` 
- Errors: `{error: "no_wordsets_available" | "already_in_round" | "insufficient_balance"}`

**POST /rounds/{round_id}/submit** - Submit word for prompt/copy (-$90 or -$81)
- Body: `{word: string}`
- Returns: `{success: true}` 
- Errors: `{error: "invalid_word" | "duplicate" | "expired" | "player_not_in_round" | "not_found"}`
- Note: Backend accepts submissions up to 5 seconds past expires_at

**POST /wordsets/{wordset_id}/vote** - Submit vote
- Body: `{word: string}`
- Returns: `{correct: boolean, payout, original_word: string}` 
- Errors: `{error: "expired" | "already_voted" | "not_found"}`
- Note: Backend accepts votes up to 5 seconds past expires_at

### State Queries

**GET /player/balance** - Current balance and daily bonus status
- Returns: `{balance: number, starting_balance: 1000, daily_bonus_available: boolean, daily_bonus_amount: 100, last_login: timestamp}`

**POST /player/claim-daily-bonus** - Claim daily login bonus
- Returns: `{success: true, amount: 100, new_balance: number}` 
- Errors: `{error: "already_claimed_today"}`

**GET /player/current-round** - Get active round if any
- Returns: `{round_id, round_type: "prompt"|"copy"|"vote", state: object, expires_at}` or `{current_round: null}`
- Used on app load/reconnect to resume active round

**GET /rounds/available** - Which round types can be played now
- Returns: 
```json
{
  "can_prompt": boolean,
  "can_copy": boolean,
  "can_vote": boolean,
  "prompts_waiting": number,
  "wordsets_waiting": number,
  "copy_discount_active": boolean,
  "copy_cost": 90|100,
  "current_round_id": string|null
}
```

**GET /rounds/{round_id}** - Get round details and status
- Returns: `{round_id, type, status, expires_at, prompt_text?, original_word?, submitted_word?, cost?}`

**GET /player/pending-results** - List completed wordsets awaiting result viewing
- Returns: `{pending: [{wordset_id, prompt_text, completed_at, role: "prompt"|"copy"}]}`

**GET /wordsets/{wordset_id}/results** - Get voting results (triggers prize collection)
- Returns: 
```json
{
  "votes": [
    {"word": "famous", "vote_count": 4, "is_original": true},
    {"word": "popular", "vote_count": 3, "is_original": false},
    {"word": "wealthy", "vote_count": 3, "is_original": false}
  ],
  "your_word": "famous",
  "your_points": 4,
  "your_payout": 62.50,
  "total_pool": 250,
  "total_votes": 10,
  "already_collected": boolean
}
```
- First call credits account, subsequent calls just return data

---

## Recommended Flow

### App Startup / Reconnection Flow
```
1. GET /player/balance
   - Display current balance in UI
   - Check if daily_bonus_available is true

2. If daily_bonus_available:
   - Show "Daily Bonus Available: $100" notification
   - Auto-claim or prompt user to claim
   - POST /player/claim-daily-bonus

3. GET /player/current-round
   - If active round exists: Resume that round's UI
   - Calculate time remaining from expires_at
   - If expired: Show timeout message, return to idle
   - If null: Show round selection screen

4. GET /player/pending-results
   - Display notification badge if any results pending
   - Show count in status bar

5. GET /rounds/available
   - Enable/disable Copy and Vote buttons based on availability
   - Show queue depths (prompts_waiting, wordsets_waiting)
   - If copy_discount_active: Show "$90 Copy Special!" prominently
   - Prompt button always enabled (if no current round)
```

### Idle State Polling
```
While player has no active round:

Every 10 seconds:
- GET /rounds/available
  - Update Copy/Vote button states
  - Update queue size displays
  - Update copy discount notification

- GET /player/pending-results
  - Update notification badge count
```

### Starting a Prompt Round
```
1. User clicks "Start Prompt" button
   
2. POST /rounds/prompt
   - If error "already_in_round": Show error, refresh UI
   - If error "insufficient_balance": Show error
   - If success: Display prompt and input field

3. Start client-side 60-second countdown timer
   - Calculate from expires_at timestamp
   - No server polling needed during active round
   - Display updates purely client-side

4. When timer reaches 0:
   - Disable submit button
   - Show "Time's up!" message
   - Backend has 5-second grace period (don't tell user)

5. User types word and clicks submit (before timer expires)
   
6. POST /rounds/{round_id}/submit with word
   - If error "invalid_word": Show error, let user retry (timer continues)
   - If error "expired": Show timeout message
   - If success: Show confirmation, return to idle state

7. Return to idle state
   - Resume polling GET /player/pending-results every 10 seconds
   - When wordset_id appears, show notification badge
```

### Starting a Copy Round
```
1. User clicks "Start Copy" button
   - Button only enabled if can_copy is true
   - Button shows "$90" if discount active, "$100" otherwise

2. POST /rounds/copy
   - If error "no_prompts_available": Shouldn't happen (button disabled), but show error
   - If error "already_in_round": Show error, refresh UI
   - If success: Display original word, input field, and cost paid

3. Start client-side 60-second countdown timer
   - Calculate from expires_at
   - No polling needed

4. When timer reaches 0:
   - Disable submit button
   - Show "Time's up! $10 entry fee forfeited..." (or $9 if discount active)

5. User types word and clicks submit

6. POST /rounds/{round_id}/submit with word
   - If error "duplicate": Show "That's the original word! Choose a different word." (timer continues, user can retry)
   - If error "invalid_word": Show error, let user retry
   - If error "expired": Show timeout message
   - If success: Show confirmation, return to idle state

7. Return to idle state and resume polling for results
```

### Starting a Vote Round
```
1. User clicks "Start Vote" button
   - Button only enabled if can_vote is true

2. POST /rounds/vote
   - If error "no_wordsets_available": Show error
   - If success: Display prompt and 3 words (randomized order)

3. Start client-side 15-second countdown timer
   - Calculate from expires_at
   - Show urgent visual feedback as time runs low (red at <5s)

4. When timer reaches 0:
   - Disable all word buttons
   - Show "Time's up! Vote forfeited (-$1)"
   - Return to idle after 2 seconds

5. User clicks one of the three words (before timer expires)

6. POST /wordsets/{wordset_id}/vote with word string
   - If error "expired": Show timeout message (forfeit $1)
   - If success: Immediately show results
     - Highlight correct word (green) and user's choice (red if wrong)
     - Show "Correct! +$5" or "Incorrect. The original was [word]"
     - Display earnings

7. Return to idle state immediately (no waiting for results)
```

### Viewing Results (Contributors)
```
1. User sees notification badge (from pending-results polling)

2. User clicks status bar or notification

3. GET /wordsets/{wordset_id}/results
   - Display full breakdown:
     - Original prompt
     - All three words with vote counts and bar charts
     - Highlight which was original
     - Show points: "You earned X points (Y votes)"
     - Show payout: "Your prize: $Z"
   - First view credits account
   - Subsequent views just display data (already_collected: true)

4. Update balance display
   - Fetch GET /player/balance to refresh

5. Return to idle state
```

### Error Handling
```
All API calls should handle:
- Network errors: Show retry button
- 401 Unauthorized: Re-authenticate
- 400 Bad Request: Show error message from response
- 404 Not Found: Round may have expired, return to idle
- 429 Too Many Requests: Show rate limit message
- 500 Server Error: Show generic error, allow retry

On any error during active round:
- Preserve round state if possible
- Allow user to retry submission
- If round expired, return to idle gracefully
```

### Browser Refresh / Reconnection
```
On page load or reconnection:

1. Follow "App Startup / Reconnection Flow" above

2. If current_round exists:
   - Resume appropriate UI for round type
   - Recalculate local timer from expires_at
   - Check if already expired:
     - If expires_at < now: Show timeout message, return to idle
     - If still active: Continue normally

3. If current_round is null:
   - Return to idle state
   - Check for pending results
   - Show round selection

This ensures seamless recovery from disconnection
```

### Abandonment (Timeout) Handling
```
Client-side timeout occurs:
- Stop allowing submissions (disable buttons)
- Show "Time's up!" message
- Explain consequences:
  - Prompt/Copy: "Entry fee forfeited (-$10)"
  - Vote: "Vote forfeited (-$1)"
- Automatically transition to idle

Server validates all submissions against expiry:
- Rejects submissions beyond grace period (expires_at + 5 seconds)
- Applies refunds/penalties automatically
- No explicit abandon endpoint needed

Backend processes timeouts:
- Periodic job checks for expired rounds
- Applies appropriate refunds/penalties
- Returns copy rounds to queue
- Removes player from active_round_id
```

---

## Data Models

### Player
- `player_id` (UUID)
- `balance` (integer)
- `created_at` (timestamp)
- `last_login_date` (date) - for daily bonus tracking
- `daily_bonus_claimed_at` (timestamp, nullable)
- `active_round_id` (UUID, nullable) - enforces one-round-at-a-time

### Prompt Round
- `round_id` (UUID)
- `player_id` (UUID)
- `prompt_id` (UUID, references prompt library)
- `prompt_text` (string)
- `submitted_word` (string, nullable)
- `status` (enum: active, submitted, expired, cancelled)
- `created_at` (timestamp)
- `expires_at` (timestamp)
- `cost` (integer, always 100)

### Copy Round
- `round_id` (UUID)
- `player_id` (UUID)
- `prompt_round_id` (UUID, references prompt round)
- `original_word` (string)
- `submitted_word` (string, nullable)
- `status` (enum: active, submitted, expired, abandoned)
- `created_at` (timestamp)
- `expires_at` (timestamp)
- `cost` (integer, 90 or 100) - tracks what player paid
- `system_contribution` (int, 0 or 10) - for discounted copies

### Word Set
- `wordset_id` (UUID)
- `prompt_round_id` (UUID)
- `copy_round_1_id` (UUID)
- `copy_round_2_id` (UUID)
- `prompt_text` (string)
- `original_word` (string)
- `copy_word_1` (string)
- `copy_word_2` (string)
- `word_positions` (array[3]) - randomized order for display
- `status` (enum: open, closing, closed, finalized)
- `vote_count` (integer)
- `third_vote_at` (timestamp, nullable) - starts 10-minute window
- `fifth_vote_at` (timestamp, nullable) - starts 60-second window
- `closes_at` (timestamp, nullable) - calculated based on vote timeline
- `created_at` (timestamp)
- `total_pool` (decimal, 300) - includes system contribution if applicable
- `system_contribution` (decimal, 0 or 10)

### Vote
- `vote_id` (UUID)
- `wordset_id` (UUID)
- `player_id` (UUID)
- `voted_index` (0|1|2) - position in randomized word_positions array
- `voted_word` (string) - the actual word voted for
- `correct` (boolean)
- `payout` (integer, 5 or 0) - gross payout
- `created_at` (timestamp)

### Result View
- `view_id` (UUID)
- `wordset_id` (UUID)
- `player_id` (UUID)
- `payout_collected` (boolean)
- `payout_amount` (decimal)
- `viewed_at` (timestamp)

### Transaction
- `transaction_id` (UUID)
- `player_id` (UUID)
- `amount` (integer, can be negative)
- `type` (enum: prompt_entry, copy_entry, vote_entry, vote_payout, prize_payout, refund, penalty, daily_bonus, system_contribution)
- `reference_id` (UUID, references round/wordset/vote)
- `created_at` (timestamp)

### Daily Bonus Log
- `bonus_id` (UUID)
- `player_id` (UUID)
- `amount` (integer, 100)
- `claimed_at` (timestamp)
- `date` (date) - for tracking one per day

---

## Word Validation

### Dictionary
- Use NASPA Word List (Tournament Word List)
- Preload into database
- ~190,000 words

### Validation Rules
1. Length: 2-15 characters
2. Characters: Only letters A-Z (case-insensitive)
3. Must exist in NASPA Word List
4. For copy rounds: Must not match original word (case-insensitive)

### Validation Process
```
1. Normalize input (trim whitespace, convert to uppercase)
2. Check length (2-15)
3. Check characters (A-Z only)
4. Check dictionary membership
5. For copies: Check against original word
6. Return success or specific error code
```

---

### Voting Timeline State Machine

```
Word Set Created → status: "open"
  ↓
3rd vote received → third_vote_at = now, status: "open"
  ↓
  Wait for earlier of:
  - 10 minutes elapsed since third_vote_at
  - 5th vote received
  ↓
5th vote received (within 10 min) → fifth_vote_at = now, status: "closing"
  ↓
  Accept voters for 60 seconds
  Grace period: voters who started within 60s get full 15s
  ↓
20th vote OR (60s + grace elapsed) → status: "closed"
  ↓
Calculate scores and payouts → status: "finalized"
```