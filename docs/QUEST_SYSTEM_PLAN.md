# 🎯 Quest/Bonus System Implementation Plan

## Overview
Implement a comprehensive quest and achievement system with 8 bonus types, progress tracking, claim mechanism, and celebratory UI notifications.

---

## Phase 1: Database Models & Migrations (Backend Foundation)

### Step 1.1: Create Quest Models
**File**: `backend/models/quest.py`

**Models to create**:
- `Quest` - Base quest definition and player progress tracking
  - `quest_id` (UUID, PK)
  - `player_id` (UUID, FK to players)
  - `quest_type` (String) - enum: hot_streak, deceptive_copy, obvious_original, round_completion_5, round_completion_10, round_completion_20, balanced_player, login_streak_7, feedback_contributor_10, feedback_contributor_50, milestone_votes_100, milestone_prompts_50, milestone_copies_100, milestone_phraseset_20votes
  - `status` (String) - enum: active, completed, claimed
  - `progress` (JSON) - Flexible progress tracking (e.g., `{"current": 3, "target": 5, "streak": 3}`)
  - `reward_amount` (Integer) - Flipcoins to award
  - `created_at` (DateTime)
  - `completed_at` (DateTime, nullable)
  - `claimed_at` (DateTime, nullable)
  - Indexes: player_id, quest_type, status
  - Unique constraint: player_id + quest_type (one quest per type per player at a time)

- `QuestTemplate` - Quest configuration (optional - can be hardcoded in service)
  - `template_id` (String, PK) - matches quest_type
  - `name` (String)
  - `description` (String)
  - `reward_amount` (Integer)
  - `target_value` (Integer)
  - `category` (String) - enum: streak, quality, activity, milestone

### Step 1.2: Create Migration
**File**: `backend/migrations/versions/XXX_add_quest_system.py`

- Create Quest table
- Create QuestTemplate table (optional)
- Add new transaction types: `quest_reward_hot_streak`, `quest_reward_deceptive_copy`, etc.

### Step 1.3: Update Transaction Model
**File**: `backend/models/transaction.py`

- Add new transaction types to enum/documentation

---

## Phase 2: Quest Service & Logic (Backend Business Logic)

### Step 2.1: Create Quest Service
**File**: `backend/services/quest_service.py`

**Core methods**:
```python
class QuestService:
    async def initialize_quests_for_player(player_id: UUID)
    async def get_player_quests(player_id: UUID, status: Optional[str] = None) -> List[Quest]
    async def get_quest_by_id(quest_id: UUID) -> Quest
    async def claim_quest_reward(quest_id: UUID, player_id: UUID, transaction_service: TransactionService)

    # Progress tracking methods
    async def check_and_update_vote_streak(player_id: UUID, vote_correct: bool)
    async def check_deceptive_copy(phraseset_id: UUID)
    async def check_obvious_original(phraseset_id: UUID)
    async def increment_round_completion(player_id: UUID)
    async def check_balanced_player(player_id: UUID)
    async def check_login_streak(player_id: UUID)
    async def increment_feedback_count(player_id: UUID)
    async def check_milestone_votes(player_id: UUID, total_votes: int)
    async def check_milestone_prompts(player_id: UUID, total_prompts: int)
    async def check_milestone_copies(player_id: UUID, total_copies: int)
    async def check_milestone_phraseset_20votes(player_id: UUID, phraseset_id: UUID, vote_count: int)
```

### Step 2.2: Quest Definitions & Configuration
**File**: `backend/config.py` or create `backend/services/quest_definitions.py`

Define quest configurations:
```python
QUEST_CONFIGS = {
    "hot_streak_5": {"name": "Hot Streak", "target": 5, "reward": 10, ...},
    "hot_streak_10": {"name": "Blazing Streak", "target": 10, "reward": 25, ...},
    # ... etc
}
```

### Step 2.3: Integrate Quest Checks into Existing Services

**Files to modify**:
- `backend/services/vote_service.py` - After vote submission
  - Call `quest_service.check_and_update_vote_streak()`
  - Call `quest_service.check_milestone_votes()`

- `backend/services/phraseset_service.py` - When phraseset finalizes
  - Call `quest_service.check_deceptive_copy()`
  - Call `quest_service.check_obvious_original()`
  - Call `quest_service.check_milestone_phraseset_20votes()`

- `backend/services/round_service.py` - After round completion
  - Call `quest_service.increment_round_completion()`

- `backend/services/player_service.py` - During login
  - Call `quest_service.check_login_streak()`

- `backend/routers/prompt_feedback.py` - After feedback submission
  - Call `quest_service.increment_feedback_count()`

---

## Phase 3: Quest API Endpoints (Backend Routes)

### Step 3.1: Create Quest Router
**File**: `backend/routers/quests.py`

**Endpoints**:
```python
GET /quests - Get all player quests (active, completed, claimed)
  Response: List[QuestResponse]

GET /quests/active - Get only active quests with progress
  Response: List[QuestResponse]

GET /quests/claimable - Get completed but unclaimed quests
  Response: List[QuestResponse]

GET /quests/{quest_id} - Get single quest details
  Response: QuestResponse

POST /quests/{quest_id}/claim - Claim quest reward
  Response: ClaimQuestRewardResponse {success, quest_type, reward_amount, new_balance}
```

### Step 3.2: Create Quest Schemas
**File**: `backend/schemas/quest.py`

```python
class QuestProgress(BaseModel):
    current: int
    target: int
    percentage: float
    # Quest-specific fields

class QuestResponse(BaseModel):
    quest_id: UUID
    quest_type: str
    name: str
    description: str
    status: str  # active, completed, claimed
    progress: QuestProgress
    reward_amount: int
    category: str
    created_at: datetime
    completed_at: Optional[datetime]
    claimed_at: Optional[datetime]

class ClaimQuestRewardResponse(BaseModel):
    success: bool
    quest_type: str
    reward_amount: int
    new_balance: int
```

### Step 3.3: Register Router
**File**: `backend/main.py`

Add quest router to app

---

## Phase 4: Frontend API Client (Frontend-Backend Integration)

### Step 4.1: Update API Types
**File**: `frontend/src/api/types.ts`

```typescript
export interface QuestProgress {
  current: number;
  target: number;
  percentage: number;
  // Quest-specific optional fields
  streak?: number;
  votes_needed?: number;
  days_logged_in?: number[];
}

export interface Quest {
  quest_id: string;
  quest_type: string;
  name: string;
  description: string;
  status: 'active' | 'completed' | 'claimed';
  progress: QuestProgress;
  reward_amount: number;
  category: 'streak' | 'quality' | 'activity' | 'milestone';
  created_at: string;
  completed_at?: string;
  claimed_at?: string;
}

export interface ClaimQuestRewardResponse {
  success: boolean;
  quest_type: string;
  reward_amount: number;
  new_balance: number;
}
```

### Step 4.2: Add Quest API Methods
**File**: `frontend/src/api/client.ts`

```typescript
async getQuests(): Promise<Quest[]>
async getActiveQuests(): Promise<Quest[]>
async getClaimableQuests(): Promise<Quest[]>
async getQuest(questId: string): Promise<Quest>
async claimQuestReward(questId: string): Promise<ClaimQuestRewardResponse>
```

---

## Phase 5: Quest Context & State Management (Frontend State)

### Step 5.1: Create Quest Context
**File**: `frontend/src/contexts/QuestContext.tsx`

```typescript
interface QuestContextType {
  quests: Quest[];
  activeQuests: Quest[];
  claimableQuests: Quest[];
  loading: boolean;
  error: string | null;
  refreshQuests: () => Promise<void>;
  claimQuest: (questId: string) => Promise<ClaimQuestRewardResponse>;
  clearError: () => void;
}
```

### Step 5.2: Integrate with GameContext
**File**: `frontend/src/contexts/GameContext.tsx`

- Add quest state management
- Call `refreshQuests()` after relevant actions (vote, round completion, etc.)
- Trigger notifications when quests complete

---

## Phase 6: Quest UI Components (Frontend Components)

### Step 6.1: Create Success Notification Component
**File**: `frontend/src/components/SuccessNotification.tsx`

- Similar to ErrorNotification but with:
  - Green/blue branded color scheme
  - Celebration icon (🎉, ⭐, etc.)
  - Auto-dismiss after 5 seconds
  - Support for "Quest completed!" messages

### Step 6.2: Create Quest Card Component
**File**: `frontend/src/components/QuestCard.tsx`

Props: `quest: Quest, onClaim?: (questId: string) => void`

**Features**:
- Display quest name, description
- Progress bar (visual representation of progress.current / progress.target)
- Reward amount badge
- Status indicator (active, completed, claimed)
- Claim button (for completed quests)
- Category icon/badge
- Locked/unlocked visual state

### Step 6.3: Create Quest Progress Bar Component
**File**: `frontend/src/components/QuestProgressBar.tsx`

- Animated progress bar
- Show percentage or "X / Y" format
- Color coding by category
- Pulse animation when near completion

### Step 6.4: Create Quest Category Filter
**File**: `frontend/src/components/QuestFilter.tsx`

- Tabs/buttons for: All, Streaks, Quality, Activity, Milestones
- Filter quest list by category

---

## Phase 7: Quests Page (Frontend Page)

### Step 7.1: Create Quests Page
**File**: `frontend/src/pages/Quests.tsx`

**Layout** (similar to Dashboard/Results):
```
Header with balance
┌─────────────────────────────────────┐
│ Quests & Achievements               │
│                                     │
│ [Claimable Rewards: 3] 🎁          │
│ Total Rewards Earned: $XXX         │
└─────────────────────────────────────┘

[Category Filter: All | Streaks | Quality | Activity | Milestones]

┌── Active Quests ──────────────────┐
│ [QuestCard] [QuestCard] [QuestCard] │
│ [QuestCard] [QuestCard]             │
└─────────────────────────────────────┘

┌── Completed Quests ───────────────┐
│ [QuestCard] [QuestCard]            │
└─────────────────────────────────────┘

┌── Claimed Quests ─────────────────┐
│ [QuestCard] [QuestCard] [QuestCard] │
└─────────────────────────────────────┘
```

**Features**:
- Real-time progress updates
- Click quest card to expand details
- Claim button for completed quests
- Filter by category
- Sort by: progress, reward amount, completion date
- Empty states with encouraging messages

### Step 7.2: Add Navigation Link
**Files**: `frontend/src/App.tsx`, `frontend/src/components/Header.tsx` (if exists)

- Add "Quests" link to navigation
- Badge indicator for claimable quests count

---

## Phase 8: Dashboard Integration (Frontend Dashboard)

### Step 8.1: Add Quest Notification to Dashboard
**File**: `frontend/src/pages/Dashboard.tsx`

Add after daily bonus notification:
```tsx
{claimableQuests.length > 0 && (
  <div className="bg-green-50 border-2 border-green-400 rounded-lg p-4">
    <h3>🎉 Quests Completed!</h3>
    <p>You have {claimableQuests.length} quest(s) ready to claim</p>
    <button onClick={() => navigate('/quests')}>View Quests</button>
  </div>
)}
```

### Step 8.2: Add Celebration Notification Trigger
**File**: `frontend/src/contexts/GameContext.tsx` or `QuestContext.tsx`

When quest completes (status changes from active to completed):
- Show SuccessNotification with quest name and reward
- Play subtle animation (optional)
- Update balance display

**Trigger points**:
- After vote submission (if hot streak completes)
- After phraseset finalization (if deceptive/obvious bonus earned)
- After round completion
- After daily login
- Polling/refresh (check if new completed quests exist)

---

## Phase 9: Quest-Specific Logic Implementation (Backend Deep Dive)

### Step 9.1: Hot Streak Quest (5/10/20 correct votes)
**Integration point**: `backend/services/vote_service.py` after vote submission

**Logic**:
```python
# After creating vote record
if vote.correct:
    await quest_service.check_and_update_vote_streak(player_id, correct=True)
else:
    await quest_service.check_and_update_vote_streak(player_id, correct=False)  # Resets streak
```

**Quest progress structure**:
```json
{
  "current_streak": 3,
  "target": 5,
  "highest_streak": 8
}
```

**Auto-create next tier**: When hot_streak_5 is claimed, auto-create hot_streak_10

### Step 9.2: Deceptive Copy Quest (75%+ votes)
**Integration point**: `backend/services/phraseset_service.py` when phraseset finalizes

**Logic**:
```python
# After vote tallying
for copy_player in [copy1_player_id, copy2_player_id]:
    copy_vote_count = votes_for_copy[copy_player]
    vote_percentage = copy_vote_count / total_votes
    if vote_percentage >= 0.75:
        await quest_service.complete_deceptive_copy_quest(copy_player, vote_percentage)
```

**Quest progress**: One-time completion, no streak

### Step 9.3: Obvious Original Quest (85%+ votes)
**Integration point**: `backend/services/phraseset_service.py` when phraseset finalizes

**Logic**: Similar to deceptive copy, check original phrase vote percentage

### Step 9.4: Round Completion Quests (5/10/20 rounds in 24h)
**Integration point**: `backend/services/round_service.py` after round submission

**Logic**:
```python
# After successful round completion
await quest_service.increment_round_completion(player_id)
```

**Quest progress structure**:
```json
{
  "rounds_completed": 7,
  "target": 10,
  "window_start": "2025-10-17T12:00:00Z",
  "rounds_in_window": [list of round timestamps]
}
```

**Window logic**: Rolling 24-hour window, resets when quest claimed

### Step 9.5: Balanced Player Quest (1 prompt, 2 copies, 10 votes in 24h)
**Integration point**: Multiple - after each round type completion

**Quest progress structure**:
```json
{
  "window_start": "2025-10-17T12:00:00Z",
  "prompts": 1,
  "copies": 2,
  "votes": 8,
  "target": {"prompts": 1, "copies": 2, "votes": 10}
}
```

### Step 9.6: 7-Day Login Streak Quest
**Integration point**: `backend/services/player_service.py` during login or daily bonus check

**Logic**:
```python
# When player logs in
await quest_service.check_login_streak(player_id)
```

**Quest progress structure**:
```json
{
  "consecutive_days": 5,
  "target": 7,
  "last_login_date": "2025-10-17",
  "login_dates": ["2025-10-13", "2025-10-14", "2025-10-15", "2025-10-16", "2025-10-17"]
}
```

### Step 9.7: Feedback Contributor Quest (10/50 feedback submissions)
**Integration point**: `backend/routers/prompt_feedback.py` after feedback submission

**Logic**:
```python
# After creating prompt_feedback record
await quest_service.increment_feedback_count(player_id)
```

**Auto-create next tier**: feedback_contributor_10 → feedback_contributor_50

### Step 9.8: Milestone Quests
**Integration points**:
- 100th vote: `vote_service.py` after vote creation
- 50th prompt: `round_service.py` after prompt submission
- 100th copy: `round_service.py` after copy submission
- First phraseset with 20 votes: `phraseset_service.py` when vote count reaches 20

**Logic**: Check total count from database, complete quest if threshold reached

---

## Phase 10: Testing & Refinement

### Step 10.1: Backend Unit Tests
**Files**: `tests/test_quest_service.py`, `tests/test_quest_api.py`

Test cases:
- Quest creation and initialization
- Progress tracking for each quest type
- Reward claiming and transaction creation
- Edge cases (quest already claimed, insufficient data, etc.)
- Concurrency (multiple quest completions simultaneously)

### Step 10.2: Frontend Component Tests
**Files**: `frontend/src/components/__tests__/`

Test QuestCard, SuccessNotification, QuestProgressBar rendering

### Step 10.3: Integration Testing
- Complete workflows for each quest type
- Verify transactions created correctly
- Verify UI updates properly
- Test claim flow end-to-end

### Step 10.4: Manual QA
- Visual design consistency
- Mobile responsiveness
- Performance with many quests
- Notification timing and clarity

---

## Phase 11: Documentation & Deployment

### Step 11.1: Update Documentation
**Files**:
- `README.md` - Add quest system overview
- `docs/API.md` - Document quest endpoints
- `docs/DATA_MODELS.md` - Document Quest model
- `docs/ARCHITECTURE.md` - Explain quest service integration

### Step 11.2: Database Migration
- Run migration on development
- Test migration rollback
- Prepare migration for production

### Step 11.3: Configuration
- Add quest-related settings to config
- Environment variable configuration if needed

### Step 11.4: Deploy
- Backend deployment
- Frontend build and deployment
- Monitor for errors

---

## Implementation Summary

**Total Files to Create**: ~15
- Backend: 5 (models, service, router, schemas, migration)
- Frontend: 7 (page, components, context, API types/methods)
- Tests: 3+

**Total Files to Modify**: ~12
- Backend: 6 (existing services, main.py, config)
- Frontend: 4 (App.tsx, Dashboard.tsx, GameContext, client.ts)
- Docs: 4

**Estimated Complexity**: High (10-15 hours of implementation)

**Key Technical Decisions**:
1. Quest progress stored as JSON for flexibility
2. One Quest record per player per quest_type (unique constraint)
3. Auto-create next tier quests when current tier claimed
4. Polling vs WebSockets: Use polling initially (consistent with current architecture)
5. Quest completion triggers: Synchronous checks after relevant actions

**Risk Mitigation**:
- Use transactions for all quest rewards to ensure balance consistency
- Distributed locking for concurrent quest completions
- Graceful degradation if quest service fails (log error, don't block main action)
- Comprehensive error handling in claim flow

---

## Quest Definitions Reference

| Quest Type | Name | Target | Reward | Category | Resets |
|------------|------|--------|--------|----------|---------|
| hot_streak_5 | Hot Streak | 5 correct votes | $10 | Streak | On wrong vote |
| hot_streak_10 | Blazing Streak | 10 correct votes | $25 | Streak | On wrong vote |
| hot_streak_20 | Inferno Streak | 20 correct votes | $75 | Streak | On wrong vote |
| deceptive_copy | Master Deceiver | 75%+ votes to copy | $20 | Quality | Per phraseset |
| obvious_original | Clear Original | 85%+ votes to original | $15 | Quality | Per phraseset |
| round_completion_5 | Quick Player | 5 rounds in 24h | $25 | Activity | 24h window |
| round_completion_10 | Active Player | 10 rounds in 24h | $75 | Activity | 24h window |
| round_completion_20 | Power Player | 20 rounds in 24h | $200 | Activity | 24h window |
| balanced_player | Balanced Player | 1p/2c/10v in 24h | $20 | Activity | 24h window |
| login_streak_7 | Week Warrior | 7 consecutive days | $200 | Streak | On missed day |
| feedback_contributor_10 | Feedback Novice | 10 feedback submissions | $5 | Milestone | Never (one-time) |
| feedback_contributor_50 | Feedback Expert | 50 feedback submissions | $25 | Milestone | Never (one-time) |
| milestone_votes_100 | Century Voter | 100 total votes | $50 | Milestone | Never (one-time) |
| milestone_prompts_50 | Prompt Master | 50 total prompts | $100 | Milestone | Never (one-time) |
| milestone_copies_100 | Copy Champion | 100 total copies | $75 | Milestone | Never (one-time) |
| milestone_phraseset_20votes | Popular Set | First set with 20 votes | $25 | Milestone | Never (one-time) |

---

## Next Steps

Implementation can proceed in phases as outlined above. Each phase builds on the previous one, allowing for incremental development and testing.

**Recommended Start**: Phase 1 (Database Models & Migrations) to establish the foundation for the quest system.
