"""Password hashing utilities using bcrypt."""
from __future__ import annotations

import bcrypt


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against a stored hash."""
    try:
        password_bytes = password.encode('utf-8')
        hash_bytes = password_hash.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hash_bytes)
    except (ValueError, TypeError, AttributeError):
        return False


def needs_update(password_hash: str) -> bool:
    """Check if a password hash needs to be upgraded to current algorithm.

    With bcrypt, hashes don't typically need updating unless you want to
    increase the cost factor. This function always returns False for now.
    """
    return False
