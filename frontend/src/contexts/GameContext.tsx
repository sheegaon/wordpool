import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import apiClient from '../api/client';
import type { Player, ActiveRound, PendingResult, RoundAvailability } from '../api/types';

interface GameContextType {
  // State
  apiKey: string | null;
  player: Player | null;
  activeRound: ActiveRound | null;
  pendingResults: PendingResult[];
  roundAvailability: RoundAvailability | null;
  loading: boolean;
  error: string | null;

  // Actions
  setApiKey: (key: string) => void;
  logout: () => void;
  refreshBalance: () => Promise<void>;
  refreshCurrentRound: () => Promise<void>;
  refreshPendingResults: () => Promise<void>;
  refreshRoundAvailability: () => Promise<void>;
  claimBonus: () => Promise<void>;
  clearError: () => void;
}

const GameContext = createContext<GameContextType | undefined>(undefined);

export const GameProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [apiKey, setApiKeyState] = useState<string | null>(() =>
    localStorage.getItem('wordpool_api_key')
  );
  const [player, setPlayer] = useState<Player | null>(null);
  const [activeRound, setActiveRound] = useState<ActiveRound | null>(null);
  const [pendingResults, setPendingResults] = useState<PendingResult[]>([]);
  const [roundAvailability, setRoundAvailability] = useState<RoundAvailability | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const setApiKey = useCallback((key: string) => {
    localStorage.setItem('wordpool_api_key', key);
    setApiKeyState(key);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('wordpool_api_key');
    setApiKeyState(null);
    setPlayer(null);
    setActiveRound(null);
    setPendingResults([]);
    setRoundAvailability(null);
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const refreshBalance = useCallback(async () => {
    if (!apiKey) return;
    try {
      const data = await apiClient.getBalance();
      setPlayer(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch balance');
      if (err instanceof Error && err.message.includes('Invalid API key')) {
        logout();
      }
    }
  }, [apiKey, logout]);

  const refreshCurrentRound = useCallback(async () => {
    if (!apiKey) return;
    try {
      const data = await apiClient.getCurrentRound();
      setActiveRound(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch current round');
    }
  }, [apiKey]);

  const refreshPendingResults = useCallback(async () => {
    if (!apiKey) return;
    try {
      const data = await apiClient.getPendingResults();
      setPendingResults(data.pending);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch pending results');
    }
  }, [apiKey]);

  const refreshRoundAvailability = useCallback(async () => {
    if (!apiKey) return;
    try {
      const data = await apiClient.getRoundAvailability();
      setRoundAvailability(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch round availability');
    }
  }, [apiKey]);

  const claimBonus = useCallback(async () => {
    if (!apiKey) return;
    try {
      setLoading(true);
      await apiClient.claimDailyBonus();
      await refreshBalance();
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to claim bonus');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [apiKey, refreshBalance]);

  // Initial load when API key is set
  useEffect(() => {
    if (apiKey) {
      refreshBalance();
      refreshCurrentRound();
      refreshPendingResults();
      refreshRoundAvailability();
    }
  }, [apiKey]);

  // Polling intervals
  useEffect(() => {
    if (!apiKey) return;

    // Poll balance every 30 seconds
    const balanceInterval = setInterval(refreshBalance, 30000);

    // Poll current round every 5 seconds if there's an active round
    const roundInterval = setInterval(() => {
      if (activeRound?.round_id) {
        refreshCurrentRound();
      }
    }, 5000);

    // Poll pending results every 60 seconds
    const resultsInterval = setInterval(refreshPendingResults, 60000);

    // Poll round availability every 10 seconds when idle
    const availabilityInterval = setInterval(() => {
      if (!activeRound?.round_id) {
        refreshRoundAvailability();
      }
    }, 10000);

    return () => {
      clearInterval(balanceInterval);
      clearInterval(roundInterval);
      clearInterval(resultsInterval);
      clearInterval(availabilityInterval);
    };
  }, [apiKey, activeRound?.round_id, refreshBalance, refreshCurrentRound, refreshPendingResults, refreshRoundAvailability]);

  const value: GameContextType = {
    apiKey,
    player,
    activeRound,
    pendingResults,
    roundAvailability,
    loading,
    error,
    setApiKey,
    logout,
    refreshBalance,
    refreshCurrentRound,
    refreshPendingResults,
    refreshRoundAvailability,
    claimBonus,
    clearError,
  };

  return <GameContext.Provider value={value}>{children}</GameContext.Provider>;
};

export const useGame = () => {
  const context = useContext(GameContext);
  if (context === undefined) {
    throw new Error('useGame must be used within a GameProvider');
  }
  return context;
};
