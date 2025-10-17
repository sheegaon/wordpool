"""Minimal JWT encode/decode helpers (HS256 only)."""
from __future__ import annotations

import base64
import json
import time
import hmac
import hashlib
from typing import Any, Dict


class InvalidTokenError(Exception):
    """Raised when a JWT cannot be validated."""


class ExpiredSignatureError(InvalidTokenError):
    """Raised when a JWT has expired."""


def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64decode(segment: str) -> bytes:
    padding = '=' * (-len(segment) % 4)
    return base64.urlsafe_b64decode(segment + padding)


def encode_jwt(payload: Dict[str, Any], secret: str, algorithm: str = "HS256") -> str:
    """Encode a JWT using HS256."""

    if algorithm != "HS256":
        raise ValueError("Only HS256 is supported")

    header = {"typ": "JWT", "alg": algorithm}
    header_segment = _b64encode(json.dumps(header, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    payload_segment = _b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_segment}.{payload_segment}".encode("utf-8")
    signature = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    signature_segment = _b64encode(signature)
    return f"{header_segment}.{payload_segment}.{signature_segment}"


def decode_jwt(token: str, secret: str, algorithms: list[str] | None = None) -> Dict[str, Any]:
    """Decode and validate a JWT."""

    algorithms = algorithms or ["HS256"]
    if "HS256" not in algorithms:
        raise InvalidTokenError("Unsupported algorithm")

    try:
        header_segment, payload_segment, signature_segment = token.split(".")
    except ValueError as exc:
        raise InvalidTokenError("Token structure invalid") from exc

    signing_input = f"{header_segment}.{payload_segment}".encode("utf-8")
    expected_signature = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    signature = _b64decode(signature_segment)
    if not hmac.compare_digest(expected_signature, signature):
        raise InvalidTokenError("Signature verification failed")

    try:
        payload_bytes = _b64decode(payload_segment)
        payload = json.loads(payload_bytes.decode("utf-8"))
    except (ValueError, json.JSONDecodeError) as exc:
        raise InvalidTokenError("Payload decode failed") from exc

    exp = payload.get("exp")
    if exp is not None and time.time() >= float(exp):
        raise ExpiredSignatureError("token_expired")

    return payload
