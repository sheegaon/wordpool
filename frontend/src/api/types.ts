// API Response Types based on backend documentation

export interface Player {
  balance: number;
  starting_balance: number;
  daily_bonus_available: boolean;
  daily_bonus_amount: number;
  last_login_date: string;
  outstanding_prompts: number;
}

export interface CreatePlayerResponse {
  player_id: string;
  api_key: string;
  balance: number;
  message: string;
}

export interface PromptState {
  round_id: string;
  status: 'active' | 'submitted';
  expires_at: string;
  cost: number;
  prompt_text: string;
}

export interface CopyState {
  round_id: string;
  status: 'active' | 'submitted';
  expires_at: string;
  cost: number;
  original_word: string;
  discount_active: boolean;
}

export interface VoteState {
  round_id: string;
  status: 'active' | 'submitted';
  expires_at: string;
  wordset_id: string;
  prompt_text: string;
  words: string[];
}

export interface ActiveRound {
  round_id: string | null;
  round_type: 'prompt' | 'copy' | 'vote' | null;
  expires_at: string | null;
  state: PromptState | CopyState | VoteState | null;
}

export interface PendingResult {
  wordset_id: string;
  prompt_text: string;
  completed_at: string;
  role: string;
  payout_collected: boolean;
}

export interface PendingResultsResponse {
  pending: PendingResult[];
}

export interface DailyBonusResponse {
  success: boolean;
  amount: number;
  new_balance: number;
}

export interface RoundAvailability {
  can_prompt: boolean;
  can_copy: boolean;
  can_vote: boolean;
  prompts_waiting: number;
  wordsets_waiting: number;
  copy_discount_active: boolean;
  copy_cost: number;
  current_round_id: string | null;
}

export interface StartPromptResponse {
  round_id: string;
  prompt_text: string;
  expires_at: string;
  cost: number;
}

export interface StartCopyResponse {
  round_id: string;
  original_word: string;
  prompt_round_id: string;
  expires_at: string;
  cost: number;
  discount_active: boolean;
}

export interface StartVoteResponse {
  round_id: string;
  wordset_id: string;
  prompt_text: string;
  words: string[];
  expires_at: string;
}

export interface SubmitWordResponse {
  success: boolean;
  word: string;
}

export interface VoteResponse {
  correct: boolean;
  payout: number;
  original_word: string;
  your_choice: string;
}

export interface VoteResult {
  word: string;
  vote_count: number;
  is_original: boolean;
}

export interface WordsetResults {
  prompt_text: string;
  votes: VoteResult[];
  your_word: string;
  your_role: string;
  your_points: number;
  your_payout: number;
  total_pool: number;
  total_votes: number;
  already_collected: boolean;
  finalized_at: string;
}

export interface ApiError {
  detail: string;
}

export interface HealthResponse {
  status: string;
  database: string;
  redis: string;
}
