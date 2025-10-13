# Results Tracking Feature - Visual Diagrams

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐  ┌──────────────────┐  ┌─────────────────┐  │
│  │  Dashboard   │  │ Phraseset        │  │ Claim Results   │  │
│  │              │  │ Tracking Page    │  │ Page            │  │
│  │ • In Progress│  │                  │  │                 │  │
│  │ • Unclaimed  │  │ • Filter List    │  │ • Unclaimed     │  │
│  │ • Quick Stats│  │ • Detail View    │  │ • Claim Button  │  │
│  └──────┬───────┘  └────────┬─────────┘  └────────┬────────┘  │
│         │                   │                      │            │
│         └───────────────────┼──────────────────────┘            │
│                             │                                   │
│  ┌──────────────────────────┴────────────────────────────────┐ │
│  │              API Client (TypeScript)                       │ │
│  │  • getPlayerPhrasesets()                                  │ │
│  │  • getPhrasesetDetails()                                  │ │
│  │  • claimPrize()                                           │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────┬───────────────────────────────────────┘
                          │ HTTPS/JSON
┌─────────────────────────┴───────────────────────────────────────┐
│                      Backend (FastAPI)                           │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    API Endpoints                            │ │
│  │  GET  /player/phrasesets                                   │ │
│  │  GET  /player/phrasesets/summary                           │ │
│  │  GET  /phrasesets/{id}/details                             │ │
│  │  POST /phrasesets/{id}/claim                               │ │
│  └────────────────────┬───────────────────────────────────────┘ │
│                       │                                          │
│  ┌────────────────────┴───────────────────────────────────────┐ │
│  │                     Services Layer                          │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐ │ │
│  │  │ Phraseset    │  │  Activity    │  │  Transaction    │ │ │
│  │  │ Service      │  │  Service     │  │  Service        │ │ │
│  │  │              │  │              │  │                 │ │ │
│  │  │ • Query      │  │ • Record     │  │ • Prize Claim   │ │ │
│  │  │ • Filter     │  │ • Timeline   │  │ • Balance Upd   │ │ │
│  │  │ • Access Chk │  │ • Counts     │  │                 │ │ │
│  │  └──────────────┘  └──────────────┘  └─────────────────┘ │ │
│  └────────────────────┬───────────────────────────────────────┘ │
│                       │                                          │
│  ┌────────────────────┴───────────────────────────────────────┐ │
│  │                    Database (PostgreSQL)                    │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐ │ │
│  │  │ phrasesets   │  │ phraseset_   │  │ result_views    │ │ │
│  │  │              │  │ activity     │  │                 │ │ │
│  │  │ • status     │  │              │  │ • payout_claimed│ │ │
│  │  │ • vote_count │  │ • type       │  │ • claim_at      │ │ │
│  │  │ • created_at │  │ • metadata   │  │                 │ │ │
│  │  └──────────────┘  └──────────────┘  └─────────────────┘ │ │
│  └──────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

---

## Data Flow: Recording Activity

```
User Action: Submit Copy Phrase
         │
         ├─► [POST /rounds/{id}/submit]
         │
         ├─► RoundService.submit_copy_phrase()
         │        │
         │        ├─► Validate phrase
         │        ├─► Update round status
         │        ├─► Create/update phraseset
         │        │
         │        └─► ActivityService.record_activity()
         │                  │
         │                  ├─► Create PhrasesetActivity record
         │                  │   • type: "copy1_submitted" or "copy2_submitted"
         │                  │   • player_id: copy player
         │                  │   • metadata: {copy_phrase: "..."}
         │                  │
         │                  └─► Insert into database
         │
         └─► Response: {success: true}


Timeline View:
┌────────────────────────────────────────────┐
│ 📝 Copy Submitted                          │
│    Player2 submitted "MONEY"               │
│    2 minutes ago                           │
└────────────────────────────────────────────┘
```

---

## Data Flow: Viewing Phraseset Details

```
User Opens Tracking Page
         │
         ├─► [GET /player/phrasesets]
         │        │
         │        └─► PhrasesetService.get_player_phrasesets()
         │                  │
         │                  ├─► Query phrasesets where player contributed
         │                  ├─► Apply role/status filters
         │                  ├─► Get activity counts
         │                  │
         │                  └─► Return list
         │
User Selects Phraseset
         │
         ├─► [GET /phrasesets/{id}/details]
         │        │
         │        ├─► PhrasesetService.is_contributor()
         │        │   • Verify access
         │        │
         │        ├─► Query phraseset with relationships
         │        │   • prompt_round → player
         │        │   • copy_rounds → players
         │        │   • votes → voters
         │        │
         │        └─► ActivityService.get_phraseset_activity()
         │                  │
         │                  ├─► Query all activities for phraseset
         │                  ├─► Order by created_at
         │                  ├─► Include player info
         │                  │
         │                  └─► Return timeline
         │
         └─► Render: Full phraseset details + activity timeline
```

---

## State Machine: Phraseset Lifecycle

```
                    ┌─────────────────┐
                    │ Prompt Submitted│
                    │   (waiting_     │
                    │    copies)      │
                    └────────┬────────┘
                             │
                    Copy 1 Submitted
                             │
                    ┌────────▼────────┐
                    │  Waiting Copy 2 │
                    │  (waiting_copy1)│
                    └────────┬────────┘
                             │
                    Copy 2 Submitted
                             │
                    ┌────────▼────────┐
                    │  Phraseset      │
                    │  Created        │
                    │  (open, voting) │
                    └────────┬────────┘
                             │
            ┌────────────────┼────────────────┐
            │                │                │
       0-2 votes        3-4 votes        5+ votes
            │                │                │
    ┌───────▼──────┐  ┌──────▼─────┐  ┌──────▼─────┐
    │ Open         │  │ Open       │  │ Closing    │
    │              │  │ (10min     │  │ (60sec     │
    │              │  │  window)   │  │  window)   │
    └───────┬──────┘  └──────┬─────┘  └──────┬─────┘
            │                │                │
            └────────────────┼────────────────┘
                             │
                    20 votes OR timeout
                             │
                    ┌────────▼────────┐
                    │   Finalized     │
                    │                 │
                    │ • Calculate $   │
                    │ • Available for │
                    │   claiming      │
                    └────────┬────────┘
                             │
                    Player claims prize
                             │
                    ┌────────▼────────┐
                    │   Claimed       │
                    │                 │
                    │ • Prize paid    │
                    │ • Archived      │
                    └─────────────────┘

Activity Timeline Shows:
✓ prompt_created
✓ copy1_submitted
✓ copy2_submitted
✓ vote_submitted (x N)
✓ third_vote_reached
✓ fifth_vote_reached
✓ finalized
```

---

## UI Component Hierarchy

```
PhrasesetTrackingPage
│
├── Filters
│   ├── RoleFilter (All/Prompts/Copies)
│   └── StatusFilter (All/In Progress/Voting/Finalized)
│
├── PhrasesetList (Left Column)
│   └── PhrasesetCard[]
│       ├── Prompt text
│       ├── Your phrase
│       ├── StatusBadge
│       ├── Progress summary
│       └── New activity indicator
│
└── PhrasesetDetails (Right Column)
    ├── Header
    │   ├── Prompt text
    │   ├── StatusBadge
    │   └── Your role/phrase
    │
    ├── ContributorsSection
    │   └── ContributorCard[]
    │       ├── Player name
    │       ├── Phrase
    │       └── "You" indicator
    │
    ├── VotingProgressSection
    │   ├── ProgressBar
    │   ├── Vote count
    │   └── Time remaining
    │
    ├── VotesSection
    │   └── VoteCard[]
    │       ├── Voter name
    │       ├── Voted phrase
    │       ├── Correct/incorrect icon
    │       └── Timestamp
    │
    ├── ResultsSection (if finalized)
    │   ├── Vote breakdown
    │   ├── Payout calculation
    │   └── ClaimButton
    │
    └── ActivityTimeline
        └── ActivityItem[]
            ├── Activity icon
            ├── Activity description
            ├── Player name
            ├── Metadata
            └── Timestamp
```

---

## Database Schema Relationships

```
┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│   players    │         │    rounds    │         │  phrasesets  │
│──────────────│         │──────────────│         │──────────────│
│ player_id PK │◄────────│ player_id FK │         │ phraseset_id │
│ api_key      │         │ round_id  PK │         │ (PK)         │
│ balance      │         │ round_type   │◄────┐   │              │
│              │         │ status       │     │   │ prompt_round_│
│              │         │ phraseset_id │     └───│ id        FK │
│              │         │ (FK nullable)│         │              │
└──────────────┘         └──────────────┘     ┌───│ copy_round_1_│
                                              │   │ id        FK │
                                              │   │              │
                                              └───│ copy_round_2_│
                                                  │ id        FK │
                                                  │              │
                                                  │ status       │
                                                  │ vote_count   │
                                                  │ third_vote_at│
                                                  │ fifth_vote_at│
                                                  │ finalized_at │
                                                  └──────┬───────┘
                                                         │
                    ┌────────────────────────────────────┤
                    │                                    │
         ┌──────────▼────────┐              ┌────────────▼────────┐
         │ phraseset_        │              │   result_views      │
         │ activity          │              │─────────────────────│
         │───────────────────│              │ view_id          PK │
         │ activity_id    PK │              │ phraseset_id     FK │
         │ phraseset_id   FK │              │ player_id        FK │
         │ activity_type     │              │ payout_claimed      │
         │ player_id      FK │              │ payout_amount       │
         │ metadata   (JSONB)│              │ first_viewed_at     │
         │ created_at        │              │ payout_claimed_at   │
         └───────────────────┘              └─────────────────────┘
                    │
                    │
         ┌──────────▼────────┐
         │     votes         │
         │───────────────────│
         │ vote_id        PK │
         │ phraseset_id   FK │
         │ player_id      FK │
         │ voted_phrase      │
         │ correct           │
         │ payout            │
         │ created_at        │
         └───────────────────┘
```

---

## Activity Recording Points

```
┌─────────────────────────────────────────────────────────────┐
│                     Round Submission Flow                    │
└─────────────────────────────────────────────────────────────┘

Prompt Submission:
  RoundService.submit_prompt_phrase()
    → ActivityService.record_activity(
        type: "prompt_created",
        player_id: prompt_player_id
      )

Copy 1 Submission:
  RoundService.submit_copy_phrase()
    → ActivityService.record_activity(
        type: "copy1_submitted",
        player_id: copy1_player_id,
        metadata: {copy_phrase: "..."}
      )

Copy 2 Submission:
  RoundService.submit_copy_phrase()
    → ActivityService.record_activity(
        type: "copy2_submitted",
        player_id: copy2_player_id,
        metadata: {copy_phrase: "..."}
      )
    → Create PhraseSet (triggers voting phase)

┌─────────────────────────────────────────────────────────────┐
│                      Voting Flow                             │
└─────────────────────────────────────────────────────────────┘

Vote Submission:
  VoteService.submit_vote()
    → Create Vote record
    → ActivityService.record_activity(
        type: "vote_submitted",
        player_id: voter_id,
        metadata: {
          voted_phrase: "...",
          correct: true/false
        }
      )

Vote Timeline Updates:
  VoteService._update_vote_timeline()
    → If vote_count == 3:
        ActivityService.record_activity(
          type: "third_vote_reached",
          player_id: null
        )
    → If vote_count == 5:
        ActivityService.record_activity(
          type: "fifth_vote_reached",
          player_id: null
        )

Finalization:
  VoteService._finalize_wordset()
    → Calculate payouts
    → ActivityService.record_activity(
        type: "finalized",
        player_id: null,
        metadata: {
          total_votes: N,
          payouts: {...}
        }
      )
```

---

## Frontend State Management

```
┌─────────────────────────────────────────────────────────────┐
│                    GameContext (Global)                      │
└─────────────────────────────────────────────────────────────┘
  • player (balance, outstanding_prompts)
  • activeRound
  • refreshBalance()
  • refreshCurrentRound()

┌─────────────────────────────────────────────────────────────┐
│              PhrasesetTracking Page (Local)                  │
└─────────────────────────────────────────────────────────────┘
  State:
    • phrasesets: PhrasesetSummary[]
    • selectedId: string | null
    • details: PhrasesetDetails | null
    • filters: {role, status}
    • loading states
    • error states

  Effects:
    • Load phrasesets on mount
    • Load details when selection changes
    • Poll for updates every 5-10 seconds
    • Refresh after claim action

  Actions:
    • setFilters()
    • selectPhraseset()
    • claimPrize()
    • refresh()

┌─────────────────────────────────────────────────────────────┐
│                    Dashboard (Local)                         │
└─────────────────────────────────────────────────────────────┘
  State:
    • summary: PhrasesetDashboardSummary
    • unclaimedResults: UnclaimedResult[]

  Effects:
    • Load summary on mount
    • Poll every 30 seconds

  Actions:
    • navigateToTracking()
    • navigateToClaimResults()
```

---

## Polling Strategy

```
Dashboard:
  • Poll summary every 30 seconds
  • Only when page is visible
  • Cancel on unmount

Tracking Page:
  • Poll phraseset list every 30 seconds
  • Poll selected phraseset details every 5-10 seconds
  • Increase frequency if status is "closing"
  • Stop polling finalized phrasesets
  • Pause when tab not visible

Smart Polling (optimization):
  • Use exponential backoff for finalized
  • Aggressive polling (5s) for active voting
  • Normal polling (30s) for waiting copies
  • Stop polling after 5 minutes of no changes

Future: WebSocket Events
  • "phraseset.copy_submitted"
  • "phraseset.vote_received"
  • "phraseset.finalized"
  • Instant updates, no polling needed
```

---

## Access Control Flow

```
GET /phrasesets/{id}/details

Step 1: Authentication
  ├─► Check X-API-Key header
  ├─► Load Player from database
  └─► Proceed if valid

Step 2: Load Phraseset
  ├─► Query PhraseSet by phraseset_id
  ├─► Include relationships (prompt_round, copy_rounds)
  └─► 404 if not found

Step 3: Authorization (Contributor Check)
  ├─► Get contributor player_ids
  │   • prompt_round.player_id
  │   • copy_round_1.player_id
  │   • copy_round_2.player_id
  │
  ├─► Check if current player in contributors
  │
  └─► If NOT contributor:
      • Return 403 Forbidden
      • "Not a contributor to this phraseset"

Step 4: Load Additional Data
  ├─► Load activity timeline
  ├─► Load votes (if status allows)
  ├─► Load results (if finalized)
  └─► Calculate display data

Step 5: Return Response
  └─► Full phraseset details with activity
```

---

## Example API Responses

### GET /player/phrasesets/summary

```json
{
  "in_progress": {
    "prompts": 5,
    "copies": 3
  },
  "finalized": {
    "prompts": 12,
    "copies": 8,
    "unclaimed_prompts": 2,
    "unclaimed_copies": 1
  },
  "total_unclaimed_amount": 150
}
```

### GET /player/phrasesets?role=prompt&status=voting

```json
{
  "phrasesets": [
    {
      "phraseset_id": "abc-123",
      "prompt_text": "my deepest desire is to be (a/an)",
      "your_role": "prompt",
      "your_phrase": "FAMOUS",
      "status": "voting",
      "created_at": "2025-01-10T12:00:00Z",
      "updated_at": "2025-01-10T12:15:00Z",
      "has_copy1": true,
      "has_copy2": true,
      "vote_count": 8,
      "third_vote_at": "2025-01-10T12:10:00Z",
      "fifth_vote_at": null,
      "finalized_at": null,
      "your_payout": null,
      "payout_claimed": false,
      "new_activity_count": 3
    }
  ],
  "total": 1,
  "has_more": false
}
```

### GET /phrasesets/abc-123/details

```json
{
  "phraseset_id": "abc-123",
  "prompt_text": "my deepest desire is to be (a/an)",
  "status": "voting",
  "original_phrase": "FAMOUS",
  "copy_phrase_1": "POPULAR",
  "copy_phrase_2": "WEALTHY",
  "prompt_player": {
    "player_id": "player-1",
    "username": "Player1",
    "is_you": true
  },
  "copy1_player": {
    "player_id": "player-2",
    "username": "Player2",
    "is_you": false
  },
  "copy2_player": {
    "player_id": "player-3",
    "username": "Player3",
    "is_you": false
  },
  "vote_count": 8,
  "third_vote_at": "2025-01-10T12:10:00Z",
  "fifth_vote_at": null,
  "closes_at": null,
  "votes": [
    {
      "vote_id": "vote-1",
      "voter": {
        "player_id": "voter-1",
        "username": "Voter1"
      },
      "voted_phrase": "FAMOUS",
      "correct": true,
      "voted_at": "2025-01-10T12:11:00Z"
    }
  ],
  "results": null,
  "your_role": "prompt",
  "your_phrase": "FAMOUS",
  "your_payout": null,
  "payout_claimed": false,
  "activity": [
    {
      "activity_type": "prompt_created",
      "player": {
        "player_id": "player-1",
        "username": "Player1"
      },
      "created_at": "2025-01-10T12:00:00Z"
    },
    {
      "activity_type": "copy1_submitted",
      "player": {
        "player_id": "player-2",
        "username": "Player2"
      },
      "metadata": {
        "copy_phrase": "POPULAR"
      },
      "created_at": "2025-01-10T12:05:00Z"
    }
  ],
  "created_at": "2025-01-10T12:00:00Z",
  "finalized_at": null
}
```

---

## Performance Considerations

### Database Indexes

```sql
-- High priority (query hot paths)
CREATE INDEX idx_phraseset_activity_phraseset_created
  ON phraseset_activity(phraseset_id, created_at);

CREATE INDEX idx_rounds_player_status
  ON rounds(player_id, status)
  WHERE round_type IN ('prompt', 'copy');

CREATE INDEX idx_phrasesets_status_created
  ON phrasesets(status, created_at);

-- Medium priority
CREATE INDEX idx_result_views_player_claimed
  ON result_views(player_id, payout_claimed);

CREATE INDEX idx_votes_phraseset_created
  ON votes(phraseset_id, created_at);
```

### Query Optimization

```python
# Bad: N+1 queries
for phraseset in phrasesets:
    activity = get_activity(phraseset.id)  # N queries

# Good: Batch query
phraseset_ids = [p.id for p in phrasesets]
activities = get_activities_for_phrasesets(phraseset_ids)  # 1 query
```

### Caching Strategy

```python
# Cache summary in Redis (5 minute TTL)
@cache(key="phraseset_summary:{player_id}", ttl=300)
async def get_phraseset_summary(player_id):
    ...

# Invalidate on state changes
async def record_activity(...):
    await record_to_db(...)
    await cache.delete(f"phraseset_summary:{player_id}")
```

---

## Migration Strategy

### Step 1: Add Tables (Zero Downtime)
- Add phraseset_activity table
- Add new columns to rounds (nullable)
- Add new columns to result_views (nullable)

### Step 2: Deploy Backend (Backward Compatible)
- New endpoints don't affect existing functionality
- Old endpoints still work
- Activity recording is additive

### Step 3: Backfill Data (Optional)
- Create "finalized" activities for existing phrasesets
- No functional impact if skipped

### Step 4: Deploy Frontend
- New pages don't replace old ones
- Dashboard updates are additive
- Feature flag for gradual rollout

### Step 5: Monitor
- Watch query performance
- Track API response times
- Monitor user engagement
