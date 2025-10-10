import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import apiClient, { extractErrorMessage } from '../api/client';
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

  const refreshBalance = useCallback(async (signal?: AbortSignal) => {
    if (!apiKey) return;
    try {
      const data = await apiClient.getBalance(signal);
      setPlayer(data);
      setError(null);
    } catch (err) {
      // Ignore aborted requests
      if (err instanceof Error && err.name === 'CanceledError') return;
      const errorMessage = extractErrorMessage(err);
      setError(errorMessage || 'Failed to fetch balance');
      if (errorMessage && errorMessage.includes('Invalid API key')) {
        logout();
      }
    }
  }, [apiKey, logout]);

  const refreshCurrentRound = useCallback(async (signal?: AbortSignal) => {
    if (!apiKey) return;
    try {
      const data = await apiClient.getCurrentRound(signal);
      setActiveRound(data);
      setError(null);
    } catch (err) {
      // Ignore aborted requests
      if (err instanceof Error && err.name === 'CanceledError') return;
      setError(extractErrorMessage(err) || 'Failed to fetch current round');
    }
  }, [apiKey]);

  const refreshPendingResults = useCallback(async (signal?: AbortSignal) => {
    if (!apiKey) return;
    try {
      const data = await apiClient.getPendingResults(signal);
      setPendingResults(data.pending);
      setError(null);
    } catch (err) {
      // Ignore aborted requests
      if (err instanceof Error && err.name === 'CanceledError') return;
      setError(extractErrorMessage(err) || 'Failed to fetch pending results');
    }
  }, [apiKey]);

  const refreshRoundAvailability = useCallback(async (signal?: AbortSignal) => {
    if (!apiKey) return;
    try {
      const data = await apiClient.getRoundAvailability(signal);
      setRoundAvailability(data);
      setError(null);
    } catch (err) {
      // Ignore aborted requests
      if (err instanceof Error && err.name === 'CanceledError') return;
      setError(extractErrorMessage(err) || 'Failed to fetch round availability');
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
      setError(extractErrorMessage(err) || 'Failed to claim bonus');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [apiKey, refreshBalance]);

  // Initial load when API key is set
  useEffect(() => {
    if (!apiKey) return;

    const controller = new AbortController();

    refreshBalance(controller.signal);
    refreshCurrentRound(controller.signal);
    refreshPendingResults(controller.signal);
    refreshRoundAvailability(controller.signal);

    return () => {
      controller.abort();
    };
  }, [apiKey, refreshBalance, refreshCurrentRound, refreshPendingResults, refreshRoundAvailability]);

  // Polling intervals
  useEffect(() => {
    if (!apiKey) return;

    const controllers: AbortController[] = [];

    // Poll balance every 30 seconds
    const balanceInterval = setInterval(() => {
      const controller = new AbortController();
      controllers.push(controller);
      refreshBalance(controller.signal);
    }, 30000);

    // Poll current round every 5 seconds if there's an active round
    const roundInterval = setInterval(() => {
      if (activeRound?.round_id) {
        const controller = new AbortController();
        controllers.push(controller);
        refreshCurrentRound(controller.signal);
      }
    }, 5000);

    // Poll pending results every 60 seconds
    const resultsInterval = setInterval(() => {
      const controller = new AbortController();
      controllers.push(controller);
      refreshPendingResults(controller.signal);
    }, 60000);

    // Poll round availability every 10 seconds when idle
    const availabilityInterval = setInterval(() => {
      if (!activeRound?.round_id) {
        const controller = new AbortController();
        controllers.push(controller);
        refreshRoundAvailability(controller.signal);
      }
    }, 10000);

    return () => {
      // Clear intervals
      clearInterval(balanceInterval);
      clearInterval(roundInterval);
      clearInterval(resultsInterval);
      clearInterval(availabilityInterval);

      // Abort all pending requests
      controllers.forEach(controller => controller.abort());
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
