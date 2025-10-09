"""Custom exceptions for the application."""


class WordPoolException(Exception):
    """Base exception for WordPool application."""
    pass


class InsufficientBalanceError(WordPoolException):
    """Player does not have enough balance for operation."""
    pass


class AlreadyInRoundError(WordPoolException):
    """Player is already in an active round."""
    pass


class RoundNotFoundError(WordPoolException):
    """Round does not exist or player doesn't have access."""
    pass


class RoundExpiredError(WordPoolException):
    """Round has expired past grace period."""
    pass


class InvalidWordError(WordPoolException):
    """Word is invalid (not in dictionary, wrong format, etc.)."""
    pass


class DuplicateWordError(WordPoolException):
    """Copy word matches original word."""
    pass


class MaxOutstandingPromptsError(WordPoolException):
    """Player has reached maximum outstanding prompts."""
    pass


class NoPromptsAvailableError(WordPoolException):
    """No prompts waiting in queue for copy round."""
    pass


class NoWordsetsAvailableError(WordPoolException):
    """No wordsets waiting in queue for voting."""
    pass


class AlreadyVotedError(WordPoolException):
    """Player has already voted on this wordset."""
    pass


class DailyBonusNotAvailableError(WordPoolException):
    """Daily bonus has already been claimed today."""
    pass


class SelfVotingError(WordPoolException):
    """Cannot vote on own wordset."""
    pass
