# Implementation Plan

## Implementation Priorities

### Phase 1 - MVP (Core Gameplay)
1. Player accounts and authentication
2. Balance management and transactions
3. Core game loop (prompt, copy, vote)
4. Word validation (NASPA list)
5. Queue system (basic FIFO)
6. Scoring and payouts
7. One-round-at-a-time enforcement
8. Results viewing and prize collection
9. Essential API endpoints

### Phase 2 - Economic Balance
1. Daily login bonus
2. Copy discount when queue > 10
3. System contribution tracking
4. Queue depth visibility
5. Transaction history
6. Balance safeguards

### Phase 3 - Polish & UX
1. Improved error messages
2. Round history and statistics
3. Better queue management UI
4. Performance optimization
5. Mobile responsiveness

### Phase 4 - Engagement Features
1. Player statistics and win rates
2. Leaderboards
3. Achievement system
4. Social features (friends, challenges)
5. Premium prompts
6. Seasonal events

---

## Testing Considerations

### Load Testing Scenarios
1. **Queue Imbalance**: Simulate 100 prompt players, 10 copy players
2. **Voting Rush**: 20 voters hitting same word set simultaneously
3. **Grace Period**: Submissions arriving 1-6 seconds after expiry
4. **Copy Discount**: Toggle when queue crosses 10 threshold

### Edge Cases to Test
1. Player disconnects mid-round, reconnects
2. Two copy players submit identical words (both should be rejected for duplicate)
3. Word set receives exactly 3 votes and sits for 10 minutes
4. Word set receives 5 votes immediately (should trigger 60s window)
5. 20 voters queue up simultaneously (should cap at 20)
6. Player balance exactly $100 or $1 (boundary conditions)
7. Daily bonus at midnight boundary
8. Clock skew between client and server

### Economic Testing
1. Monitor average earnings by role (prompt/copy/voter)
2. Track queue wait times
3. Measure copy discount activation frequency
4. Validate prize pool math (should always sum correctly)
5. Detect economic exploits or imbalances

---

## Security Considerations

### Authentication & Authorization
- JWT tokens or session-based auth
- Validate player_id matches authenticated user on all endpoints
- Rate limiting on all endpoints (especially vote to prevent spam)

### Anti-Cheat Measures
- Server-side timer validation (grace period but not exploitable)
- Prevent self-voting (check contributor IDs)
- Prevent duplicate voting (one vote per word set per player)
- Word validation server-side only (don't trust client)
- Transaction validation (ensure balance sufficient before deducting)

### Data Integrity
- Atomic transactions for balance updates
- Idempotent prize

---

## Monitoring & Analytics

### Key Metrics to Track

**Economic Metrics:**
- Average payout by role (prompt/copy/voter)
- Win rate by role
- Player balance distribution
- Daily bonus claim rate
- Copy discount activation frequency
- Rake collected vs. prizes distributed

**Queue Health:**
- Prompts waiting for copies (alert if >20)
- Word sets waiting for votes (alert if >50)
- Average wait time: prompt → first copy
- Average wait time: word set creation → 3 votes
- Average wait time: 3 votes → finalization

**Player Engagement:**
- Daily active users
- Average rounds per player per day
- Round type distribution (prompt/copy/vote %)
- Retention: D1, D7, D30
- Churn: players reaching $0 balance

**Performance:**
- API response times (p50, p95, p99)
- Failed submissions (by error type)
- Grace period usage frequency
- Timeout/abandonment rate by round type

**Game Balance:**
- Voter accuracy (% correct votes)
- Original vs. copy win rates
- Word similarity quality (measured by vote distribution)
- Most/least profitable prompts

### Alerts to Configure
1. Queue imbalance: >20 prompts waiting
2. Economic imbalance: any role avg payout <$80 over 1000 rounds
3. Low voter participation: <3 votes per word set avg
4. High abandonment: >20% timeout rate
5. Server errors: >1% of requests failing
6. Balance depletion: >10% of active players under $100

---

## Future Enhancements (Post-MVP)

### Gameplay Additions
1. **Difficulty Tiers**: Easy/Medium/Hard prompts with adjusted payouts
2. **Themed Rounds**: Holiday, pop culture, or category-specific prompts
3. **Team Mode**: 2v2 copy rounds with shared payouts
4. **Streak Bonuses**: Consecutive correct votes earn multipliers
5. **Power-ups**: "See one copy's vote distribution" for $10
6. **Speed Bonuses**: Submit within 10 seconds for extra points

### Economic Features
1. **Subscription**: $10/month for no rake on votes, daily $200 bonus
2. **Tournaments**: Weekly competitions with prize pools
3. **Referral Bonuses**: $50 for each friend who joins
4. **Bundle Pricing**: Buy 10 prompt rounds for $900
5. **Dynamic Rake**: Lower rake during off-peak hours

### Social Features
1. **Friends System**: See friends' activity, challenge them
2. **Chat**: Post-round discussion of word choices
3. **Leaderboards**: Daily/weekly/all-time top earners
4. **Replay Sharing**: Share interesting word sets on social media
5. **Spectator Mode**: Watch live rounds (no voting)

### Advanced Matching
1. **Skill-Based Matching**: Match similar-skill copy players
2. **ELO Ratings**: Track player skill, display ranks
3. **Ranked Mode**: Competitive ladder with seasons
4. **Private Rooms**: Create custom games with friends

### Analytics for Players
1. **Personal Stats**: Win rates, favorite prompts, earnings over time
2. **Word History**: All words you've played, which got most votes
3. **Insights**: "Your copies fool voters 65% of the time"
4. **Achievements**: "Voted correctly 50 times in a row"

### Content Management
1. **User-Submitted Prompts**: Community creates prompts (moderated)
2. **Prompt Voting**: Rate prompts, promote good ones
3. **Seasonal Rotations**: Fresh prompt sets every month
4. **Banned Words**: Block inappropriate or problematic words
5. **Word of the Day**: Featured prompt with bonus payouts

---

## Database Indexes

### Suggested Indexes for Performance

**Players Table:**
- `player_id` (primary key)
- `active_round_id` (for checking one-at-a-time constraint)
- `last_login_date` (for daily bonus queries)

**Rounds Table (Prompt/Copy):**
- `round_id` (primary key)
- `player_id` (for user's round history)
- `status, created_at` (composite, for queue queries)
- `expires_at` (for timeout cleanup jobs)
- `prompt_round_id` (for copy rounds, linking to original)

**Word Sets Table:**
- `wordset_id` (primary key)
- `status, vote_count` (composite, for voting queue)
- `third_vote_at, fifth_vote_at` (for timeline calculations)
- `prompt_round_id, copy_round_1_id, copy_round_2_id` (for linking)

**Votes Table:**
- `vote_id` (primary key)
- `wordset_id` (for aggregating votes)
- `player_id, wordset_id` (composite unique, prevent duplicate voting)
- `created_at` (for vote timeline tracking)

**Transactions Table:**
- `transaction_id` (primary key)
- `player_id, created_at` (composite, for transaction history)
- `type` (for filtering by transaction type)
- `reference_id` (for linking to rounds/wordsets)

**Result Views Table:**
- `player_id, wordset_id` (composite unique, for idempotent collection)
- `payout_collected` (for finding pending results)

---

### Visual Design Principles
1. **Clear Timers**: Large, visible countdown with color coding (green >30s, yellow 10-30s, red <10s)
2. **Cost Transparency**: Always show costs and potential earnings upfront
3. **Queue Visibility**: Show how many prompts/word sets are waiting
4. **Progress Indicators**: Show round status (submitted, waiting for results)
5. **Celebratory Feedback**: Animations for wins, uplifting messages
6. **Loss Mitigation**: Frame losses gently ("Better luck next time! Only -$1")
7. **Discount Highlighting**: Make $90 copy rounds visually prominent with badges

---

## Launch Checklist

### Pre-Launch Testing
- [ ] Load test with 1000 concurrent users
- [ ] Verify queue management under stress
- [ ] Test all timeout/abandonment scenarios
- [ ] Validate scoring math across 100+ word sets
- [ ] Test grace period edge cases
- [ ] Verify daily bonus logic across date boundaries
- [ ] Test copy discount activation/deactivation
- [ ] Security audit (SQL injection, XSS, auth bypass)
- [ ] Mobile browser compatibility (iOS Safari, Android Chrome)
- [ ] Network disconnection recovery testing

### Launch Day Prep
- [ ] Database backups automated
- [ ] Monitoring dashboards configured
- [ ] Alert thresholds set
- [ ] Customer support scripts prepared
- [ ] FAQ page published
- [ ] Terms of service and privacy policy finalized
- [ ] Payment processing (if real money) tested and certified
- [ ] Rate limiting tuned
- [ ] CDN configured for static assets
- [ ] Logging infrastructure ready

### Week 1 Monitoring
- [ ] Track queue balance hourly
- [ ] Monitor economic metrics daily
- [ ] Review player feedback and bug reports
- [ ] Adjust copy discount threshold if needed
- [ ] Watch for exploits or gaming patterns
- [ ] Measure voter accuracy and adjust point ratios if needed
- [ ] Track timeout/abandonment rates
- [ ] Ensure prize pools always balance correctly