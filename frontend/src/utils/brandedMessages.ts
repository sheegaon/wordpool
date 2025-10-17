/**
 * Branded success messages for Quipflip
 */

export const successMessages = {
  promptSubmitted: [
    "Nice quip!",
    "You flipped it!",
    "Quip-tastic submission!",
    "That's a keeper!",
    "Brilliant quip!",
  ],
  copySubmitted: [
    "Perfect flip!",
    "You nailed the copy!",
    "Matched like a pro!",
    "Quip copied successfully!",
    "Great minds flip alike!",
  ],
  voteSubmitted: [
    "Vote locked in!",
    "Your pick is in!",
    "Choice recorded!",
    "Decision made!",
    "Let's see if you're right!",
  ],
  bonusClaimed: [
    "Bonus quipped into your bank!",
    "Daily quips collected!",
    "Your balance just got flipped!",
    "Cha-ching!",
  ],
  prizesClaimed: [
    "Quip-tastic winnings!",
    "You flipped those prizes!",
    "Prizes claimed successfully!",
    "Money in the Quip Bank!",
  ],
};

/**
 * Get a random success message from a category
 */
export const getRandomMessage = (category: keyof typeof successMessages): string => {
  const messages = successMessages[category];
  return messages[Math.floor(Math.random() * messages.length)];
};

/**
 * Loading messages for Quipflip
 */
export const loadingMessages = {
  default: "Shuffling the tiles...",
  starting: "Preparing your quip...",
  submitting: "Flipping your quip...",
  loading: "Loading quips...",
  claiming: "Claiming your quips...",
};
