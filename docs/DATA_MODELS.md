# Data Models

### Player
- `player_id` (UUID)
- `balance` (integer)
- `created_at` (timestamp)
- `last_login_date` (date) - for daily bonus tracking
- `daily_bonus_claimed_at` (timestamp, nullable)
- `active_round_id` (UUID, nullable) - enforces one-round-at-a-time

### Prompt Round
- `round_id` (UUID)
- `player_id` (UUID)
- `prompt_id` (UUID, references prompt library)
- `prompt_text` (string)
- `submitted_word` (string, nullable)
- `status` (enum: active, submitted, expired, cancelled)
- `created_at` (timestamp)
- `expires_at` (timestamp)
- `cost` (integer, always 100)

### Copy Round
- `round_id` (UUID)
- `player_id` (UUID)
- `prompt_round_id` (UUID, references prompt round)
- `original_word` (string)
- `submitted_word` (string, nullable)
- `status` (enum: active, submitted, expired, abandoned)
- `created_at` (timestamp)
- `expires_at` (timestamp)
- `cost` (integer, 90 or 100) - tracks what player paid
- `system_contribution` (int, 0 or 10) - for discounted copies

### Word Set
- `wordset_id` (UUID)
- `prompt_round_id` (UUID)
- `copy_round_1_id` (UUID)
- `copy_round_2_id` (UUID)
- `prompt_text` (string)
- `original_word` (string)
- `copy_word_1` (string)
- `copy_word_2` (string)
- `word_positions` (array[3]) - randomized order for display
- `status` (enum: open, closing, closed, finalized)
- `vote_count` (integer)
- `third_vote_at` (timestamp, nullable) - starts 10-minute window
- `fifth_vote_at` (timestamp, nullable) - starts 60-second window
- `closes_at` (timestamp, nullable) - calculated based on vote timeline
- `created_at` (timestamp)
- `total_pool` (integer, 300) - includes system contribution if applicable
- `system_contribution` (integer, 0 or 10)

### Vote
- `vote_id` (UUID)
- `wordset_id` (UUID)
- `player_id` (UUID)
- `voted_index` (0|1|2) - position in randomized word_positions array
- `voted_word` (string) - the actual word voted for
- `correct` (boolean)
- `payout` (integer, 5 or 0) - gross payout
- `created_at` (timestamp)

### Result View
- `view_id` (UUID)
- `wordset_id` (UUID)
- `player_id` (UUID)
- `payout_collected` (boolean)
- `payout_amount` (integer)
- `viewed_at` (timestamp)

### Transaction
- `transaction_id` (UUID)
- `player_id` (UUID)
- `amount` (integer, can be negative)
- `type` (enum: prompt_entry, copy_entry, vote_entry, vote_payout, prize_payout, refund, penalty, daily_bonus, system_contribution)
- `reference_id` (UUID, references round/wordset/vote)
- `created_at` (timestamp)

### Daily Bonus Log
- `bonus_id` (UUID)
- `player_id` (UUID)
- `amount` (integer, 100)
- `claimed_at` (timestamp)
- `date` (date) - for tracking one per day
