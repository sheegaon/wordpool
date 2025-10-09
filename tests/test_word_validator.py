"""Tests for word validation."""
import pytest
from backend.services.word_validator import WordValidator


def test_word_validator_loads_dictionary():
    """Test validator loads dictionary successfully."""
    validator = WordValidator()
    assert len(validator.dictionary) > 0


def test_valid_words():
    """Test valid words pass validation."""
    validator = WordValidator()

    # Common words that should be in dictionary
    valid, msg = validator.validate("cat")
    assert valid is True

    valid, msg = validator.validate("dog")
    assert valid is True

    valid, msg = validator.validate("house")
    assert valid is True


def test_word_length_validation():
    """Test word length constraints (2-15 characters)."""
    validator = WordValidator()

    # Too short (1 char)
    valid, msg = validator.validate("a")
    assert valid is False
    assert "2-15" in msg or "length" in msg.lower()

    # Too long (16 chars)
    valid, msg = validator.validate("a" * 16)
    assert valid is False
    assert "2-15" in msg or "characters" in msg.lower()

    # Valid lengths
    valid, msg = validator.validate("ab")  # 2 chars
    assert valid is True or "not found" in msg.lower()  # Could be invalid word

    valid, msg = validator.validate("a" * 15)  # 15 chars
    # Valid length, but probably not a word
    assert "length" not in msg.lower()


def test_alphabetic_validation():
    """Test only A-Z characters are allowed."""
    validator = WordValidator()

    # Numbers
    valid, msg = validator.validate("cat123")
    assert valid is False
    assert "letters" in msg.lower()

    # Special characters
    valid, msg = validator.validate("cat-dog")
    assert valid is False

    valid, msg = validator.validate("cat's")
    assert valid is False

    # Spaces
    valid, msg = validator.validate("cat dog")
    assert valid is False


def test_case_insensitivity():
    """Test validation is case-insensitive."""
    validator = WordValidator()

    # All should be treated the same
    valid1, _ = validator.validate("cat")
    valid2, _ = validator.validate("CAT")
    valid3, _ = validator.validate("CaT")

    assert valid1 == valid2 == valid3


def test_copy_word_duplicate_rejection():
    """Test copy validation rejects duplicates."""
    validator = WordValidator()

    # Same word
    valid, msg = validator.validate_copy("cat", "cat")
    assert valid is False
    assert "duplicate" in msg.lower() or "same" in msg.lower()

    # Same word different case
    valid, msg = validator.validate_copy("CAT", "cat")
    assert valid is False

    # Different words (if valid)
    valid, msg = validator.validate_copy("dog", "cat")
    # Could be invalid if word not in dictionary, but should not be duplicate error
    if not valid:
        assert "duplicate" not in msg.lower()


def test_invalid_dictionary_word():
    """Test made-up words are rejected."""
    validator = WordValidator()

    # Made-up words unlikely to be in dictionary
    valid, msg = validator.validate("xyzabc")
    assert valid is False
    assert "not found" in msg.lower() or "dictionary" in msg.lower()

    valid, msg = validator.validate("qqqqq")
    assert valid is False
