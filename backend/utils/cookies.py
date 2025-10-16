"""HTTP cookie helpers."""
from fastapi import Response

from backend.config import get_settings


def set_refresh_cookie(response: Response, token: str, *, expires_days: int | None = None) -> None:
    """Set the refresh token cookie with secure defaults."""

    settings = get_settings()
    days = expires_days or settings.refresh_token_exp_days
    max_age = days * 24 * 60 * 60
    response.set_cookie(
        key=settings.refresh_token_cookie_name,
        value=token,
        httponly=True,
        secure=settings.environment != "development",
        samesite="lax",
        max_age=max_age,
        expires=max_age,
        path="/",
    )


def clear_refresh_cookie(response: Response) -> None:
    """Remove the refresh token cookie from the client."""

    settings = get_settings()
    response.delete_cookie(
        key=settings.refresh_token_cookie_name,
        path="/",
    )
