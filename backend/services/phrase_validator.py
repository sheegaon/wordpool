"""Phrase validation service with similarity checking."""
import os
import re
import logging
from typing import Set

from sklearn.metrics.pairwise import cosine_similarity

from backend.config import get_settings
from backend.utils.exceptions import InvalidPhraseError, DuplicatePhraseError, PhraseTooSimilarError

logger = logging.getLogger(__name__)


class PhraseValidator:
    """Validates phrases against dictionary and similarity constraints."""

    # Common connecting words that are allowed even if short or not in dictionary
    CONNECTING_WORDS = {'A', 'I'}

    def __init__(self):
        self.settings = get_settings()
        self.dictionary: Set[str] = self._load_dictionary()
        self._similarity_model = None  # Lazy load on first use
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

    @property
    def similarity_model(self):
        """Lazy load sentence transformer model."""
        if self._similarity_model is None:
            try:
                from sentence_transformers import SentenceTransformer
                logger.info(f"Loading similarity model: {self.settings.similarity_model}")
                self._similarity_model = SentenceTransformer(self.settings.similarity_model)
                logger.info("Similarity model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load similarity model: {e}")
                raise
        return self._similarity_model

    def calculate_similarity(self, phrase1: str, phrase2: str) -> float:
        """
        Calculate cosine similarity between two phrases using sentence embeddings.

        Args:
            phrase1: First phrase
            phrase2: Second phrase

        Returns:
            Similarity score between 0.0 and 1.0
        """
        try:
            # Normalize phrases
            phrase1 = phrase1.strip().lower()
            phrase2 = phrase2.strip().lower()

            # Get embeddings
            embeddings = self.similarity_model.encode([phrase1, phrase2])

            # Calculate cosine similarity
            similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]

            logger.debug(f"Similarity between '{phrase1}' and '{phrase2}': {similarity:.4f}")
            return float(similarity)
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            # If similarity check fails, be conservative and allow the phrase
            logger.warning("Similarity check failed, allowing phrase")
            return 0.0

    def _parse_phrase(self, phrase: str) -> list[str]:
        """
        Parse phrase into individual words.

        Args:
            phrase: Raw phrase input

        Returns:
            List of words
        """
        # Strip and normalize whitespace
        phrase = phrase.strip()
        phrase = re.sub(r'\s+', ' ', phrase)  # Replace multiple spaces with single space

        # Split into words
        words = phrase.split()
        return words

    def validate(self, phrase: str) -> tuple[bool, str]:
        """
        Validate a phrase for format and dictionary compliance.

        Args:
            phrase: The phrase to validate

        Returns:
            (is_valid, error_message)
        """
        # Normalize
        phrase = phrase.strip()

        # Check basic format
        if not phrase:
            return False, "Phrase cannot be empty"

        # Check overall length
        if len(phrase) > self.settings.phrase_max_length:
            return False, f"Phrase must be {self.settings.phrase_max_length} characters or less"

        # Check for valid characters (letters and spaces only)
        if not re.match(r'^[a-zA-Z\s]+$', phrase):
            return False, "Phrase must contain only letters A-Z and spaces"

        # Parse into words
        words = self._parse_phrase(phrase)

        # Check word count
        if len(words) < self.settings.phrase_min_words:
            return False, f"Phrase must contain at least {self.settings.phrase_min_words} word"

        if len(words) > self.settings.phrase_max_words:
            return False, f"Phrase must contain at most {self.settings.phrase_max_words} words"

        # Validate each word
        for word in words:
            word_upper = word.upper()

            # Allow common connecting words regardless of length or dictionary
            if word_upper in self.CONNECTING_WORDS:
                continue

            # Check word length (skip for connecting words)
            if len(word) < self.settings.phrase_min_char_per_word:
                return False, f"Each word must be at least {self.settings.phrase_min_char_per_word} characters"

            if len(word) > self.settings.phrase_max_char_per_word:
                return False, f"Each word must be at most {self.settings.phrase_max_char_per_word} characters"

            # Check dictionary
            if word_upper not in self.dictionary:
                return False, f"Word '{word}' not in dictionary"

        return True, ""

    def validate_copy(
        self,
        phrase: str,
        original_phrase: str,
        other_copy_phrase: str | None = None
    ) -> tuple[bool, str]:
        """
        Validate a copy phrase (includes duplicate and similarity checks).

        Args:
            phrase: The copy phrase to validate
            original_phrase: The original prompt phrase
            other_copy_phrase: The other copy phrase (if already submitted)

        Returns:
            (is_valid, error_message)
        """
        # First validate format and dictionary
        is_valid, error = self.validate(phrase)
        if not is_valid:
            return False, error

        # Normalize for comparison
        phrase_normalized = phrase.strip().upper()
        original_normalized = original_phrase.strip().upper()

        # Check for exact duplicate of original
        if phrase_normalized == original_normalized:
            return False, "Cannot submit the same phrase as original"

        # Check for exact duplicate of other copy
        if other_copy_phrase:
            other_copy_normalized = other_copy_phrase.strip().upper()
            if phrase_normalized == other_copy_normalized:
                return False, "Cannot submit the same phrase as other copy"

        # Check similarity to original phrase
        try:
            similarity_to_original = self.calculate_similarity(phrase, original_phrase)

            if similarity_to_original >= self.settings.similarity_threshold:
                return False, (
                    f"Phrase too similar to original "
                    f"(similarity: {similarity_to_original:.2f}, "
                    f"threshold: {self.settings.similarity_threshold})"
                )
        except Exception as e:
            logger.error(f"Similarity check to original failed: {e}")
            # If similarity check fails, be conservative and reject
            return False, "Unable to verify phrase uniqueness, please try a different phrase"

        # Check similarity to other copy if it exists
        if other_copy_phrase:
            try:
                similarity_to_other = self.calculate_similarity(phrase, other_copy_phrase)

                if similarity_to_other >= self.settings.similarity_threshold:
                    return False, (
                        f"Phrase too similar to other copy "
                        f"(similarity: {similarity_to_other:.2f}, "
                        f"threshold: {self.settings.similarity_threshold})"
                    )
            except Exception as e:
                logger.error(f"Similarity check to other copy failed: {e}")
                # If similarity check fails, be conservative and reject
                return False, "Unable to verify phrase uniqueness, please try a different phrase"

        return True, ""


# Singleton instance
_phrase_validator: PhraseValidator | None = None


def get_phrase_validator() -> PhraseValidator:
    """Get singleton phrase validator instance."""
    global _phrase_validator
    if _phrase_validator is None:
        _phrase_validator = PhraseValidator()
    return _phrase_validator
