# Prompt Library Examples for Wordpool

Prompts are incomplete sentences or phrases with a blank. These encourage creative, dictionary-valid word responses (e.g., from NASPA list). Prompts should be neutral, engaging, and varied in difficulty/categories to maintain balance—avoiding sensitive topics per safety guidelines.

## Summary Tables

Here's a table-based summary. Each includes 5-8 examples with potential player responses (in italics) for illustration. Aim for 100+ total in the backend database, with metrics like `usage_count` and `avg_copy_quality` to rotate underperformers.

### Straightforward Prompts
These are everyday, relatable setups—low difficulty, high accessibility. Focus on personal habits or simple concepts.

| Prompt Text | Example Responses |
|-------------|-------------------|
| "my deepest desire is to be (a/an)" | *famous, rich, actor, explorer* |
| "success means being" | *happy, wealthy, fulfilled, loved* |
| "the secret to happiness is (a/an)" | *love, money, contentment, adventure* |
| "every day I" | *work, eat, play, sleep, dream* |
| "I feel most alive when I'm" | *running, creating, exploring, laughing* |
| "the world needs more" | *kindness, innovation, compassion, laughter* |
| "my favorite way to relax is with (a/an)" | *book, music, walk, friend* |
| "a perfect day starts with" | *coffee, sunrise, exercise, silence* |

### Deep Prompts
Philosophical or introspective—medium difficulty, encouraging abstract or profound words.

| Prompt Text | Example Responses |
|-------------|-------------------|
| "beauty is fundamentally" | *subjective, fleeting, timeless, inner* |
| "the meaning of life is" | *love, growth, mystery, purpose* |
| "art should be" | *provocative, beautiful, meaningful, free* |
| "freedom means" | *choice, independence, responsibility, flight* |
| "true wisdom comes from" | *experience, failure, reflection, age* |
| "the essence of friendship is" | *trust, loyalty, support, laughter* |
| "courage is facing" | *fear, uncertainty, truth, danger* |
| "happiness is ultimately" | *internal, shared, momentary, pursued* |

### Silly Prompts
Humorous or absurd—fun, low-stakes difficulty. These were incomplete in PLAN.md, so I've expanded with whimsical twists inspired by Balderdash's quirky definitions or word association chains (e.g., starting absurd scenarios).

| Prompt Text | Example Responses |
|-------------|-------------------|
| "the best superpower would be to turn into (a/an)" | *pancake, invisible, flying, talking* |
| "if animals could talk, a cat would say" | *feed, nap, worship, scratch* |
| "the weirdest invention ever is (a/an)" | *toaster, umbrella, robot, hat* |
| "my spirit animal is (a/an)" | *sloth, eagle, unicorn, potato* |
| "a zombie's favorite food is" | *brains, pizza, candy, salad* |
| "if I were a superhero, my weakness would be" | *kryptonite, Mondays, chocolate, tickles* |
| "the secret ingredient in magic potions is" | *frog, sparkle, laughter, salt* |
| "aliens probably think humans are" | *weird, noisy, cute, delicious* |

### Fun/Action-Oriented
To add variety (e.g., for seasonal rotations), these focus on dynamic or pop-culture vibes, drawing from Codenames' clue-linking (e.g., thematic associations).

| Prompt Text | Example Responses |
|-------------|-------------------|
| "a spy's best gadget is (a/an)" | *watch, laser, pen, shoe* |
| "the ultimate adventure involves" | *treasure, danger, maps, friends* |
| "in a fairy tale, the hero always finds (a/an)" | *sword, princess, dragon, key* |
| "my dream job would be (a/an)" | *astronaut, chef, detective, pirate* |
| "the key to winning a game is" | *strategy, luck, cheating, fun* |
| "a robot's daily routine includes" | *charging, computing, dancing, error* |
| "if I could time travel, I'd visit the" | *future, past, dinosaurs, Renaissance* |

### Abstract/Conceptual
Higher difficulty, inspired by word association games for broader interpretations.

| Prompt Text | Example Responses |
|-------------|-------------------|
| "time feels like (a/an)" | *river, thief, gift, illusion* |
| "dreams are made of" | *stars, memories, fears, wishes* |
| "silence can be" | *golden, deafening, peaceful, awkward* |
| "innovation starts with (a/an)" | *idea, failure, question, spark* |
| "the color of joy is" | *yellow, rainbow, bright, warm* |
| "echoes remind me of" | *mountains, past, loneliness, music* |

These examples ensure prompts are open-ended yet structured, promoting synonyms or associations in copy rounds (e.g., "famous" → "popular"). For implementation:
- **Total Variety**: Aim for 20-30 per category to start, with backend randomization.
- **Metrics Tracking**: As in PLAN.md, monitor `avg_copy_quality` (e.g., based on vote distribution evenness—ideal if copies fool 20-50% of voters).
- **Moderation**: Add filters to exclude prompts that could lead to disallowed content (per safety instructions).

## Prompt Library Design

### Prompt Structure
```json
{
  "prompt_id": "uuid",
  "text": "my deepest desire is to be (a/an)",
  "category": "simple|deep|silly|fun|abstract",
  "created_at": "timestamp",
  "usage_count": 0,
  "avg_copy_quality": 0.0,
  "enabled": true
}
```