# Frontend Implementation Plan

## Overview

This document provides high-level guidance for implementing a WordPool frontend. The backend API is complete and documented in [API.md](API.md). This plan focuses on the minimum viable frontend and logical phasing.

---

## Phase 1: MVP Frontend (Core Gameplay)

### Essential Screens

1. **Landing / Authentication**
   - Create new player (POST /player) → receive API key
   - API key input for returning players
   - Store API key securely (localStorage/sessionStorage)

2. **Dashboard / Home**
   - Display current balance
   - Show daily bonus notification if available
   - Display active round status (if any)
   - Notification badge for pending results
   - Round selection buttons (Prompt / Copy / Vote)
   - Button state based on availability (GET /rounds/available)

3. **Prompt Round**
   - Display prompt text
   - Text input for word submission
   - Countdown timer (3 minutes / 180 seconds)
   - Submit button (disabled after timeout)
   - Validation feedback

4. **Copy Round**
   - Display original phrase to copy
   - Display cost (\$100 or \$90 if discount)
   - Text input for copy word
   - Countdown timer (3 minutes / 180 seconds)
   - Submit button with duplicate detection feedback

5. **Vote Round**
   - Display prompt text
   - Three word buttons (randomized order)
   - Countdown timer (60 seconds, visual urgency at <10s)
   - Immediate feedback after vote (correct/incorrect, payout)

6. **Results View**
   - Display prompt text
   - Show all three words with vote counts
   - Highlight original phrase
   - Show your word, role, points, and payout
   - "Collected" indicator for already-viewed results
   - List of pending results (from GET /player/pending-results)

### Core Components

**Timer Component**
- Calculate remaining time from `expires_at` timestamp
- Update every second
- Visual states: normal → warning (10s) → urgent (5s) → expired
- Don't show grace period to users

**Balance Display**
- Show current balance prominently
- Update after each action
- Animate on changes

**Round State Manager**
- Poll GET /player/current-round on app load
- Resume active round if exists
- Handle reconnection gracefully

**Error Handler**
- Map API error codes to user-friendly messages
- Show retry options for network errors
- Handle insufficient balance → suggest daily bonus

### State Management

**Required Global State:**
- `apiKey` (persisted)
- `balance` (from GET /player/balance)
- `activeRound` (from GET /player/current-round)
- `pendingResults` (from GET /player/pending-results)
- `roundAvailability` (from GET /rounds/available)

**Polling Strategy:**
- Balance/status: Every 30s or after actions
- Current round: Every 5s during active round
- Pending results: Every 60s in idle state
- Round availability: Every 10s in idle state

### User Flow

```
1. First visit → Create player → Store API key → Dashboard
2. Return visit → Load API key → GET /player/balance → Dashboard
3. Dashboard → Check daily bonus → Claim if available
4. Dashboard → Check active round → Resume if exists
5. Dashboard → Select round type → Start round
6. In round → Submit word → Return to dashboard
7. Dashboard → Notification badge → View results
```

---

## Phase 2: Polish & User Experience

### Enhanced Features

1. **Transaction History**
   - List of recent transactions with types and amounts
   - Filter by type (earnings, costs, bonuses)
   - Running balance column

2. **Improved Round Selection**
   - Show queue depths (X prompts waiting, Y wordsets waiting)
   - Copy discount badge when active
   - Estimated wait time hints
   - "Coming soon" for unavailable round types

3. **Enhanced Results**
   - Visual chart/graph of vote distribution
   - Breakdown of payout calculation
   - Share results feature
   - History of past results

4. **Settings / Account**
   - API key rotation
   - Export transaction history
   - Game statistics preview

5. **Better Error Handling**
   - Graceful offline mode
   - Reconnection handling with state preservation
   - Clear error messages with suggested actions

6. **Loading States**
   - Skeleton screens
   - Loading indicators
   - Optimistic updates

### UX Improvements

- Animations on balance changes
- Sound effects (optional, user toggle)
- Haptic feedback on mobile
- Dark mode support
- Tutorial/onboarding flow
- Keyboard shortcuts
- Accessibility (ARIA labels, keyboard navigation)

---

## Phase 3: Advanced Features

### Player Statistics Dashboard
- Win rate by role (prompt/copy/voter)
- Total earnings over time
- Favorite prompt categories
- Average points per contribution
- Success streak tracking

### Social Features
- Leaderboards (daily/weekly/all-time)
- Achievement badges
- Share results to social media
- Friend system (if backend supports)

### Premium Experience
- Progressive Web App (PWA)
- Push notifications for results ready
- Offline caching
- Native mobile apps (React Native / Flutter)

### Real-time Updates
- WebSocket connection for live updates (requires backend Phase 3)
- Live vote counts as they come in
- Real-time queue depth changes
- Instant result notifications

---

## Technical Considerations

### Framework Recommendations

**Web:**
- React / Next.js (most popular, good ecosystem)
- Vue / Nuxt (simpler learning curve)
- Svelte / SvelteKit (performance-focused)

**Mobile:**
- React Native (cross-platform, shares code with web)
- Flutter (high performance, native feel)
- Native iOS/Android (best UX, more effort)

### State Management Options

**Simple (MVP):**
- React Context API
- Vue Composition API
- Svelte stores

**Advanced (Phase 2+):**
- Redux Toolkit (React)
- Pinia (Vue)
- Zustand (lightweight, React)

### API Client

Create a typed API client using the TypeScript definitions in [API.md](API.md#frontend-integration). Consider:
- Axios or Fetch API wrapper
- Automatic retry logic
- Request/response interceptors for API key injection
- Error transformation to user-friendly messages

### Offline Strategy

**Phase 1:**
- Show error message when offline
- Preserve API key in storage

**Phase 2+:**
- Queue actions for later submission
- Cache recent results
- Service worker for PWA

---

## Testing Strategy

### Phase 1 Testing

**Manual Testing:**
- Complete game flow (prompt → copy → vote → results)
- Timer expiration handling
- Error scenarios (insufficient balance, invalid words)
- Reconnection after disconnect

**Automated Testing:**
- API client unit tests
- Component tests for timer logic
- Integration tests for critical flows
- E2E tests for happy path

### Phase 2+ Testing

- Visual regression testing
- Performance testing (bundle size, load time)
- Accessibility audits
- Cross-browser testing
- Mobile device testing

---

## Deployment

### Phase 1 MVP
- Static hosting (Vercel, Netlify, GitHub Pages)
- Environment variables for API URL
- CORS configuration with backend
- HTTPS required for API key security

### Phase 2+
- CDN for assets
- Analytics integration
- Error tracking (Sentry)
- Performance monitoring

---

## Design Guidelines

### Visual Hierarchy
- Balance and timer should be most prominent
- Clear call-to-action buttons
- Consistent color coding (green=success, red=error, blue=info)

### Responsive Design
- Mobile-first approach
- Touch-friendly tap targets (minimum 44x44px)
- Readable font sizes (minimum 16px)
- Landscape and portrait support

### Performance
- Minimize bundle size
- Lazy load routes
- Optimize images
- Debounce API calls

### Accessibility
- Semantic HTML
- ARIA labels for interactive elements
- Keyboard navigation support
- Screen reader friendly
- Color contrast ratios (WCAG AA minimum)

---

## Development Workflow

### Phase 1 Priorities (Week 1-2)
1. Set up project structure and routing
2. Implement authentication flow
3. Create dashboard with round selection
4. Build prompt/copy/vote round components
5. Implement timer logic
6. Add results viewing
7. Polish error handling and edge cases

### Phase 2 Priorities (Week 3-4)
1. Add transaction history
2. Improve loading states
3. Add animations and transitions
4. Implement settings/account page
5. Add offline handling
6. Accessibility improvements

### Phase 3+ (Post-MVP)
- Statistics dashboard
- Social features
- PWA conversion
- Mobile apps
- Real-time features

---

## API Integration Checklist

**Authentication:**
- ✅ POST /player (create account)
- ✅ Store API key securely
- ✅ Include X-API-Key header in all requests
- ✅ Handle 401 errors (invalid key)

**Player Management:**
- ✅ GET /player/balance
- ✅ POST /player/claim-daily-bonus
- ✅ GET /player/current-round
- ✅ GET /player/pending-results
- ⏸️ POST /player/rotate-key (Phase 2)

**Round Management:**
- ✅ GET /rounds/available
- ✅ POST /rounds/prompt
- ✅ POST /rounds/copy
- ✅ POST /rounds/vote
- ✅ POST /rounds/{round_id}/submit
- ⏸️ GET /rounds/{round_id} (Phase 2 - for history)

**Voting & Results:**
- ✅ POST /wordsets/{wordset_id}/vote
- ✅ GET /wordsets/{wordset_id}/results

---

## Success Metrics

### Phase 1 (MVP)
- Users can complete full game flow without confusion
- <2 second response time for API calls
- 90%+ uptime
- Zero critical bugs in production

### Phase 2+
- Average session length > 5 minutes
- Daily active user retention > 30%
- <1% error rate on API calls
- Lighthouse score > 90

---

## Common Pitfalls to Avoid

1. **Timer Sync Issues**
   - Always calculate from server `expires_at`, not client-side countdown
   - Account for network latency
   - Don't trust client time

2. **Race Conditions**
   - Handle rapid button clicks (disable while processing)
   - Optimistic updates with rollback on error
   - Check current round state before starting new round

3. **State Staleness**
   - Refresh balance after every transaction
   - Poll for round availability changes
   - Handle concurrent session detection (if needed)

4. **API Key Security**
   - Never log API keys
   - Clear from memory on logout
   - Don't expose in URLs
   - Use HTTPS only

5. **Error Handling**
   - Always handle network errors gracefully
   - Provide actionable error messages
   - Allow retry for transient failures
   - Distinguish between client and server errors

---

## Next Steps

1. **Choose your framework** - React, Vue, or Svelte
2. **Set up project** - Use create-react-app, Vite, or Next.js
3. **Create API client** - TypeScript wrapper around fetch/axios
4. **Build authentication** - Landing page + API key storage
5. **Implement dashboard** - Balance display + round selection
6. **Add round screens** - Prompt → Copy → Vote
7. **Build results view** - Vote breakdown + payout display
8. **Test full flow** - End-to-end user journey
9. **Deploy** - Static hosting with environment config
10. **Iterate** - Gather feedback and improve

See [API.md](API.md) for complete API reference and [MVP_SUMMARY.md](MVP_SUMMARY.md) for backend status.
