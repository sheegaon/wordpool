"""Word validation service."""
import os
from typing import Set
import logging

logger = logging.getLogger(__name__)


class WordValidator:
    """Validates words against dictionary."""

    def __init__(self):
        self.dictionary: Set[str] = self._load_dictionary()
        logger.info(f"Loaded dictionary with {len(self.dictionary)} words")

    def _load_dictionary(self) -> Set[str]:
        """Load word list from file."""
        # Path relative to this file
        data_path = os.path.join(os.path.dirname(__file__), "../data/dictionary.txt")

        if not os.path.exists(data_path):
            logger.error(f"Dictionary file not found at: {data_path}")
            logger.error("Run: python scripts/download_dictionary.py")
            raise FileNotFoundError(f"Dictionary file not found: {data_path}")

        with open(data_path, "r") as f:
            return {line.strip().upper() for line in f if line.strip()}

    def validate(self, word: str) -> tuple[bool, str]:
        """
        Validate a word.

        Returns:
            (is_valid, error_message)
        """
        # Normalize
        word = word.strip().upper()

        # Check length
        if len(word) < 2 or len(word) > 15:
            return False, "Word must be 2-15 characters"

        # Check characters
        if not word.isalpha():
            return False, "Word must contain only letters A-Z"

        # Check dictionary
        if word not in self.dictionary:
            return False, "Word not in dictionary"

        return True, ""

    def validate_copy(self, word: str, original: str) -> tuple[bool, str]:
        """
        Validate a copy word (includes duplicate check).

        Returns:
            (is_valid, error_message)
        """
        # First validate normally
        is_valid, error = self.validate(word)
        if not is_valid:
            return False, error

        # Check for duplicate
        word_normalized = word.strip().upper()
        original_normalized = original.strip().upper()

        if word_normalized == original_normalized:
            return False, "Cannot submit the same word as original"

        return True, ""


# Singleton instance
_word_validator: WordValidator | None = None


def get_word_validator() -> WordValidator:
    """Get singleton word validator instance."""
    global _word_validator
    if _word_validator is None:
        _word_validator = WordValidator()
    return _word_validator
