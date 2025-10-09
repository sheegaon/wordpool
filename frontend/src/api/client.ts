import axios, { AxiosError } from 'axios';
import type {
  Player,
  CreatePlayerResponse,
  ActiveRound,
  PendingResultsResponse,
  DailyBonusResponse,
  RoundAvailability,
  StartPromptResponse,
  StartCopyResponse,
  StartVoteResponse,
  SubmitWordResponse,
  VoteResponse,
  WordsetResults,
  HealthResponse,
  ApiError,
} from './types';

// Base URL - configure based on environment
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add API key
api.interceptors.request.use((config) => {
  const apiKey = localStorage.getItem('wordpool_api_key');
  if (apiKey && config.headers) {
    config.headers['X-API-Key'] = apiKey;
  }
  return config;
});

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiError>) => {
    // Transform error to user-friendly message
    if (error.response?.data?.detail) {
      throw new Error(error.response.data.detail);
    }
    if (error.response?.status === 401) {
      throw new Error('Invalid API key. Please login again.');
    }
    if (error.response?.status === 429) {
      throw new Error('Rate limit exceeded. Please try again later.');
    }
    if (error.code === 'ERR_NETWORK') {
      throw new Error('Network error. Please check your connection.');
    }
    throw new Error('An unexpected error occurred.');
  }
);

// API Client methods
export const apiClient = {
  // Health & Info
  async getHealth(): Promise<HealthResponse> {
    const { data } = await api.get('/health');
    return data;
  },

  // Player endpoints
  async createPlayer(): Promise<CreatePlayerResponse> {
    const { data } = await api.post('/player');
    return data;
  },

  async getBalance(): Promise<Player> {
    const { data } = await api.get('/player/balance');
    return data;
  },

  async claimDailyBonus(): Promise<DailyBonusResponse> {
    const { data } = await api.post('/player/claim-daily-bonus');
    return data;
  },

  async getCurrentRound(): Promise<ActiveRound> {
    const { data } = await api.get('/player/current-round');
    return data;
  },

  async getPendingResults(): Promise<PendingResultsResponse> {
    const { data } = await api.get('/player/pending-results');
    return data;
  },

  async rotateKey(): Promise<{ new_api_key: string; message: string }> {
    const { data } = await api.post('/player/rotate-key');
    return data;
  },

  // Round endpoints
  async getRoundAvailability(): Promise<RoundAvailability> {
    const { data } = await api.get('/rounds/available');
    return data;
  },

  async startPromptRound(): Promise<StartPromptResponse> {
    const { data } = await api.post('/rounds/prompt', {});
    return data;
  },

  async startCopyRound(): Promise<StartCopyResponse> {
    const { data } = await api.post('/rounds/copy', {});
    return data;
  },

  async startVoteRound(): Promise<StartVoteResponse> {
    const { data } = await api.post('/rounds/vote', {});
    return data;
  },

  async submitWord(roundId: string, word: string): Promise<SubmitWordResponse> {
    const { data } = await api.post(`/rounds/${roundId}/submit`, { word });
    return data;
  },

  // Wordset endpoints
  async submitVote(wordsetId: string, word: string): Promise<VoteResponse> {
    const { data } = await api.post(`/wordsets/${wordsetId}/vote`, { word });
    return data;
  },

  async getWordsetResults(wordsetId: string): Promise<WordsetResults> {
    const { data } = await api.get(`/wordsets/${wordsetId}/results`);
    return data;
  },
};

export default apiClient;
