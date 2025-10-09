import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { GameProvider, useGame } from './contexts/GameContext';
import { Landing } from './pages/Landing';
import { Dashboard } from './pages/Dashboard';
import { PromptRound } from './pages/PromptRound';
import { CopyRound } from './pages/CopyRound';
import { VoteRound } from './pages/VoteRound';
import { Results } from './pages/Results';
import { ErrorNotification } from './components/ErrorNotification';

// Protected Route wrapper
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { apiKey } = useGame();

  if (!apiKey) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
};

// App Routes
const AppRoutes: React.FC = () => {
  const { apiKey } = useGame();

  return (
    <>
      <ErrorNotification />
      <Routes>
        <Route
          path="/"
          element={apiKey ? <Navigate to="/dashboard" replace /> : <Landing />}
        />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/prompt"
          element={
            <ProtectedRoute>
              <PromptRound />
            </ProtectedRoute>
          }
        />
        <Route
          path="/copy"
          element={
            <ProtectedRoute>
              <CopyRound />
            </ProtectedRoute>
          }
        />
        <Route
          path="/vote"
          element={
            <ProtectedRoute>
              <VoteRound />
            </ProtectedRoute>
          }
        />
        <Route
          path="/results"
          element={
            <ProtectedRoute>
              <Results />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  );
};

// Main App
function App() {
  return (
    <Router>
      <GameProvider>
        <AppRoutes />
      </GameProvider>
    </Router>
  );
}

export default App;
