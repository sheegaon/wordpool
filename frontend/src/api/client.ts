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
  SubmitPhraseResponse,
  VoteResponse,
  PhrasesetResults,
  HealthResponse,
  ApiError,
  UsernameLoginResponse,
  PromptFeedbackResponse,
  GetPromptFeedbackResponse,
  PhrasesetListResponse,
  PhrasesetDashboardSummary,
  PhrasesetDetails,
  ClaimPrizeResponse,
  UnclaimedResultsResponse,
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

// Helper function to extract meaningful error messages
const extractErrorMessage = (error: any): string => {
  // If it's already a string, return it
  if (typeof error === 'string') {
    return error;
  }
  
  // If it's an Error object, use its message
  if (error instanceof Error) {
    return error.message;
  }
  
  // If it's an object with a message property, use that
  if (error && typeof error === 'object') {
    // Handle FastAPI/Pydantic validation errors
    if (error.detail) {
      const detail = error.detail;
      // If detail is an array (Pydantic validation errors)
      if (Array.isArray(detail)) {
        // Extract the first validation error message
        const firstError = detail[0];
        if (firstError) {
          if (typeof firstError === 'string') {
            return firstError;
          }
          if (typeof firstError === 'object' && 'msg' in firstError && typeof firstError.msg === 'string') {
            return firstError.msg;
          }
        }
        // Fallback to a generic validation error message
        return 'Validation error';
      }
      // If detail is a string (regular API errors)
      if (typeof detail === 'string') {
        return detail;
      }
      if (detail && typeof detail === 'object') {
        if ('msg' in detail && typeof detail.msg === 'string') {
          return detail.msg;
        }
        if ('message' in detail && typeof detail.message === 'string') {
          return detail.message;
        }
      }
    }

    // Handle backend error objects like {"error": "invalid_phrase", "message": "..."}
    if (error.error && error.message) {
      return error.message;
    }

    if (error.message) {
      return error.message;
    }
  }

  // Fallback to string conversion
  return String(error);
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
  const apiKey = localStorage.getItem('quipflip_api_key');
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
    // Transform error into a format the UI can parse without losing detail
    if (error.response) {
      const { status, data } = error.response;

      let errorPayload: any;
      if (data == null) {
        errorPayload = {};
      } else if (Array.isArray(data)) {
        errorPayload = { detail: data };
      } else if (typeof data === 'object') {
        errorPayload = { ...data };
      } else {
        errorPayload = { detail: String(data) };
      }

      if (status === 401) {
        errorPayload.detail = errorPayload.detail || 'Invalid API key. Please login again.';
      } else if (status === 429) {
        errorPayload.detail = errorPayload.detail || 'Rate limit exceeded. Please try again later.';
      }

      errorPayload.status = status;
      return Promise.reject(errorPayload);
    }

    if (error.code === 'ERR_NETWORK') {
      return Promise.reject({ message: 'Network error. Please check your connection.' });
    }

    return Promise.reject(error);
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

  async loginWithUsername(username: string, signal?: AbortSignal): Promise<UsernameLoginResponse> {
    const { data } = await api.post('/player/login', { username }, { signal });
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

  async getPlayerPhrasesets(
    params: { role?: string; status?: string; limit?: number; offset?: number } = {},
    signal?: AbortSignal,
  ): Promise<PhrasesetListResponse> {
    const { data } = await api.get('/player/phrasesets', {
      params,
      signal,
    });
    return data;
  },

  async getPhrasesetsSummary(signal?: AbortSignal): Promise<PhrasesetDashboardSummary> {
    const { data } = await api.get('/player/phrasesets/summary', { signal });
    return data;
  },

  async getUnclaimedResults(signal?: AbortSignal): Promise<UnclaimedResultsResponse> {
    const { data } = await api.get('/player/unclaimed-results', { signal });
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

  async submitPhrase(roundId: string, phrase: string, signal?: AbortSignal): Promise<SubmitPhraseResponse> {
    const { data } = await api.post(`/rounds/${roundId}/submit`, { phrase }, { signal });
    return data;
  },

  // Phraseset endpoints
  async submitVote(phrasesetId: string, phrase: string, signal?: AbortSignal): Promise<VoteResponse> {
    const { data } = await api.post(`/phrasesets/${phrasesetId}/vote`, { phrase }, { signal });
    return data;
  },

  async getPhrasesetResults(phrasesetId: string, signal?: AbortSignal): Promise<PhrasesetResults> {
    const { data } = await api.get(`/phrasesets/${phrasesetId}/results`, { signal });
    return data;
  },

  async getPhrasesetDetails(phrasesetId: string, signal?: AbortSignal): Promise<PhrasesetDetails> {
    const { data } = await api.get(`/phrasesets/${phrasesetId}/details`, { signal });
    return data;
  },

  async claimPhrasesetPrize(phrasesetId: string, signal?: AbortSignal): Promise<ClaimPrizeResponse> {
    const { data } = await api.post(`/phrasesets/${phrasesetId}/claim`, {}, { signal });
    return data;
  },

  // Prompt feedback endpoints
  async submitPromptFeedback(roundId: string, feedbackType: 'like' | 'dislike', signal?: AbortSignal): Promise<PromptFeedbackResponse> {
    const { data } = await api.post(`/rounds/${roundId}/feedback`, { feedback_type: feedbackType }, { signal });
    return data;
  },

  async getPromptFeedback(roundId: string, signal?: AbortSignal): Promise<GetPromptFeedbackResponse> {
    const { data } = await api.get(`/rounds/${roundId}/feedback`, { signal });
    return data;
  },
};

export default apiClient;

// Export the error message extraction utility for use in components
export { extractErrorMessage };
