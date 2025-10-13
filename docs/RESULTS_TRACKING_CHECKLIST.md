# Results Tracking Feature - Implementation Checklist

Quick reference checklist for implementing the results tracking feature.

## Phase 1: Backend Foundation ✅

### Database Schema
- [ ] Create migration file `XXXXXX_add_phraseset_tracking.py`
- [ ] Add `phraseset_activity` table with columns:
  - [ ] activity_id (UUID, PK)
  - [ ] phraseset_id (UUID, FK)
  - [ ] activity_type (VARCHAR)
  - [ ] player_id (UUID, FK, nullable)
  - [ ] metadata (JSONB)
  - [ ] created_at (TIMESTAMP)
- [ ] Add indexes on phraseset_activity
- [ ] Modify `rounds` table:
  - [ ] Add phraseset_status column
  - [ ] Add copy1_player_id column
  - [ ] Add copy2_player_id column
- [ ] Modify `result_views` table:
  - [ ] Add first_viewed_at column
  - [ ] Add payout_claimed_at column
  - [ ] Rename payout_collected to payout_claimed
- [ ] Test migration up/down

### Models
- [ ] Create `backend/models/phraseset_activity.py`
- [ ] Add PhrasesetActivity model with relationships
- [ ] Update Round model with new columns
- [ ] Update ResultView model with new columns
- [ ] Add relationships to existing models

### Services
- [ ] Create `backend/services/activity_service.py`
  - [ ] `record_activity()` method
  - [ ] `get_phraseset_activity()` method
  - [ ] `get_new_activity_counts()` method
- [ ] Create `backend/services/phraseset_service.py`
  - [ ] `get_player_phrasesets()` method
  - [ ] `get_phraseset_summary()` method
  - [ ] `get_phraseset_details()` method
  - [ ] `claim_prize()` method
  - [ ] `is_contributor()` method
- [ ] Modify `backend/services/round_service.py`
  - [ ] Record "prompt_created" activity in submit_prompt_phrase()
  - [ ] Record "copy1_submitted" or "copy2_submitted" in submit_copy_phrase()
  - [ ] Update prompt round status tracking
- [ ] Modify `backend/services/vote_service.py`
  - [ ] Record "vote_submitted" activity in submit_vote()
  - [ ] Record "third_vote_reached" in _update_vote_timeline()
  - [ ] Record "fifth_vote_reached" in _update_vote_timeline()
  - [ ] Record "finalized" activity in _finalize_wordset()

### Schemas
- [ ] Create `backend/schemas/phraseset.py` (if not exists, or add to existing)
  - [ ] PhrasesetSummary schema
  - [ ] PhrasesetListResponse schema
  - [ ] PhrasesetDashboardSummary schema
  - [ ] PhrasesetDetails schema
  - [ ] PhrasesetActivity schema
  - [ ] ClaimPrizeRequest schema
  - [ ] ClaimPrizeResponse schema
  - [ ] UnclaimedResultsResponse schema

### API Endpoints
- [ ] Create new router or add to existing phrasesets router
- [ ] `GET /player/phrasesets` endpoint
  - [ ] Query params: role, status, limit, offset
  - [ ] Authorization check
  - [ ] Call phraseset_service.get_player_phrasesets()
  - [ ] Return filtered list
- [ ] `GET /player/phrasesets/summary` endpoint
  - [ ] Authorization check
  - [ ] Call phraseset_service.get_phraseset_summary()
  - [ ] Return dashboard stats
- [ ] `GET /phrasesets/{phraseset_id}/details` endpoint
  - [ ] Authorization check
  - [ ] Verify contributor access
  - [ ] Call phraseset_service.get_phraseset_details()
  - [ ] Return full details with activity
- [ ] `POST /phrasesets/{phraseset_id}/claim` endpoint
  - [ ] Authorization check
  - [ ] Verify contributor and finalized status
  - [ ] Call phraseset_service.claim_prize()
  - [ ] Return claim response
- [ ] `GET /player/unclaimed-results` endpoint (replaces pending-results)
  - [ ] Authorization check
  - [ ] Query unclaimed result_views
  - [ ] Return unclaimed list
- [ ] Keep `GET /player/pending-results` for backward compatibility

### Unit Tests
- [ ] `tests/test_activity_service.py`
  - [ ] test_record_activity()
  - [ ] test_get_phraseset_activity()
  - [ ] test_get_new_activity_counts()
- [ ] `tests/test_phraseset_service.py`
  - [ ] test_get_player_phrasesets_all()
  - [ ] test_get_player_phrasesets_filter_role()
  - [ ] test_get_player_phrasesets_filter_status()
  - [ ] test_get_phraseset_summary()
  - [ ] test_get_phraseset_details_contributor()
  - [ ] test_get_phraseset_details_non_contributor()
  - [ ] test_claim_prize_success()
  - [ ] test_claim_prize_idempotent()
  - [ ] test_claim_prize_not_finalized()
- [ ] Update existing test files:
  - [ ] `tests/test_round_service.py` - Verify activity recording
  - [ ] `tests/test_vote_service.py` - Verify activity recording

### Integration Tests
- [ ] `tests/test_phraseset_tracking_flow.py`
  - [ ] test_prompt_submission_creates_activity()
  - [ ] test_copy_submission_creates_activity()
  - [ ] test_vote_submission_creates_activity()
  - [ ] test_phraseset_status_transitions()
  - [ ] test_access_control()
  - [ ] test_activity_timeline_order()
  - [ ] test_prize_claiming_flow()
  - [ ] test_complete_lifecycle()

---

## Phase 2: Frontend Foundation ✅

### TypeScript Types
- [ ] Add to `frontend/src/api/types.ts`:
  - [ ] PhrasesetSummary interface
  - [ ] PhrasesetListResponse interface
  - [ ] PhrasesetDashboardSummary interface
  - [ ] PhrasesetDetails interface
  - [ ] PhrasesetActivity interface
  - [ ] PhrasesetContributor interface
  - [ ] PhrasesetVote interface
  - [ ] ClaimResponse interface
  - [ ] UnclaimedResult interface

### API Client
- [ ] Add to `frontend/src/api/client.ts`:
  - [ ] getPlayerPhrasesets(params)
  - [ ] getPhrasesetsSummary()
  - [ ] getPhrasesetDetails(id)
  - [ ] claimPrize(id)
  - [ ] getUnclaimedResults()

### Reusable Components
- [ ] Create `frontend/src/components/StatusBadge.tsx`
  - [ ] Support status types: waiting_copies, waiting_copy1, voting, finalized
  - [ ] Color coding
  - [ ] Icon support
  - [ ] Props: status, count (optional)
- [ ] Create `frontend/src/components/ProgressBar.tsx`
  - [ ] Visual progress indicator
  - [ ] Show markers for 3rd and 5th votes
  - [ ] Props: current, thirdVote, fifthVote, max
- [ ] Create `frontend/src/components/ActivityTimeline.tsx`
  - [ ] Map activity types to icons and labels
  - [ ] Format timestamps
  - [ ] Render metadata
  - [ ] Props: activities
- [ ] Create `frontend/src/components/PhrasesetList.tsx`
  - [ ] List view of phrasesets
  - [ ] Highlight selected
  - [ ] Show status badge
  - [ ] New activity indicator
  - [ ] Props: phrasesets, onSelect, selectedId

---

## Phase 3: Frontend Pages ✅

### New Page: Phraseset Tracking
- [ ] Create `frontend/src/pages/PhrasesetTracking.tsx`
- [ ] Two-column layout (list + details)
- [ ] Filter controls:
  - [ ] Role filter (All/Prompts/Copies)
  - [ ] Status filter (All/In Progress/Voting/Finalized)
- [ ] Left column - Phraseset list:
  - [ ] Use PhrasesetList component
  - [ ] Load on mount
  - [ ] Apply filters
  - [ ] Handle selection
- [ ] Right column - Details panel:
  - [ ] Use PhrasesetDetails component
  - [ ] Load details when selection changes
  - [ ] Poll for updates (every 5-10 seconds)
  - [ ] Handle claim action
- [ ] Empty states
- [ ] Loading states
- [ ] Error handling

### New Component: Phraseset Details
- [ ] Create `frontend/src/components/PhrasesetDetails.tsx`
- [ ] Header section:
  - [ ] Prompt text
  - [ ] Status badge
  - [ ] Your role and phrase
- [ ] Contributors section (if phraseset created):
  - [ ] List all contributors
  - [ ] Highlight yourself
  - [ ] Show phrases
- [ ] Progress section (if voting):
  - [ ] Use ProgressBar component
  - [ ] Show vote count / target
  - [ ] Time remaining if closing
- [ ] Votes section:
  - [ ] Use ActivityTimeline or custom vote list
  - [ ] Show voter, voted phrase, correct/incorrect
- [ ] Results section (if finalized):
  - [ ] Vote breakdown
  - [ ] Payout calculation
  - [ ] Your payout highlighted
  - [ ] Claim button (if unclaimed)
- [ ] Activity timeline:
  - [ ] Use ActivityTimeline component
  - [ ] Show full history
- [ ] Props: phrasesetId, onClaim callback

### Modified Page: Dashboard
- [ ] Add "In Progress" section
  - [ ] Fetch summary on mount
  - [ ] Show prompt count and copy count
  - [ ] "Track Progress" button
  - [ ] Navigate to /phrasesets
- [ ] Modify "Pending Results" section
  - [ ] Rename to "Unclaimed Results"
  - [ ] Use new unclaimed-results endpoint
  - [ ] Show prompt/copy breakdown
  - [ ] Show total unclaimed amount
  - [ ] "Claim Prizes" button
  - [ ] Navigate to /phrasesets?filter=unclaimed
- [ ] Add polling for summary (every 30 seconds)

### Modified Page: Results (or merge with tracking)
- [ ] Option A: Keep as separate "Claim Results" page
  - [ ] Focus only on unclaimed
  - [ ] Big claim buttons
  - [ ] Link to full tracking page
- [ ] Option B: Redirect to tracking page with unclaimed filter
- [ ] Decide which approach and implement

### Routing
- [ ] Add route `/phrasesets` in App.tsx
- [ ] Add route `/phrasesets/:id` (optional detail page)
- [ ] Update navigation from dashboard

---

## Phase 4: Polish & Testing ✅

### Component Tests
- [ ] StatusBadge.test.tsx
- [ ] ProgressBar.test.tsx
- [ ] ActivityTimeline.test.tsx
- [ ] PhrasesetList.test.tsx
- [ ] PhrasesetDetails.test.tsx

### Page Tests
- [ ] PhrasesetTracking.test.tsx
- [ ] Dashboard updates test
- [ ] Results page test

### E2E Tests
- [ ] Create `tests/e2e/test_phraseset_tracking.py` (or similar)
- [ ] Test complete flow:
  - [ ] Player 1 submits prompt
  - [ ] Navigate to tracking page
  - [ ] Verify prompt appears
  - [ ] Player 2 submits copy
  - [ ] Verify activity updates for Player 1
  - [ ] Player 3 submits second copy
  - [ ] Verify phraseset active
  - [ ] Players vote
  - [ ] Verify vote timeline
  - [ ] Phraseset finalizes
  - [ ] Player 1 claims prize
  - [ ] Verify balance updated

### Performance Testing
- [ ] Benchmark activity queries
- [ ] Test with large datasets (100+ phrasesets)
- [ ] Verify polling doesn't cause issues
- [ ] Check bundle size impact
- [ ] Test on mobile devices

### UI/UX Polish
- [ ] Responsive design (mobile, tablet, desktop)
- [ ] Loading skeletons
- [ ] Empty state illustrations
- [ ] Error messages clear and helpful
- [ ] Animations for state transitions
- [ ] Accessibility (keyboard nav, screen readers)
- [ ] Color contrast compliance

---

## Phase 5: Documentation ✅

### API Documentation
- [ ] Update `docs/API.md`
  - [ ] Document all new endpoints
  - [ ] Add request/response examples
  - [ ] Update TypeScript types
  - [ ] Add error codes

### Frontend Documentation
- [ ] Update `docs/FRONTEND_PLAN.md`
  - [ ] Add new pages and components
  - [ ] Update routing table
  - [ ] Add polling strategy

### Architecture Documentation
- [ ] Update `docs/ARCHITECTURE.md`
  - [ ] Add activity tracking system
  - [ ] Update state machine diagrams
  - [ ] Add new service descriptions

### Database Documentation
- [ ] Update `docs/DATA_MODELS.md`
  - [ ] Document phraseset_activity table
  - [ ] Update rounds table schema
  - [ ] Update result_views table schema

### User Guide
- [ ] Create `docs/USER_GUIDE_TRACKING.md`
  - [ ] How to track your phrasesets
  - [ ] Understanding the timeline
  - [ ] How to claim prizes
  - [ ] Screenshots/examples

### README
- [ ] Update main README.md
  - [ ] Add tracking feature to feature list
  - [ ] Update screenshots if applicable

---

## Phase 6: Deployment ✅

### Pre-deployment
- [ ] Review all code changes
- [ ] Run full test suite
- [ ] Test migration on staging database
- [ ] Backup production database
- [ ] Create rollback plan

### Deployment Steps
- [ ] Deploy backend:
  - [ ] Run migrations
  - [ ] Deploy new code
  - [ ] Verify health check
  - [ ] Test new endpoints
- [ ] Deploy frontend:
  - [ ] Build production bundle
  - [ ] Deploy to hosting
  - [ ] Verify all pages load
  - [ ] Test tracking page

### Post-deployment
- [ ] Monitor error rates
- [ ] Check performance metrics
- [ ] Verify activity recording works
- [ ] Test claim flow end-to-end
- [ ] Monitor user engagement

### Rollback Plan (if needed)
- [ ] Frontend: Revert to previous build
- [ ] Backend: Revert code (new endpoints won't be called)
- [ ] Database: Keep migration (backward compatible)

---

## Quick Start Checklist

### Minimum Viable Implementation (1 week spike)

**Backend (2 days):**
- [ ] Add phraseset_activity table
- [ ] Basic ActivityService (record + query)
- [ ] One endpoint: GET /player/phrasesets
- [ ] Record activities in existing services
- [ ] Basic tests

**Frontend (2 days):**
- [ ] StatusBadge component
- [ ] Basic tracking page (list only, no details)
- [ ] Dashboard "In Progress" section
- [ ] Wire up API

**Testing (1 day):**
- [ ] Integration test of full flow
- [ ] Manual testing

This gives you a working prototype to validate the concept before full implementation.

---

## Notes & Tips

### Development Order
1. Start with database and models (foundation)
2. Build services and test them in isolation
3. Add API endpoints and test with curl/Postman
4. Build frontend components in Storybook (optional)
5. Integrate frontend components into pages
6. E2E testing
7. Polish and documentation

### Testing Strategy
- Write tests BEFORE implementing complex logic
- Use fixtures for common test scenarios
- Test happy path + error cases + edge cases
- Integration tests more valuable than unit tests for this feature

### Performance Considerations
- Add database indexes FIRST, test THEN
- Consider caching phraseset summary in Redis
- Batch API calls where possible
- Use pagination for large lists
- Lazy load activity timeline

### Common Pitfalls
- **Forgetting to record activities** - Add to service methods, not endpoints
- **Access control bugs** - Always verify contributor before showing details
- **Timezone issues** - Use UTC everywhere, format on frontend
- **Race conditions** - Use database transactions for claim flow
- **Stale data** - Implement proper polling or WebSockets

---

**Estimated Total Time:** 100-150 hours (~3 weeks)

**Priority:** High - Significantly improves user engagement and transparency

**Risk:** Low - All additive changes, can be feature-flagged
