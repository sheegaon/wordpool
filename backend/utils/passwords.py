"""Simple password hashing utilities using PBKDF2."""
from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import os


def hash_password(password: str, iterations: int = 120_000) -> str:
    """Hash a password using PBKDF2-HMAC-SHA256."""
    salt = os.urandom(16)
    derived = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iterations)
    encoded_salt = base64.b64encode(salt).decode('ascii')
    encoded_hash = base64.b64encode(derived).decode('ascii')
    return f"{iterations}:{encoded_salt}:{encoded_hash}"


def verify_password(password: str, encoded: str) -> bool:
    """Verify a password against a stored PBKDF2 hash."""
    try:
        iterations_str, encoded_salt, encoded_hash = encoded.split(':')
        iterations = int(iterations_str)
        salt = base64.b64decode(encoded_salt)
        expected = base64.b64decode(encoded_hash)
    except (ValueError, TypeError, binascii.Error):
        return False

    computed = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iterations)
    return hmac.compare_digest(expected, computed)
