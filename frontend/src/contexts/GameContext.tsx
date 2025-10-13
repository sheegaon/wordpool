import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import apiClient, { extractErrorMessage } from '../api/client';
import type {
  Player,
  ActiveRound,
  PendingResult,
  RoundAvailability,
  PhrasesetDashboardSummary,
  UnclaimedResult,
} from '../api/types';

interface GameContextType {
  // State
  apiKey: string | null;
  username: string | null;
  player: Player | null;
  activeRound: ActiveRound | null;
  pendingResults: PendingResult[];
  phrasesetSummary: PhrasesetDashboardSummary | null;
  unclaimedResults: UnclaimedResult[];
  roundAvailability: RoundAvailability | null;
  loading: boolean;
  error: string | null;

  // Actions
  setApiKey: (key: string, username?: string) => void;
  logout: () => void;
  refreshBalance: () => Promise<void>;
  refreshCurrentRound: () => Promise<void>;
  refreshPendingResults: () => Promise<void>;
  refreshPhrasesetSummary: () => Promise<void>;
  refreshUnclaimedResults: () => Promise<void>;
  refreshRoundAvailability: () => Promise<void>;
  claimBonus: () => Promise<void>;
  clearError: () => void;
}

const GameContext = createContext<GameContextType | undefined>(undefined);

export const GameProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [apiKey, setApiKeyState] = useState<string | null>(() =>
    localStorage.getItem('wordpool_api_key')
  );
  const [username, setUsername] = useState<string | null>(() =>
    localStorage.getItem('wordpool_username')
  );
  const [player, setPlayer] = useState<Player | null>(null);
  const [activeRound, setActiveRound] = useState<ActiveRound | null>(null);
  const [pendingResults, setPendingResults] = useState<PendingResult[]>([]);
  const [phrasesetSummary, setPhrasesetSummary] = useState<PhrasesetDashboardSummary | null>(null);
  const [unclaimedResults, setUnclaimedResults] = useState<UnclaimedResult[]>([]);
  const [roundAvailability, setRoundAvailability] = useState<RoundAvailability | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const setApiKey = useCallback((key: string, nextUsername?: string) => {
    localStorage.setItem('wordpool_api_key', key);
    setApiKeyState(key);
    if (nextUsername) {
      localStorage.setItem('wordpool_username', nextUsername);
      setUsername(nextUsername);
    }
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('wordpool_api_key');
    localStorage.removeItem('wordpool_username');
    setApiKeyState(null);
    setUsername(null);
    setPlayer(null);
    setActiveRound(null);
    setPendingResults([]);
    setPhrasesetSummary(null);
    setUnclaimedResults([]);
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
      if (data.username && data.username !== username) {
        localStorage.setItem('wordpool_username', data.username);
        setUsername(data.username);
      }
      setError(null);
    } catch (err) {
      if (err instanceof Error && err.name === 'CanceledError') return;
      const errorMessage = extractErrorMessage(err);
      setError(errorMessage || 'Failed to fetch balance');
      if (errorMessage && errorMessage.includes('Invalid API key')) {
        logout();
      }
    }
  }, [apiKey, logout, username]);

  const refreshCurrentRound = useCallback(async (signal?: AbortSignal) => {
    if (!apiKey) return;
    try {
      const data = await apiClient.getCurrentRound(signal);
      setActiveRound(data);
      setError(null);
    } catch (err) {
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
      if (err instanceof Error && err.name === 'CanceledError') return;
      setError(extractErrorMessage(err) || 'Failed to fetch pending results');
    }
  }, [apiKey]);

  const refreshPhrasesetSummary = useCallback(async (signal?: AbortSignal) => {
    if (!apiKey) return;
    try {
      const data = await apiClient.getPhrasesetsSummary(signal);
      setPhrasesetSummary(data);
      setError(null);
    } catch (err) {
      if (err instanceof Error && err.name === 'CanceledError') return;
      setError(extractErrorMessage(err) || 'Failed to fetch phraseset summary');
    }
  }, [apiKey]);

  const refreshUnclaimedResults = useCallback(async (signal?: AbortSignal) => {
    if (!apiKey) return;
    try {
      const data = await apiClient.getUnclaimedResults(signal);
      setUnclaimedResults(data.unclaimed);
      setError(null);
    } catch (err) {
      if (err instanceof Error && err.name === 'CanceledError') return;
      setError(extractErrorMessage(err) || 'Failed to fetch unclaimed results');
    }
  }, [apiKey]);

  const refreshRoundAvailability = useCallback(async (signal?: AbortSignal) => {
    if (!apiKey) return;
    try {
      const data = await apiClient.getRoundAvailability(signal);
      setRoundAvailability(data);
      setError(null);
    } catch (err) {
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

  // Initial load
  useEffect(() => {
    if (!apiKey) return;

    const controller = new AbortController();
    refreshBalance(controller.signal);
    refreshCurrentRound(controller.signal);
    refreshPendingResults(controller.signal);
    refreshPhrasesetSummary(controller.signal);
    refreshUnclaimedResults(controller.signal);
    refreshRoundAvailability(controller.signal);

    return () => controller.abort();
  }, [
    apiKey,
    refreshBalance,
    refreshCurrentRound,
    refreshPendingResults,
    refreshPhrasesetSummary,
    refreshUnclaimedResults,
    refreshRoundAvailability,
  ]);

  // Polling intervals
  useEffect(() => {
    if (!apiKey) return;

    const controllers: AbortController[] = [];

    const pushController = () => {
      const controller = new AbortController();
      controllers.push(controller);
      return controller;
    };

    const balanceInterval = setInterval(() => {
      const controller = pushController();
      refreshBalance(controller.signal);
    }, 30000);

    const roundInterval = setInterval(() => {
      if (activeRound?.round_id) {
        const controller = pushController();
        refreshCurrentRound(controller.signal);
      }
    }, 5000);

    const resultsInterval = setInterval(() => {
      const controller = pushController();
      refreshPendingResults(controller.signal);
    }, 60000);

    const summaryInterval = setInterval(() => {
      const controller = pushController();
      refreshPhrasesetSummary(controller.signal);
    }, 60000);

    const unclaimedInterval = setInterval(() => {
      const controller = pushController();
      refreshUnclaimedResults(controller.signal);
    }, 60000);

    const availabilityInterval = setInterval(() => {
      if (!activeRound?.round_id) {
        const controller = pushController();
        refreshRoundAvailability(controller.signal);
      }
    }, 10000);

    return () => {
      clearInterval(balanceInterval);
      clearInterval(roundInterval);
      clearInterval(resultsInterval);
      clearInterval(summaryInterval);
      clearInterval(unclaimedInterval);
      clearInterval(availabilityInterval);
      controllers.forEach(controller => controller.abort());
    };
  }, [
    apiKey,
    activeRound?.round_id,
    refreshBalance,
    refreshCurrentRound,
    refreshPendingResults,
    refreshPhrasesetSummary,
    refreshUnclaimedResults,
    refreshRoundAvailability,
  ]);

  const value: GameContextType = {
    apiKey,
    username,
    player,
    activeRound,
    pendingResults,
    phrasesetSummary,
    unclaimedResults,
    roundAvailability,
    loading,
    error,
    setApiKey,
    logout,
    refreshBalance,
    refreshCurrentRound,
    refreshPendingResults,
    refreshPhrasesetSummary,
    refreshUnclaimedResults,
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
