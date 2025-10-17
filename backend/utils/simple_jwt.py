"""JWT encode/decode helpers using PyJWT library."""
from __future__ import annotations

from typing import Any, Dict

import jwt
from jwt.exceptions import ExpiredSignatureError as PyJWTExpiredSignatureError
from jwt.exceptions import InvalidTokenError as PyJWTInvalidTokenError


class InvalidTokenError(Exception):
    """Raised when a JWT cannot be validated."""


class ExpiredSignatureError(InvalidTokenError):
    """Raised when a JWT has expired."""


def encode_jwt(payload: Dict[str, Any], secret: str, algorithm: str = "HS256") -> str:
    """Encode a JWT using PyJWT.

    Args:
        payload: The JWT payload/claims
        secret: The secret key for signing
        algorithm: The algorithm to use (default: HS256)

    Returns:
        The encoded JWT string
    """
    return jwt.encode(payload, secret, algorithm=algorithm)


def decode_jwt(token: str, secret: str, algorithms: list[str] | None = None) -> Dict[str, Any]:
    """Decode and validate a JWT using PyJWT.

    Args:
        token: The JWT token to decode
        secret: The secret key for verification
        algorithms: List of allowed algorithms (default: ["HS256"])

    Returns:
        The decoded payload

    Raises:
        ExpiredSignatureError: If the token has expired
        InvalidTokenError: If the token is invalid
    """
    algorithms = algorithms or ["HS256"]

    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=algorithms,
            options={
                "verify_signature": True,
                "verify_exp": True,
                "require_exp": False,  # Don't require exp claim, but verify if present
            }
        )
        return payload
    except PyJWTExpiredSignatureError as exc:
        raise ExpiredSignatureError("token_expired") from exc
    except (PyJWTInvalidTokenError, ValueError, TypeError) as exc:
        raise InvalidTokenError("invalid_token") from exc
