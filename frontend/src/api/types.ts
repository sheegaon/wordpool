// API Response Types based on backend documentation

export interface Player {
  username: string;
  balance: number;
  starting_balance: number;
  daily_bonus_available: boolean;
  daily_bonus_amount: number;
  last_login_date: string;
  outstanding_prompts: number;
}

export interface CreatePlayerResponse {
  player_id: string;
  username: string;
  api_key: string;
  balance: number;
  message: string;
}

export interface UsernameLoginResponse {
  player_id: string;
  username: string;
  api_key: string;
  message: string;
}

export interface PromptState {
  round_id: string;
  status: 'active' | 'submitted';
  expires_at: string;
  cost: number;
  prompt_text: string;
  feedback_type?: 'like' | 'dislike' | null;
}

export interface CopyState {
  round_id: string;
  status: 'active' | 'submitted';
  expires_at: string;
  cost: number;
  original_phrase: string;
  discount_active: boolean;
}

export interface VoteState {
  round_id: string;
  status: 'active' | 'submitted';
  expires_at: string;
  phraseset_id: string;
  prompt_text: string;
  phrases: string[];
}

export interface ActiveRound {
  round_id: string | null;
  round_type: 'prompt' | 'copy' | 'vote' | null;
  expires_at: string | null;
  state: PromptState | CopyState | VoteState | null;
}

export interface PendingResult {
  phraseset_id: string;
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
  phrasesets_waiting: number;
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
  original_phrase: string;
  prompt_round_id: string;
  expires_at: string;
  cost: number;
  discount_active: boolean;
}

export interface StartVoteResponse {
  round_id: string;
  phraseset_id: string;
  prompt_text: string;
  phrases: string[];
  expires_at: string;
}

export interface SubmitPhraseResponse {
  success: boolean;
  phrase: string;
}

export interface VoteResponse {
  correct: boolean;
  payout: number;
  original_phrase: string;
  your_choice: string;
}

export interface VoteResult {
  phrase: string;
  vote_count: number;
  is_original: boolean;
}

export interface PhrasesetResults {
  prompt_text: string;
  votes: VoteResult[];
  your_phrase: string;
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

export interface SubmitPromptFeedbackRequest {
  feedback_type: 'like' | 'dislike';
}

export interface PromptFeedbackResponse {
  success: boolean;
  feedback_type: 'like' | 'dislike';
  message: string;
}

export interface GetPromptFeedbackResponse {
  feedback_type: 'like' | 'dislike' | null;
  feedback_id: string | null;
  created_at: string | null;
}
