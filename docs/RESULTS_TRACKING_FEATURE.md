# Results Tracking Feature - Complete Design Specification

## Overview

This feature enables players to track their prompt and copy submissions throughout the game lifecycle - from initial submission through copy collection, voting, and final results. Players can see real-time progress of their phrasesets including who has copied them, who has voted, and what votes were cast.

## Current State Analysis

### What Exists
- **Backend**:
  - `GET /player/pending-results` - Returns finalized phrasesets only
  - `GET /phrasesets/{id}/results` - Shows final results for contributors (triggers prize collection)
  - PhraseSet model tracks: status, vote_count, third_vote_at, fifth_vote_at
  - ResultView model tracks prize collection

- **Frontend**:
  - Dashboard shows count of pending (finalized) results
  - Results page shows finalized results only
  - No tracking of in-progress phrasesets

### Gaps Identified
1. **No visibility into in-progress phrasesets** - Players can't see their prompts/copies before finalization
2. **No state transition tracking** - Can't see when copies are submitted or votes arrive
3. **No voter attribution** - Can't see who voted (only final tallies)
4. **No copy attribution** - Can't see who submitted copies
5. **Confusing results workflow** - Prize collection happens on first view, but unclear to users
6. **No separation of roles** - Results screen doesn't distinguish between prompts you created vs copies you submitted

## Feature Design

### User Stories

**As a player who submitted a prompt, I want to:**
1. See when copy players submit their phrases
2. See who submitted each copy
3. Track voting progress in real-time
4. See who voted and what they voted for
5. Know when my phraseset is finalized
6. Claim my prize explicitly

**As a player who submitted a copy, I want to:**
1. See the prompt after I submit
2. See the other copy player's submission
3. Track voting progress
4. See all votes
5. Claim my prize

**As a player, I want to:**
1. Distinguish between my prompts and my copies in the dashboard
2. View detailed state for any phraseset I contributed to
3. See historical results I've already claimed

---

## Database Schema Changes

### 1. New Table: `phraseset_activity`

Tracks all state transitions and events for audit and display.

```sql
CREATE TABLE phraseset_activity (
    activity_id UUID PRIMARY KEY,
    phraseset_id UUID NOT NULL REFERENCES phrasesets(phraseset_id),
    activity_type VARCHAR(50) NOT NULL,  -- 'prompt_created', 'copy_submitted', 'vote_submitted', 'finalized'
    player_id UUID REFERENCES players(player_id),  -- Who triggered this activity (NULL for system events)
    metadata JSONB,  -- Flexible storage for event-specific data
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    INDEX idx_phraseset_activity_phraseset_id (phraseset_id, created_at),
    INDEX idx_phraseset_activity_player_id (player_id, created_at)
);
```

**Activity Types:**
- `prompt_created` - Prompt round submitted
  - metadata: `{}`
- `copy1_submitted` - First copy submitted
  - metadata: `{"copy_player_id": UUID, "copy_phrase": "TEXT"}`
- `copy2_submitted` - Second copy submitted (creates phraseset)
  - metadata: `{"copy_player_id": UUID, "copy_phrase": "TEXT"}`
- `vote_submitted` - Vote received
  - metadata: `{"voter_id": UUID, "voted_phrase": "TEXT", "correct": bool}`
- `third_vote_reached` - System event
  - metadata: `{}`
- `fifth_vote_reached` - System event
  - metadata: `{}`
- `finalized` - System event
  - metadata: `{"total_votes": int, "payouts": {...}}`

### 2. Modify Table: `rounds`

Add tracking for prompts waiting in queue (before phraseset creation).

```sql
ALTER TABLE rounds
ADD COLUMN phraseset_status VARCHAR(20),  -- 'waiting_copies', 'waiting_copy1', 'active', 'finalized', 'abandoned'
ADD COLUMN copy1_player_id UUID REFERENCES players(player_id),
ADD COLUMN copy2_player_id UUID REFERENCES players(player_id);

CREATE INDEX idx_rounds_phraseset_status ON rounds(phraseset_status) WHERE round_type = 'prompt';
```

**Status meanings:**
- `waiting_copies` - Prompt submitted, waiting for 2 copy players
- `waiting_copy1` - First copy submitted, waiting for second
- `active` - Phraseset created, voting in progress
- `finalized` - Voting complete
- `abandoned` - Round expired before phraseset creation

### 3. Modify Table: `result_views`

Track when results were claimed separately from first view.

```sql
ALTER TABLE result_views
ADD COLUMN first_viewed_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN payout_claimed_at TIMESTAMP WITH TIME ZONE,
RENAME COLUMN payout_collected TO payout_claimed;
```

---

## API Endpoints

### 1. `GET /player/phrasesets` - Get All Player Phrasesets

Returns all phrasesets the player contributed to (prompt or copy), in all states.

**Query Parameters:**
- `role` (optional): Filter by role - "prompt", "copy", or "all" (default: "all")
- `status` (optional): Filter by status - "in_progress", "voting", "finalized", "all" (default: "all")
- `limit` (optional): Number of results (default: 50, max: 100)
- `offset` (optional): Pagination offset (default: 0)

**Response:**
```json
{
  "phrasesets": [
    {
      "phraseset_id": "uuid",
      "prompt_text": "my deepest desire is to be (a/an)",
      "your_role": "prompt",  // or "copy"
      "your_phrase": "FAMOUS",
      "status": "voting",  // or "waiting_copies", "waiting_copy1", "finalized"
      "created_at": "2025-01-10T12:00:00Z",
      "updated_at": "2025-01-10T12:05:00Z",

      // Progress indicators
      "has_copy1": true,
      "has_copy2": true,
      "vote_count": 8,
      "third_vote_at": "2025-01-10T12:10:00Z",
      "fifth_vote_at": null,
      "finalized_at": null,

      // Only when finalized
      "your_payout": null,
      "payout_claimed": false,

      // Counts
      "new_activity_count": 3  // Number of activities since last viewed
    }
  ],
  "total": 42,
  "has_more": true
}
```

### 2. `GET /player/phrasesets/summary` - Dashboard Summary

Quick summary for dashboard display.

**Response:**
```json
{
  "in_progress": {
    "prompts": 5,  // Your prompts waiting for copies or voting
    "copies": 3    // Your copies waiting for votes
  },
  "finalized": {
    "prompts": 12,  // Your finalized prompts
    "copies": 8,    // Your finalized copies
    "unclaimed_prompts": 2,  // Finalized but payout not claimed
    "unclaimed_copies": 1
  }
}
```

### 3. `GET /phrasesets/{phraseset_id}/details` - Detailed Phraseset View

Get full details including activity timeline. Available to contributors only.

**Response:**
```json
{
  "phraseset_id": "uuid",
  "prompt_text": "the secret to happiness is (a/an)",
  "status": "voting",  // waiting_copies, waiting_copy1, voting, finalized

  // Phrases
  "original_phrase": "LOVE",
  "copy_phrase_1": "MONEY",
  "copy_phrase_2": "CONTENTMENT",

  // Contributors (only show after phraseset created)
  "prompt_player": {
    "player_id": "uuid",
    "username": "Player1",  // Or player_id if username not implemented
    "is_you": true
  },
  "copy1_player": {
    "player_id": "uuid",
    "username": "Player2",
    "is_you": false
  },
  "copy2_player": {
    "player_id": "uuid",
    "username": "Player3",
    "is_you": false
  },

  // Voting progress
  "vote_count": 8,
  "third_vote_at": "2025-01-10T12:10:00Z",
  "fifth_vote_at": null,
  "closes_at": "2025-01-10T12:20:00Z",

  // Votes (if status is voting or finalized)
  "votes": [
    {
      "vote_id": "uuid",
      "voter": {
        "player_id": "uuid",
        "username": "Voter1"
      },
      "voted_phrase": "LOVE",
      "correct": true,
      "voted_at": "2025-01-10T12:11:00Z"
    }
  ],

  // Results (only if finalized)
  "results": {
    "vote_counts": {
      "LOVE": 4,
      "MONEY": 3,
      "CONTENTMENT": 3
    },
    "payouts": {
      "prompt": {"player_id": "uuid", "payout": 62, "points": 4},
      "copy1": {"player_id": "uuid", "payout": 93, "points": 6},
      "copy2": {"player_id": "uuid", "payout": 93, "points": 6}
    },
    "total_pool": 250
  },

  // Your info
  "your_role": "prompt",
  "your_phrase": "LOVE",
  "your_payout": 62,
  "payout_claimed": false,

  // Activity timeline
  "activity": [
    {
      "activity_type": "prompt_created",
      "player": {"player_id": "uuid", "username": "Player1"},
      "created_at": "2025-01-10T12:00:00Z"
    },
    {
      "activity_type": "copy1_submitted",
      "player": {"player_id": "uuid", "username": "Player2"},
      "metadata": {"copy_phrase": "MONEY"},
      "created_at": "2025-01-10T12:05:00Z"
    },
    {
      "activity_type": "copy2_submitted",
      "player": {"player_id": "uuid", "username": "Player3"},
      "metadata": {"copy_phrase": "CONTENTMENT"},
      "created_at": "2025-01-10T12:08:00Z"
    },
    {
      "activity_type": "vote_submitted",
      "player": {"player_id": "uuid", "username": "Voter1"},
      "metadata": {"voted_phrase": "LOVE", "correct": true},
      "created_at": "2025-01-10T12:11:00Z"
    }
  ],

  "created_at": "2025-01-10T12:00:00Z",
  "finalized_at": null
}
```

### 4. `POST /phrasesets/{phraseset_id}/claim` - Claim Prize

Explicitly claim prize from finalized phraseset. Idempotent.

**Response:**
```json
{
  "success": true,
  "amount": 62,
  "new_balance": 1062,
  "already_claimed": false
}
```

**Errors:**
- 400: Phraseset not finalized yet
- 403: Not a contributor
- 404: Phraseset not found

### 5. `GET /phrasesets/{phraseset_id}/activity` - Activity Timeline

Get activity timeline for a phraseset. (Can be merged with details endpoint if preferred)

**Response:**
```json
{
  "phraseset_id": "uuid",
  "activities": [
    {
      "activity_id": "uuid",
      "activity_type": "vote_submitted",
      "player": {
        "player_id": "uuid",
        "username": "Voter1"
      },
      "metadata": {
        "voted_phrase": "LOVE",
        "correct": true
      },
      "created_at": "2025-01-10T12:11:00Z"
    }
  ]
}
```

### 6. Modified: `GET /player/pending-results`

**Change:** Rename to better reflect purpose, add more detail.

**New name:** `GET /player/unclaimed-results`

**Response:**
```json
{
  "unclaimed": [
    {
      "phraseset_id": "uuid",
      "prompt_text": "the meaning of life is",
      "your_role": "prompt",
      "your_phrase": "LOVE",
      "finalized_at": "2025-01-06T12:00:00Z",
      "your_payout": 75,
      "vote_count": 10
    }
  ],
  "total_unclaimed_amount": 150
}
```

---

## Backend Service Changes

### 1. New Service: `ActivityService`

**File:** `backend/services/activity_service.py`

**Responsibilities:**
- Record phraseset activity events
- Query activity timelines
- Track viewed state

**Key Methods:**
```python
async def record_activity(
    phraseset_id: UUID,
    activity_type: str,
    player_id: UUID | None = None,
    metadata: dict | None = None
) -> PhrasesetActivity

async def get_phraseset_activity(
    phraseset_id: UUID,
    since: datetime | None = None
) -> list[PhrasesetActivity]

async def get_new_activity_counts(
    player_id: UUID,
    phraseset_ids: list[UUID]
) -> dict[UUID, int]
```

### 2. Modified Service: `RoundService`

**Changes:**
- Update `submit_prompt_phrase()` to record "prompt_created" activity
- Update `submit_copy_phrase()` to record "copy1_submitted" or "copy2_submitted"
- Track prompt round status (waiting_copies, waiting_copy1)

### 3. Modified Service: `VoteService`

**Changes:**
- Update `submit_vote()` to record "vote_submitted" activity
- Update `_finalize_wordset()` to record "finalized" activity
- Track vote milestone events (third_vote_reached, fifth_vote_reached)

### 4. New Service: `PhrasesetService`

**File:** `backend/services/phraseset_service.py`

**Responsibilities:**
- Get player's phrasesets with filtering
- Get detailed phraseset view
- Handle prize claiming
- Check contributor access

**Key Methods:**
```python
async def get_player_phrasesets(
    player_id: UUID,
    role: str | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0
) -> tuple[list[dict], int]

async def get_phraseset_details(
    phraseset_id: UUID,
    player_id: UUID
) -> dict

async def claim_prize(
    phraseset_id: UUID,
    player_id: UUID,
    transaction_service: TransactionService
) -> dict

async def is_contributor(
    phraseset_id: UUID,
    player_id: UUID
) -> bool
```

### 5. Modified: `ResultView` model

Update to track claim separately from view:
- `first_viewed_at` - When player first viewed the details
- `payout_claimed_at` - When player explicitly claimed
- Backward compatibility: existing logic auto-claims on first view

---

## Frontend Changes

### 1. New Component: `PhrasesetList`

**File:** `frontend/src/components/PhrasesetList.tsx`

Reusable list component showing phrasesets with status badges.

**Props:**
```typescript
interface PhrasesetListProps {
  phrasesets: PhrasesetSummary[];
  onSelect: (phrasesetId: string) => void;
  selectedId?: string;
}
```

### 2. Modified Page: `Dashboard`

**Changes:**
- Split "Results Ready" notification into:
  - "Prompt Results Ready" (count)
  - "Copy Results Ready" (count)
- Add "In Progress" section showing:
  - Prompts in progress (waiting for copies or votes)
  - Copies in progress (waiting for votes)
- Add badges showing new activity

**New sections:**
```tsx
{/* In Progress Phrasesets */}
{inProgressCount > 0 && (
  <div className="bg-gray-50 border rounded-lg p-4 mb-6">
    <div className="flex justify-between items-center">
      <div>
        <p className="font-semibold text-gray-800">Phrasesets In Progress</p>
        <p className="text-sm text-gray-700">
          {summary.in_progress.prompts} prompts • {summary.in_progress.copies} copies
        </p>
      </div>
      <button onClick={handleViewTracking} className="...">
        Track Progress
      </button>
    </div>
  </div>
)}

{/* Unclaimed Results */}
{unclaimedCount > 0 && (
  <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
    <div className="flex justify-between items-center">
      <div>
        <p className="font-semibold text-green-800">Results Ready to Claim!</p>
        <p className="text-sm text-green-700">
          {summary.finalized.unclaimed_prompts} prompts •
          {summary.finalized.unclaimed_copies} copies •
          ${summary.total_unclaimed_amount} total
        </p>
      </div>
      <button onClick={handleClaimResults} className="...">
        Claim Prizes
      </button>
    </div>
  </div>
)}
```

### 3. New Page: `PhrasesetTracking`

**File:** `frontend/src/pages/PhrasesetTracking.tsx`

Two-column layout:
- **Left:** List of all phrasesets with filters
- **Right:** Detailed view of selected phraseset

**Filters:**
- Role: All / My Prompts / My Copies
- Status: All / In Progress / Voting / Finalized

**Phraseset card shows:**
- Prompt text
- Your phrase
- Status badge
- Progress indicators (e.g., "2/2 copies, 8 votes")
- New activity badge

### 4. New Component: `PhrasesetDetails`

**File:** `frontend/src/components/PhrasesetDetails.tsx`

Shows detailed phraseset information:

**For in-progress phrasesets:**
- Prompt text
- Your phrase and role
- Contributors (who submitted copies)
- Status timeline
- Vote count and voters
- Vote breakdown (if available)

**For finalized phrasesets:**
- All of the above
- Final vote tally
- Payout calculation
- Claim button (if not claimed)

**Activity Timeline:**
```tsx
<div className="space-y-2">
  {activity.map(item => (
    <div className="flex items-start gap-3 p-3 bg-gray-50 rounded">
      <ActivityIcon type={item.activity_type} />
      <div className="flex-1">
        <p className="font-semibold">{formatActivityType(item.activity_type)}</p>
        <p className="text-sm text-gray-600">
          {item.player.username} • {formatTime(item.created_at)}
        </p>
        {item.metadata && <ActivityMetadata data={item.metadata} />}
      </div>
    </div>
  ))}
</div>
```

### 5. Modified Page: `Results`

**Changes:**
- Simplify to only show unclaimed results
- Add "Claim All" button
- Add "View All Phrasesets" link to new tracking page
- Show total unclaimed amount prominently

Or consider merging with PhrasesetTracking page with a "Unclaimed" filter.

### 6. New Component: `StatusBadge`

**File:** `frontend/src/components/StatusBadge.tsx`

Reusable badge for phraseset status.

```tsx
<StatusBadge status="waiting_copies" />
<StatusBadge status="voting" count={8} />
<StatusBadge status="finalized" />
```

### 7. New Component: `ProgressBar`

**File:** `frontend/src/components/ProgressBar.tsx`

Visual progress indicator for voting.

```tsx
<ProgressBar
  current={8}
  thirdVote={3}
  fifthVote={5}
  max={20}
/>
```

### 8. API Client Updates

**File:** `frontend/src/api/client.ts`

Add new API methods:
```typescript
async getPlayerPhrasesets(params?: {
  role?: string;
  status?: string;
  limit?: number;
  offset?: number;
}): Promise<PhrasesetListResponse>

async getPhrasesetsSummary(): Promise<PhrasesetSummary>

async getPhrasesetDetails(phrasesetId: string): Promise<PhrasesetDetails>

async claimPrize(phrasesetId: string): Promise<ClaimResponse>

async getUnclaimedResults(): Promise<UnclaimedResultsResponse>
```

---

## Navigation Flow

### Updated App Routes

```tsx
<Route path="/phrasesets" element={<PhrasesetTracking />} />
<Route path="/phrasesets/:id" element={<PhrasesetDetails />} />
<Route path="/claim-results" element={<ClaimResults />} />
```

### User Journey

1. **Player submits prompt**
   - Redirected to dashboard
   - See "In Progress: 1 prompt" in new section
   - Click "Track Progress" → Go to phraseset tracking page
   - See prompt listed with status "Waiting for copies"

2. **First copy submitted**
   - Phraseset tracking page updates (via polling)
   - Status changes to "1/2 copies received"
   - Activity timeline shows new entry

3. **Second copy submitted**
   - Status changes to "Voting in progress"
   - Can now see both copy players and their phrases
   - Vote count starts at 0

4. **Votes arrive**
   - Vote count increments
   - Activity timeline shows each vote
   - Can see who voted and what they voted for
   - Progress bar fills up

5. **Phraseset finalized**
   - Status badge changes to "Finalized"
   - Results section appears
   - Dashboard shows "1 unclaimed result"
   - Vote breakdown and payouts visible
   - Big "Claim $62 Prize" button

6. **Claim prize**
   - Click claim button
   - Balance updates
   - Button changes to "Prize Claimed ✓"
   - Phraseset moves to "Claimed" list

---

## Database Migration

**File:** `backend/migrations/versions/XXXXXX_add_phraseset_tracking.py`

```python
def upgrade():
    # Create phraseset_activity table
    op.create_table(
        'phraseset_activity',
        sa.Column('activity_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('phraseset_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('activity_type', sa.String(50), nullable=False),
        sa.Column('player_id', postgresql.UUID(as_uuid=True)),
        sa.Column('metadata', postgresql.JSONB),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['phraseset_id'], ['phrasesets.phraseset_id']),
        sa.ForeignKeyConstraint(['player_id'], ['players.player_id']),
    )

    op.create_index(
        'idx_phraseset_activity_phraseset_id',
        'phraseset_activity',
        ['phraseset_id', 'created_at']
    )

    # Modify rounds table
    op.add_column('rounds', sa.Column('phraseset_status', sa.String(20)))
    op.add_column('rounds', sa.Column('copy1_player_id', postgresql.UUID(as_uuid=True)))
    op.add_column('rounds', sa.Column('copy2_player_id', postgresql.UUID(as_uuid=True)))

    # Modify result_views table
    op.add_column('result_views', sa.Column('first_viewed_at', sa.DateTime(timezone=True)))
    op.add_column('result_views', sa.Column('payout_claimed_at', sa.DateTime(timezone=True)))
    op.alter_column('result_views', 'payout_collected', new_column_name='payout_claimed')

    # Backfill first_viewed_at and payout_claimed_at from viewed_at
    op.execute("""
        UPDATE result_views
        SET first_viewed_at = viewed_at,
            payout_claimed_at = viewed_at
        WHERE payout_claimed = true
    """)

def downgrade():
    # ... reverse operations
```

---

## Testing Requirements

### Backend Unit Tests

**File:** `tests/test_activity_service.py`
- Test recording activity
- Test querying activity timeline
- Test activity counts

**File:** `tests/test_phraseset_service.py`
- Test getting player phrasesets with filters
- Test phraseset details access control
- Test prize claiming (idempotent)
- Test contributor verification

**File:** `tests/test_phraseset_tracking.py`
- Test activity recording during round submission
- Test activity recording during voting
- Test finalization activity

### Backend Integration Tests

**File:** `tests/test_phraseset_tracking_flow.py`

Test complete flow:
1. Player A submits prompt
2. Verify prompt appears in A's phraseset list with status "waiting_copies"
3. Player B submits copy
4. Verify status changes to "waiting_copy1" for Player A
5. Verify activity recorded
6. Player C submits second copy
7. Verify phraseset created and status is "voting"
8. Verify both A, B, C can see phraseset details
9. Verify Player D (non-contributor) cannot access details
10. Players vote
11. Verify activity timeline shows all votes
12. Phraseset finalizes
13. Verify results available
14. Player A claims prize
15. Verify balance updated and claim is idempotent

### Frontend Component Tests

Test new components:
- PhrasesetList rendering
- PhrasesetDetails rendering for different states
- StatusBadge displays correctly
- ProgressBar calculations
- Activity timeline formatting

### E2E Tests

**Scenario:** Complete phraseset lifecycle tracking
1. Log in as Player 1, submit prompt
2. Navigate to tracking page
3. Verify prompt appears with "waiting" status
4. Log in as Player 2, submit copy
5. Switch back to Player 1
6. Verify copy submission shows in activity
7. Continue through voting and finalization
8. Verify claim button works

---

## Implementation Phases

### Phase 1: Backend Foundation (Week 1)
- [ ] Create phraseset_activity table
- [ ] Implement ActivityService
- [ ] Implement PhrasesetService
- [ ] Modify RoundService to record activities
- [ ] Modify VoteService to record activities
- [ ] Add new API endpoints
- [ ] Write unit tests
- [ ] Migration script

### Phase 2: Backend Integration (Week 1-2)
- [ ] Integration tests
- [ ] Update existing endpoints for backward compatibility
- [ ] Performance testing (ensure activity queries don't slow down)
- [ ] Add indexes for common queries

### Phase 3: Frontend Components (Week 2)
- [ ] StatusBadge component
- [ ] ProgressBar component
- [ ] PhrasesetList component
- [ ] Activity timeline component
- [ ] API client updates
- [ ] TypeScript types

### Phase 4: Frontend Pages (Week 2-3)
- [ ] PhrasesetTracking page
- [ ] PhrasesetDetails component
- [ ] Modify Dashboard
- [ ] Modify Results page
- [ ] Navigation updates
- [ ] Polling logic for real-time updates

### Phase 5: Testing & Polish (Week 3)
- [ ] E2E tests
- [ ] Performance optimization
- [ ] Error handling
- [ ] Loading states
- [ ] Empty states
- [ ] Mobile responsiveness
- [ ] Accessibility

### Phase 6: Documentation (Week 3)
- [ ] Update API.md
- [ ] Update FRONTEND_PLAN.md
- [ ] Add user guide for new features
- [ ] Update README

---

## Open Questions & Decisions Needed

### 1. Privacy: Should players see who voted?
**Options:**
- A) Show all voter names and their votes (max transparency)
- B) Show vote breakdown but anonymize voters
- C) Only show final tallies until phraseset finalized

**Recommendation:** Option A for MVP - full transparency encourages engagement and allows players to verify fairness. Can add privacy settings later.

### 2. Should copy players see each other's phrases before voting starts?
**Current:** They cannot see each other's phrases until phraseset is created

**Options:**
- A) Keep hidden until voting starts
- B) Reveal immediately after both copies submitted
- C) Reveal after first vote arrives

**Recommendation:** Option B - reveal when phraseset becomes active. This allows copy players to see competition and builds anticipation.

### 3. Activity retention: How long to keep activity records?
**Options:**
- A) Keep forever (complete audit trail)
- B) Archive after 30/60/90 days
- C) Keep only summary after finalization

**Recommendation:** Option A for MVP since storage is cheap and players may want to review old games.

### 4. Claim workflow: Auto-claim vs explicit claim?
**Current:** Auto-claim on first view of results

**Options:**
- A) Keep auto-claim (backward compatible)
- B) Require explicit claim (clear action)
- C) Auto-claim but show prominent confirmation

**Recommendation:** Option C - auto-claim on view but show a success banner with amount. Add explicit claim button for unclaimed results.

### 5. Real-time updates: Polling vs WebSockets?
**Options:**
- A) Polling (simpler, current approach)
- B) WebSockets (real-time but more complex)
- C) Server-Sent Events (middle ground)

**Recommendation:** Option A for MVP - use polling every 5-10 seconds on tracking page. Add WebSockets in Phase 2+.

### 6. Should we show prompt text to copy players before they submit?
**Current:** Copy players only see the original phrase, not the prompt

**Concern:** If we show prompt in tracking, copy players could see it before submitting

**Recommendation:** Only show full phraseset details (including prompt) after the copy player has submitted their phrase. Until then, show limited info.

---

## Success Metrics

### Engagement Metrics
- % of players who visit tracking page
- Average time spent on tracking page
- % of players who check in-progress phrasesets
- Frequency of tracking page visits

### Usability Metrics
- % of unclaimed prizes after 24/48/72 hours
- % of players who claim all available prizes
- Time from finalization to claim
- Number of support requests about "where's my prize"

### Performance Metrics
- API response time for phraseset details
- Activity query performance
- Frontend load time for tracking page

---

## Future Enhancements

### Phase 2+ Ideas
1. **Notifications**
   - Push notifications for state changes
   - Email digests of unclaimed prizes
   - In-app notification center

2. **Social Features**
   - Comment on phrasesets
   - Share results
   - "Favorite" phrasesets

3. **Analytics Dashboard**
   - Personal statistics (win rate, avg payout)
   - Prompt performance over time
   - Copy success rate

4. **Advanced Filters**
   - Search by prompt text
   - Filter by date range
   - Sort by payout amount

5. **Batch Actions**
   - Claim all unclaimed prizes
   - Archive old phrasesets
   - Export results to CSV

6. **Real-time Features**
   - WebSocket updates
   - Live vote ticker
   - Countdown timers for closing phrasesets

7. **Gamification**
   - Badges for milestones
   - Streak tracking
   - Leaderboards

---

## Backward Compatibility

### API Changes
- All new endpoints (no breaking changes)
- Existing `/player/pending-results` kept for compatibility
- New `/player/unclaimed-results` recommended for new clients

### Database Changes
- All additive (new tables, new columns)
- Nullable columns for new fields
- Migration includes backfill for existing data

### Frontend Changes
- New pages don't affect existing flow
- Dashboard updates are purely additive
- Can feature-flag new UI during rollout

---

## Summary

This feature adds comprehensive tracking of phrasesets throughout their lifecycle, giving players visibility into:
- When their prompts get copied
- Who submitted copies
- Real-time voting progress
- Complete vote attribution
- Clear prize claiming workflow

**Key Benefits:**
1. **Transparency** - Players see exactly what's happening with their submissions
2. **Engagement** - Real-time updates encourage return visits
3. **Trust** - Full audit trail builds confidence in game fairness
4. **Clarity** - Explicit prize claiming removes confusion

**Implementation Effort:**
- Backend: ~40-60 hours
- Frontend: ~40-60 hours
- Testing: ~20-30 hours
- **Total: ~100-150 hours (~3 weeks)**

**Technical Risk:** Low - All additive changes, well-defined scope, existing patterns to follow.
