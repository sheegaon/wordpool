# WordPool Frontend

React + TypeScript frontend for the WordPool word association game.

## Features

### Phase 1 MVP (Complete)

- ✅ Player authentication with API key
- ✅ Dashboard with balance display
- ✅ Daily bonus claiming
- ✅ Three round types (Prompt, Copy, Vote)
- ✅ Real-time countdown timers
- ✅ Results viewing with vote breakdown
- ✅ Responsive design with Tailwind CSS
- ✅ Error handling and notifications
- ✅ Automatic state polling and updates
- ✅ Robust request cancellation (no memory leaks)

### Recent Improvements

See [IMPROVEMENTS.md](IMPROVEMENTS.md) and [STABLE_VERSIONS.md](STABLE_VERSIONS.md) for detailed documentation on:
- **AbortController Integration:** Proper cancellation of in-flight requests on component unmount
- **Memory Leak Prevention:** No more React warnings about setting state on unmounted components
- **Stable Package Versions:** Downgraded to production-ready versions (React 18, Tailwind 3, Vite 5)
- **Better Performance:** 22% smaller bundle size, unnecessary network requests canceled immediately

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **React Router** - Navigation
- **Axios** - HTTP client
- **Tailwind CSS** - Styling
- **Context API** - State management

## Prerequisites

- Node.js 18+ and npm
- Backend API running at `http://localhost:8000` (or configured URL)

## Installation

```bash
# Install dependencies
npm install

# Create environment file (optional)
cp .env.example .env

# Edit .env if backend is not on localhost:8000
# VITE_API_URL=http://localhost:8000
```

## Development

```bash
# Start development server
npm run dev

# The app will be available at http://localhost:5173
```

## Build

```bash
# Build for production
npm run build

# Preview production build
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── api/              # API client and TypeScript types
│   │   ├── client.ts     # Axios-based API client
│   │   └── types.ts      # TypeScript interfaces
│   ├── components/       # Reusable components
│   │   ├── ErrorNotification.tsx
│   │   └── Timer.tsx
│   ├── contexts/         # React Context for state management
│   │   └── GameContext.tsx
│   ├── hooks/            # Custom React hooks
│   │   └── useTimer.ts
│   ├── pages/            # Screen components
│   │   ├── Landing.tsx
│   │   ├── Dashboard.tsx
│   │   ├── PromptRound.tsx
│   │   ├── CopyRound.tsx
│   │   ├── VoteRound.tsx
│   │   └── Results.tsx
│   ├── App.tsx           # Main app component with routing
│   ├── main.tsx          # Entry point
│   └── index.css         # Global styles
├── public/               # Static assets
├── .env                  # Environment variables
└── package.json
```

## API Integration

The frontend connects to the backend API using the `apiClient` in `src/api/client.ts`.

### Environment Variables

- `VITE_API_URL` - Backend API URL (default: `http://localhost:8000`)

### Authentication

API keys are stored in `localStorage` and automatically included in all requests via request interceptors.

### State Management

The `GameContext` manages global state:
- Player balance and info
- Active round state
- Pending results
- Round availability

### Polling Strategy

- Balance: Every 30 seconds
- Current round: Every 5 seconds (when active)
- Pending results: Every 60 seconds
- Round availability: Every 10 seconds (when idle)

## User Flow

1. **Landing Page** - Create account or login with existing API key
2. **Dashboard** - View balance, claim bonus, select round type
3. **Round Screens** - Complete prompt/copy/vote rounds with timers
4. **Results** - View finalized wordsets and collect payouts

## Key Components

### Timer Component
- Real-time countdown from server `expires_at` timestamp
- Visual states: normal (blue) → warning (yellow) → urgent (red/pulsing)
- Automatically disables submission when expired

### GameContext
- Centralized state management
- Automatic polling for updates
- Error handling and notifications
- API key persistence

### Round Pages
- **PromptRound** - Submit word for creative prompt
- **CopyRound** - Submit similar word without seeing prompt
- **VoteRound** - Identify original word from three options
- **Results** - View vote breakdown and payouts

## Error Handling

- API errors are transformed to user-friendly messages
- Error notifications auto-dismiss after 5 seconds
- Invalid API keys trigger automatic logout
- Network errors prompt retry suggestions
- **Request cancellation:** AbortController integration prevents memory leaks and React warnings (see [IMPROVEMENTS.md](IMPROVEMENTS.md))

## Styling

Uses Tailwind CSS utility classes for:
- Responsive layouts (mobile-first)
- Color-coded round types
- Interactive button states
- Gradient backgrounds
- Loading states

## Future Enhancements (Phase 2+)

See [FRONTEND_PLAN.md](../docs/FRONTEND_PLAN.md) for planned features:
- Transaction history
- Enhanced statistics
- Settings/account page
- Progressive Web App (PWA)
- Push notifications
- Dark mode
- Accessibility improvements

## Troubleshooting

### Backend not connecting
- Ensure backend is running at the configured `VITE_API_URL`
- Check browser console for CORS errors
- Verify API key is valid (check localStorage)

### Timer not working
- Ensure system clock is accurate
- Check `expires_at` timestamp in browser devtools
- Backend and frontend should use UTC time

### Polling issues
- Check browser console for API errors
- Verify network connectivity
- Ensure API key hasn't expired

## Development Tips

- Use React DevTools to inspect component state
- Use Network tab to monitor API calls
- Check Context state in GameContext
- Timer updates every 1 second automatically

## Production Deployment

For production deployment:

1. Update `VITE_API_URL` to production backend URL
2. Build the app: `npm run build`
3. Deploy `dist/` folder to static hosting (Vercel, Netlify, etc.)
4. Ensure HTTPS for API key security
5. Configure backend CORS for your frontend domain

See [FRONTEND_PLAN.md](../docs/FRONTEND_PLAN.md) for detailed deployment guidance.
