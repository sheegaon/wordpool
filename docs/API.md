# WordPool API Documentation

## Base URL

```
Development: http://localhost:8000
Production: https://your-app.herokuapp.com
```

## Authentication

All endpoints except `/health`, `/`, and `POST /player` require authentication via API key.

**Header:**
```
X-API-Key: <your-api-key-uuid>
```

**Getting an API Key:**
Use the `POST /player` endpoint to create a new player account and receive an API key.

**Security Notes:**
- API keys are UUIDs, not JWTs (no expiration)
- Store securely (localStorage/sessionStorage for web, secure storage for mobile)
- Use `POST /player/rotate-key` if compromised
- No password recovery - losing API key means losing account

## Response Format

### Success Response
```json
{
  // Response data based on endpoint
}
```

### Error Response
```json
{
  "detail": "Human-readable error message"
}
```

### HTTP Status Codes
- `200 OK` - Success
- `201 Created` - Resource created (POST /player)
- `400 Bad Request` - Invalid request or business logic error
- `401 Unauthorized` - Missing or invalid API key
- `404 Not Found` - Resource not found
- `409 Conflict` - State conflict (e.g., already voted)
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error

### Common Error Messages
- `insufficient_balance` - Not enough balance for operation
- `already_in_round` - Player already has active round
- `expired` - Round expired past grace period
- `already_voted` - Already voted on this wordset
- `already_claimed_today` - Daily bonus already claimed
- `invalid_word` - Word validation failed
- `no_prompts_available` - No prompts available for copy
- `no_wordsets_available` - No wordsets available for voting
- `max_outstanding_prompts` - Player has 10 open/closing wordsets

---

## Endpoints

### Health & Info

#### `GET /`
Get API information.

**Response:**
```json
{
  "message": "WordPool API - Phase 1 MVP",
  "version": "1.0.0",
  "environment": "development",
  "docs": "/docs"
}
```

#### `GET /health`
Health check endpoint (no authentication required).

**Response:**
```json
{
  "status": "ok",
  "database": "connected",
  "redis": "memory"  // or "connected"
}
```

---

### Player Endpoints

#### `POST /player`
Create a new player account (no authentication required).

**Request:**
```
POST /player
```

**Response (201 Created):**
```json
{
  "player_id": "3555a0e9-d46d-4a36-8756-f0e9c836d822",
  "api_key": "dff60a88-04c8-4a11-a8d8-874add980d12",
  "balance": 1000,
  "message": "Player created! Use this API key in the X-API-Key header for authentication. Starting balance: \$1000"
}
```

**Important:** Save the `api_key` immediately - it cannot be retrieved later.

**cURL Example:**
```bash
curl -X POST http://localhost:8000/player
```

#### `POST /player/rotate-key`
Rotate API key for security (requires authentication).

**Request:**
```bash
curl -X POST http://localhost:8000/player/rotate-key \
  -H "X-API-Key: your-current-api-key"
```

**Response:**
```json
{
  "new_api_key": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "message": "API key rotated successfully. Use the new key for all future requests. Your old key is now invalid."
}
```

**Important:**
- Your old API key becomes invalid immediately
- Update all clients with the new key
- Use if you suspect key compromise

#### `GET /player/balance`
Get player balance and status.

**Response:**
```json
{
  "balance": 1000,
  "starting_balance": 1000,
  "daily_bonus_available": false,
  "daily_bonus_amount": 100,
  "last_login_date": "2025-01-06",
  "outstanding_prompts": 0
}
```

#### `POST /player/claim-daily-bonus`
Claim daily login bonus (\$100).

**Response:**
```json
{
  "success": true,
  "amount": 100,
  "new_balance": 1100
}
```

**Errors:**
- `already_claimed_today` - Already claimed bonus today
- `not_eligible` - Created account today

#### `GET /player/current-round`
Get currently active round.

**Response (active prompt round):**
```json
{
  "round_id": "uuid",
  "round_type": "prompt",
  "state": {
    "round_id": "uuid",
    "status": "active",
    "expires_at": "2025-01-06T12:34:56",
    "cost": 100,
    "prompt_text": "my deepest desire is to be (a/an)"
  },
  "expires_at": "2025-01-06T12:34:56"
}
```

**Response (active copy round):**
```json
{
  "round_id": "uuid",
  "round_type": "copy",
  "state": {
    "round_id": "uuid",
    "status": "active",
    "expires_at": "2025-01-06T12:34:56",
    "cost": 90,
    "original_word": "FAMOUS",
    "discount_active": true
  },
  "expires_at": "2025-01-06T12:34:56"
}
```

**Response (active vote round):**
```json
{
  "round_id": "uuid",
  "round_type": "vote",
  "state": {
    "round_id": "uuid",
    "status": "active",
    "expires_at": "2025-01-06T12:34:56",
    "wordset_id": "uuid",
    "prompt_text": "the secret to happiness is (a/an)",
    "words": ["LOVE", "MONEY", "CONTENTMENT"]
  },
  "expires_at": "2025-01-06T12:34:56"
}
```

**Response (no active round):**
```json
{
  "round_id": null,
  "round_type": null,
  "state": null,
  "expires_at": null
}
```

**Notes:**
- `state` structure varies by `round_type` (prompt/copy/vote)
- `status` can be "active" or "submitted"
- Frontend should poll this endpoint or check after each action

#### `GET /player/pending-results`
Get list of finalized wordsets awaiting result viewing.

**Response:**
```json
{
  "pending": [
    {
      "wordset_id": "uuid",
      "prompt_text": "the meaning of life is",
      "completed_at": "2025-01-06T12:00:00",
      "role": "prompt",
      "payout_collected": false
    }
  ]
}
```

---

### Round Endpoints

#### `POST /rounds/prompt`
Start a prompt round (-\$100).

**Request Body:**
```json
{}
```

**Response:**
```json
{
  "round_id": "uuid",
  "prompt_text": "my deepest desire is to be (a/an)",
  "expires_at": "2025-01-06T12:35:56",
  "cost": 100
}
```

**Errors:**
- `already_in_round` - Player already in active round
- `insufficient_balance` - Balance < \$100
- `max_outstanding_prompts` - Player has 10 open/closing wordsets

#### `POST /rounds/copy`
Start a copy round (-\$100 or -\$90).

**Response:**
```json
{
  "round_id": "uuid",
  "original_word": "FAMOUS",
  "prompt_round_id": "uuid",
  "expires_at": "2025-01-06T12:36:00",
  "cost": 90,
  "discount_active": true
}
```

**Errors:**
- `no_prompts_available` - No prompts in queue
- `already_in_round` - Player already in active round
- `insufficient_balance` - Balance < cost

#### `POST /rounds/vote`
Start a vote round (-\$1).

**Response:**
```json
{
  "round_id": "uuid",
  "wordset_id": "uuid",
  "prompt_text": "the secret to happiness is (a/an)",
  "words": ["LOVE", "MONEY", "CONTENTMENT"],  // Randomized order
  "expires_at": "2025-01-06T12:30:15"
}
```

**Errors:**
- `no_wordsets_available` - No wordsets in queue
- `already_in_round` - Player already in active round
- `insufficient_balance` - Balance < \$1

#### `POST /rounds/{round_id}/submit`
Submit word for prompt or copy round.

**Request Body:**
```json
{
  "word": "famous"
}
```

**Response:**
```json
{
  "success": true,
  "word": "FAMOUS"
}
```

**Errors:**
- `invalid_word` - Word not in dictionary or invalid format
- `duplicate` - Copy word matches original
- `expired` - Past grace period
- `not_found` - Round not found or not owned by player

#### `GET /rounds/available`
Get round availability status.

**Response:**
```json
{
  "can_prompt": true,
  "can_copy": true,
  "can_vote": false,
  "prompts_waiting": 12,
  "wordsets_waiting": 0,
  "copy_discount_active": true,
  "copy_cost": 90,
  "current_round_id": null
}
```

#### `GET /rounds/{round_id}`
Get round details.

**Response:**
```json
{
  "round_id": "uuid",
  "type": "prompt",
  "status": "submitted",
  "expires_at": "2025-01-06T12:35:56",
  "prompt_text": "my deepest desire is to be (a/an)",
  "original_word": null,
  "submitted_word": "FAMOUS",
  "cost": 100
}
```

---

### Wordset Endpoints

#### `POST /wordsets/{wordset_id}/vote`
Submit vote for wordset.

**Request Body:**
```json
{
  "word": "LOVE"
}
```

**Response:**
```json
{
  "correct": true,
  "payout": 5,
  "original_word": "LOVE",
  "your_choice": "LOVE"
}
```

**Errors:**
- `expired` - Past grace period
- `already_voted` - Already voted on this wordset
- `player_not_in_round` - Not in active vote round

#### `GET /wordsets/{wordset_id}/results`
Get wordset results (collects prize on first view).

**Response:**
```json
{
  "prompt_text": "my deepest desire is to be (a/an)",
  "votes": [
    {"word": "FAMOUS", "vote_count": 4, "is_original": true},
    {"word": "POPULAR", "vote_count": 3, "is_original": false},
    {"word": "WEALTHY", "vote_count": 3, "is_original": false}
  ],
  "your_word": "FAMOUS",
  "your_role": "prompt",
  "your_points": 4,
  "your_payout": 62,
  "total_pool": 250,
  "total_votes": 10,
  "already_collected": true,
  "finalized_at": "2025-01-06T13:00:00"
}
```

**Errors:**
- `Wordset not found` - Invalid wordset ID
- `Wordset not yet finalized` - Still collecting votes
- `Not a contributor to this wordset` - Player wasn't prompt/copy contributor

---

## Example Workflows

### Complete Game Flow

```bash
# 1. Check balance
curl -H "X-API-Key: your-key" http://localhost:8000/player/balance

# 2. Start prompt round
curl -X POST -H "X-API-Key: your-key" http://localhost:8000/rounds/prompt

# 3. Submit word
curl -X POST -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{"word":"famous"}' \
  http://localhost:8000/rounds/{round_id}/submit

# 4. Start copy round (as different player)
curl -X POST -H "X-API-Key: other-key" http://localhost:8000/rounds/copy

# 5. Submit copy word
curl -X POST -H "X-API-Key: other-key" \
  -H "Content-Type: application/json" \
  -d '{"word":"popular"}' \
  http://localhost:8000/rounds/{round_id}/submit

# 6. Start vote round (after 2 copies submitted)
curl -X POST -H "X-API-Key: voter-key" http://localhost:8000/rounds/vote

# 7. Submit vote
curl -X POST -H "X-API-Key: voter-key" \
  -H "Content-Type: application/json" \
  -d '{"word":"FAMOUS"}' \
  http://localhost:8000/wordsets/{wordset_id}/vote

# 8. View results (after finalization)
curl -H "X-API-Key: your-key" http://localhost:8000/wordsets/{wordset_id}/results
```

---

## Rate Limiting

Rate limiting is enforced to prevent abuse:
- General endpoints: 100 requests/minute per API key
- Vote submission: 20 requests/minute per API key

**Response when rate limited:**
```json
{
  "detail": "Rate limit exceeded. Try again later."
}
```

---

## Interactive API Documentation

Visit `/docs` for interactive Swagger UI documentation where you can test all endpoints.

Visit `/redoc` for alternative ReDoc documentation.

---

## Game Configuration

### Timing
- **Prompt round**: 60 seconds
- **Copy round**: 60 seconds
- **Vote round**: 15 seconds
- **Grace period**: 5 seconds (not shown to users - allows late submissions)

### Economics
- **Starting balance**: \$1000
- **Daily bonus**: \$100
- **Prompt cost**: \$100
- **Copy cost**: \$100 normal, \$90 with discount
- **Vote cost**: \$1
- **Vote payout (correct)**: \$5
- **Wordset prize pool**: \$300
- **Copy discount threshold**: >10 prompts waiting
- **Max outstanding prompts**: 10 per player

### Validation
- **Word length**: 2-15 characters
- **Word format**: Letters A-Z only (case insensitive, stored uppercase)
- **Dictionary**: NASPA word list
- **Copy validation**: Must differ from original word

### WordSet Voting Lifecycle
1. **Open**: 0-2 votes submitted
2. **Closing**: 3+ votes, 10-minute window starts
3. **Rapid closing**: 5+ votes, 60-second window starts
4. **Closed**: Window expired, no new votes
5. **Finalized**: Results calculated, prizes distributed

### Prize Distribution
- Prize pool split among prompt + 2 copy contributors
- Share proportional to votes received for your word
- System contributes \$10 if copy used discount pricing

## Frontend Integration

### CORS
CORS is enabled for all origins in development. For production:
- Configure `CORS_ORIGINS` environment variable
- Include credentials in requests if using cookies
- API key authentication via headers is recommended

### State Management
**Required state to track:**
- Current player API key (persistent storage)
- Current balance (update from `/player/balance`)
- Active round state (poll `/player/current-round` or update after actions)
- Pending results count (from `/player/pending-results`)

**Recommended polling intervals:**
- Balance/status: Every 30 seconds or after actions
- Current round: Every 5 seconds if timer is active
- Pending results: Every 60 seconds or after round completion

### Timer Management
- Display countdown using `expires_at` timestamp
- Don't show grace period to users (5 seconds)
- Calculate time remaining: `expires_at - current_time`
- Show "expired" when timer reaches 0
- User can still submit within grace period

### Error Handling
- Check `status` code first (200/400/401/404/409)
- Parse `detail` field for user-friendly message
- Handle `insufficient_balance` by prompting to claim daily bonus
- Handle `already_in_round` by fetching current round state
- Handle `expired` by refreshing available rounds

### Typical User Flow
1. **First visit**: Call `POST /player` → store API key
2. **Return visit**: Load API key → call `GET /player/balance`
3. **Check daily bonus**: If `daily_bonus_available` → offer to claim
4. **Start round**: Check `GET /rounds/available` → start desired round type
5. **During round**: Display timer, submit word before expiry
6. **Check results**: Poll `/player/pending-results` → view when ready

### TypeScript Types (Example)
```typescript
interface Player {
  balance: number
  daily_bonus_available: boolean
  outstanding_prompts: number
}

interface ActiveRound {
  round_id: string | null
  round_type: 'prompt' | 'copy' | 'vote' | null
  expires_at: string | null
  state: PromptState | CopyState | VoteState | null
}

interface PromptState {
  round_id: string
  status: 'active' | 'submitted'
  expires_at: string
  cost: number
  prompt_text: string
}

interface CopyState {
  round_id: string
  status: 'active' | 'submitted'
  expires_at: string
  cost: number
  original_word: string
  discount_active: boolean
}

interface VoteState {
  round_id: string
  status: 'active' | 'submitted'
  expires_at: string
  wordset_id: string
  prompt_text: string
  words: string[]
}
```

## Notes

- All timestamps in UTC ISO 8601 format
- All currency amounts in whole dollars (integer values: 100 = \$100)
- Words automatically converted to uppercase
- Grace period allows submissions up to 5 seconds past expiry
- `/docs` and `/redoc` provide interactive API testing
