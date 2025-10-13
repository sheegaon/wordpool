# Results Tracking Feature - Executive Summary

## What This Feature Does

Enables players to track their prompt and copy submissions throughout the entire game lifecycle - from submission through voting to final results and prize claiming.

## Current Problems

1. **Zero visibility** - Players can't see their submissions until voting is 100% complete
2. **No progress tracking** - Can't tell when copies arrive or how voting is progressing
3. **Mysterious prizes** - Money appears in account without clear indication of where it came from
4. **No attribution** - Can't see who copied your prompt or who voted

## What Players Will See

### Dashboard Updates
- **In Progress Section** - Shows active phrasesets
  - "5 prompts waiting for copies/votes"
  - "3 copies waiting for votes"
- **Unclaimed Prizes** - Clear call-to-action
  - "2 results ready - $125 to claim"
  - Separated by role (prompts vs copies)

### New Phraseset Tracking Page

Two-column layout with filtering:

**Left Column** - List of all your phrasesets
- Filter by role (prompts/copies)
- Filter by status (in-progress/voting/finalized)
- Shows prompt text, your phrase, status badge
- New activity indicators

**Right Column** - Detailed phraseset view
- Full prompt and all three phrases
- Contributors (who wrote each phrase)
- Complete voting timeline
- Who voted and what they voted for
- Prize calculation breakdown
- Big "Claim Prize" button when ready

### Example Timeline View

```
🎯 Prompt Created
   Player1 • 2 minutes ago

📝 Copy Submitted
   Player2 submitted "MONEY" • 1 minute ago

📝 Copy Submitted
   Player3 submitted "CONTENTMENT" • 30 seconds ago
   → Phraseset active, voting started

🗳️ Vote Received
   Voter1 voted for "LOVE" ✓ • 10 seconds ago

🗳️ Vote Received
   Voter2 voted for "MONEY" ✗ • 5 seconds ago

... 8 total votes ...

✅ Finalized
   Your payout: $62 • Claim now
```

## Technical Implementation

### Backend Changes

**New Database Table:**
- `phraseset_activity` - Records every state change

**New API Endpoints:**
- `GET /player/phrasesets` - List all your phrasesets with filters
- `GET /player/phrasesets/summary` - Dashboard stats
- `GET /phrasesets/{id}/details` - Full phraseset details with timeline
- `POST /phrasesets/{id}/claim` - Explicitly claim prize

**New Service:**
- `ActivityService` - Records and queries phraseset events
- `PhrasesetService` - Manages phraseset queries and access control

### Frontend Changes

**New Pages:**
- Phraseset Tracking page (`/phrasesets`)

**New Components:**
- `StatusBadge` - Visual status indicators
- `ProgressBar` - Voting progress visualization
- `ActivityTimeline` - Event feed
- `PhrasesetList` - Filterable list
- `PhrasesetDetails` - Detailed view with claim button

**Modified Pages:**
- Dashboard - Add in-progress and unclaimed sections
- Results - Simplify to focus on claiming

## User Flows

### Scenario 1: Track Your Prompt

1. Submit prompt for "my deepest desire is to be (a/an)"
2. Dashboard shows "1 prompt in progress"
3. Click "Track Progress" → See prompt with status "Waiting for copies (0/2)"
4. First copy arrives → Notification badge, status updates to "Waiting for copies (1/2)"
5. Second copy arrives → Status changes to "Voting in progress (0 votes)"
6. Votes arrive → See each vote in timeline, progress bar fills
7. After 10 votes → Status "Finalized", see results and "Claim $62" button
8. Click claim → Balance updates, button shows "Claimed ✓"

### Scenario 2: Check Your Copy

1. Submit copy phrase "POPULAR"
2. See phraseset in tracking page with status "Voting in progress"
3. See the prompt (revealed after you submit)
4. See the other copy player's phrase
5. Watch votes come in real-time
6. See final tally and your $93 payout
7. Claim prize

## Key Design Decisions

### 1. Full Transparency
- Show all voter names and votes
- Show copy player identities
- Complete audit trail

### 2. Explicit Prize Claiming
- Keep auto-claim on first view (backward compatible)
- Add explicit "Claim" button for clarity
- Show claim confirmation

### 3. Real-time via Polling
- Poll every 5-10 seconds on tracking page
- WebSockets deferred to Phase 2

### 4. Progressive Disclosure
- Copy players don't see prompt until they submit
- Full phraseset details only for contributors
- Activity timeline shows everything once accessible

## Open Questions for User Input

### Q1: Should voters be anonymous?
**Option A:** Show "Voter1 voted for LOVE ✓"
**Option B:** Show "Someone voted for LOVE ✓" (anonymous)
**Option C:** Show only final tallies, not individual votes

*Recommendation: Option A (full transparency)*

### Q2: When should copy players see the prompt?
**Option A:** After they submit their copy
**Option B:** Never (keep them blind)
**Option C:** After voting starts

*Recommendation: Option A (reveal after submit)*

### Q3: Auto-claim or explicit claim?
**Option A:** Auto-claim on view (current behavior)
**Option B:** Require explicit click to claim
**Option C:** Auto-claim but show big confirmation

*Recommendation: Option C (auto with confirmation)*

## Implementation Timeline

### Week 1: Backend
- Database schema and migration
- New services (ActivityService, PhrasesetService)
- API endpoints
- Unit tests

### Week 2: Frontend Foundation
- New components (StatusBadge, ProgressBar, ActivityTimeline)
- API client updates
- TypeScript types

### Week 3: Frontend Integration
- Phraseset tracking page
- Dashboard updates
- Integration and E2E tests
- Polish and bug fixes

**Total Estimate: 3 weeks (~100-150 hours)**

## Success Metrics

### Engagement
- % of players who visit tracking page
- Average time spent tracking phrasesets
- Return visit frequency

### Usability
- % of unclaimed prizes after 24 hours (should decrease)
- % of players who claim all available prizes (should increase)
- Support tickets about missing prizes (should decrease)

### Performance
- Tracking page load time < 1 second
- Activity queries < 200ms
- Real-time polling doesn't impact server

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Performance degradation from activity logging | Add indexes, benchmark queries, consider async logging |
| Users overwhelmed by too much info | Progressive disclosure, clear visual hierarchy |
| Privacy concerns about voter attribution | Make voter display configurable (Phase 2) |
| Backward compatibility breaks | All changes are additive, keep old endpoints |

## Future Enhancements (Phase 2+)

1. **Notifications** - Push/email when state changes
2. **WebSockets** - True real-time updates
3. **Analytics** - Personal stats dashboard
4. **Social** - Comment on phrasesets, share results
5. **Batch Actions** - "Claim All" button
6. **Advanced Filters** - Search, date range, sort options

## Appendix: Visual Mockups

### Dashboard - In Progress Section
```
┌─────────────────────────────────────────────┐
│ Phrasesets In Progress                      │
│                                             │
│ 5 prompts waiting • 3 copies voting         │
│                                             │
│                    [Track Progress →]       │
└─────────────────────────────────────────────┘
```

### Dashboard - Unclaimed Results
```
┌─────────────────────────────────────────────┐
│ Results Ready to Claim! 🎉                  │
│                                             │
│ 2 prompts • 1 copy • $125 total             │
│                                             │
│                    [Claim Prizes →]         │
└─────────────────────────────────────────────┘
```

### Tracking Page Layout
```
┌──────────────┬─────────────────────────────┐
│ Filters:     │ Prompt: my deepest desire   │
│ ○ All        │                             │
│ ● Prompts    │ Status: 🗳️ Voting (8 votes)│
│ ○ Copies     │                             │
│              │ Your Role: Prompt           │
│ ─────────    │ Your Phrase: LOVE           │
│              │                             │
│ [Prompt 1]   │ Contributors:               │
│ my deepest   │ • You - LOVE                │
│ 🗳️ 8 votes   │ • Player2 - MONEY           │
│              │ • Player3 - CONTENTMENT     │
│ [Prompt 2]   │                             │
│ the secret   │ Activity Timeline:          │
│ ✅ Finalized │ 🗳️ Voter1 → LOVE ✓         │
│              │ 🗳️ Voter2 → MONEY ✗        │
│ [Copy 1]     │ ... 6 more votes ...        │
│ happiness    │                             │
│ ✅ Claim $93 │ [Claim $62 Prize]           │
└──────────────┴─────────────────────────────┘
```

## Next Steps

1. **Review** this design document
2. **Answer** the open questions
3. **Approve** scope and timeline
4. **Begin** implementation Phase 1 (backend)

---

**Full Technical Specification:** See [RESULTS_TRACKING_FEATURE.md](./RESULTS_TRACKING_FEATURE.md)
