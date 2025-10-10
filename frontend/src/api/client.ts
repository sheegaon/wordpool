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

// Helper for dev logging
const isDev = import.meta.env.DEV;
const logApi = (method: string, endpoint: string, status: 'start' | 'success' | 'error', details?: any) => {
  if (!isDev) return;
  const emoji = status === 'start' ? '📤' : status === 'success' ? '✅' : '❌';
  const message = `${emoji} API [${method.toUpperCase()} ${endpoint}]`;
  if (details) {
    console.log(message, details);
  } else {
    console.log(message);
  }
};

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add API key and log requests
api.interceptors.request.use((config) => {
  const apiKey = localStorage.getItem('wordpool_api_key');
  if (apiKey && config.headers) {
    config.headers['X-API-Key'] = apiKey;
  }
  
  // Log the request
  const method = config.method?.toUpperCase() || 'UNKNOWN';
  const endpoint = config.url || '';
  logApi(method, endpoint, 'start');
  
  return config;
});

// Response interceptor for success/error logging and error handling
api.interceptors.response.use(
  (response) => {
    // Log successful response
    const method = response.config.method?.toUpperCase() || 'UNKNOWN';
    const endpoint = response.config.url || '';
    logApi(method, endpoint, 'success', response.data);
    
    return response;
  },
  (error: AxiosError<ApiError>) => {
    // Log error response
    if (error.config) {
      const method = error.config.method?.toUpperCase() || 'UNKNOWN';
      const endpoint = error.config.url || '';
      const errorMessage = error.response?.data?.detail || error.message;
      logApi(method, endpoint, 'error', errorMessage);
    }
    
    // Ignore aborted requests
    if (error.code === 'ERR_CANCELED') {
      return Promise.reject(error);
    }
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
  async getHealth(signal?: AbortSignal): Promise<HealthResponse> {
    const { data } = await api.get('/health', { signal });
    return data;
  },

  // Player endpoints
  async createPlayer(signal?: AbortSignal): Promise<CreatePlayerResponse> {
    const { data } = await api.post('/player', {}, { signal });
    return data;
  },

  async getBalance(signal?: AbortSignal): Promise<Player> {
    const { data } = await api.get('/player/balance', { signal });
    return data;
  },

  async claimDailyBonus(signal?: AbortSignal): Promise<DailyBonusResponse> {
    const { data } = await api.post('/player/claim-daily-bonus', {}, { signal });
    return data;
  },

  async getCurrentRound(signal?: AbortSignal): Promise<ActiveRound> {
    const { data } = await api.get('/player/current-round', { signal });
    return data;
  },

  async getPendingResults(signal?: AbortSignal): Promise<PendingResultsResponse> {
    const { data } = await api.get('/player/pending-results', { signal });
    return data;
  },

  async rotateKey(signal?: AbortSignal): Promise<{ new_api_key: string; message: string }> {
    const { data } = await api.post('/player/rotate-key', {}, { signal });
    return data;
  },

  // Round endpoints
  async getRoundAvailability(signal?: AbortSignal): Promise<RoundAvailability> {
    const { data } = await api.get('/rounds/available', { signal });
    return data;
  },

  async startPromptRound(signal?: AbortSignal): Promise<StartPromptResponse> {
    const { data } = await api.post('/rounds/prompt', {}, { signal });
    return data;
  },

  async startCopyRound(signal?: AbortSignal): Promise<StartCopyResponse> {
    const { data } = await api.post('/rounds/copy', {}, { signal });
    return data;
  },

  async startVoteRound(signal?: AbortSignal): Promise<StartVoteResponse> {
    const { data } = await api.post('/rounds/vote', {}, { signal });
    return data;
  },

  async submitWord(roundId: string, word: string, signal?: AbortSignal): Promise<SubmitWordResponse> {
    const { data } = await api.post(`/rounds/${roundId}/submit`, { word }, { signal });
    return data;
  },

  // Wordset endpoints
  async submitVote(wordsetId: string, word: string, signal?: AbortSignal): Promise<VoteResponse> {
    const { data } = await api.post(`/wordsets/${wordsetId}/vote`, { word }, { signal });
    return data;
  },

  async getWordsetResults(wordsetId: string, signal?: AbortSignal): Promise<WordsetResults> {
    const { data } = await api.get(`/wordsets/${wordsetId}/results`, { signal });
    return data;
  },
};

export default apiClient;
