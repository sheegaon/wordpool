"""Password hashing utilities using passlib."""
from __future__ import annotations

from passlib.context import CryptContext

# Use argon2 (recommended) with bcrypt as fallback
# Argon2 is the winner of the Password Hashing Competition and is the current best practice
pwd_context = CryptContext(
    schemes=["argon2", "bcrypt"],
    deprecated="auto",
    argon2__memory_cost=65536,  # 64 MB
    argon2__time_cost=3,  # 3 iterations
    argon2__parallelism=4,  # 4 parallel threads
)


def hash_password(password: str) -> str:
    """Hash a password using argon2 (with bcrypt fallback)."""
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against a stored hash.

    Automatically handles verification and upgrades deprecated hashes.
    """
    try:
        return pwd_context.verify(password, password_hash)
    except (ValueError, TypeError):
        return False


def needs_update(password_hash: str) -> bool:
    """Check if a password hash needs to be upgraded to current algorithm."""
    return pwd_context.needs_update(password_hash)
