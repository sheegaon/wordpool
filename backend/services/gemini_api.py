"""
Helper for interacting with the Gemini generative API.

Provides structured gameplay decisions with error handling and fallback logic
for the Think Alike bot system.
"""

import json
import logging
import os
import sys
from dataclasses import dataclass

from google import genai
from google.genai import types

__all__ = ["GeminiError", "GeminiSuggestion", "generate", "generate_copy"]

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


class GeminiError(RuntimeError):
    """Raised when the Gemini API cannot be contacted or returns an error."""


@dataclass
class GeminiSuggestion:
    """Normalized response from Gemini for gameplay decisions."""

    choice_index: int
    reason: str
    raw_text: str


def _build_prompt(original_phrase: str, prompt_text: str) -> str:
    """Build structured prompt for Think Alike gameplay decisions."""
    system_prompt = f"""
            You are playing a word game. Given an original phrase for a prompt, 
            create a similar but different phrase that could fool voters.

            Rules:
            - 1-15 characters per word
            - 1-5 words total
            - Letters and spaces only
            - Must pass dictionary validation
            - Should be similar enough to be believable as the original
            - But different enough to not be identical

            Original phrase: "{original_phrase}"
            Prompt context: "{prompt_text}"

            Generate ONE alternative phrase only:
            """

    return system_prompt


async def generate_copy(
        self, original_phrase: str, prompt_text: str,
        model: str = "gemini-2.5-flash-lite", timeout: int = 30,
) -> GeminiSuggestion:
    """Call Gemini and return the recommended noun index with structured response."""
    if not GEMINI_API_KEY:
        raise GeminiError("GEMINI_API_KEY environment variable must be set")

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        prompt = _build_prompt(original_phrase, prompt_text)

        contents = [
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=prompt)],
            ),
        ]

        generate_content_config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_budget=0),
        )

        output_text = ""
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
        ):
            if chunk.text is not None:
                output_text += chunk.text

        if not output_text:
            raise GeminiError("Gemini API returned empty response")

    except Exception as exc:
        if isinstance(exc, GeminiError):
            raise
        raise GeminiError(f"Failed to contact Gemini API: {exc}") from exc

    # Parse JSON response with fallback
    cleaned = output_text.strip().split("```")[-1].strip()
    try:
        parsed = json.loads(cleaned)
        choice_index = int(parsed.get("choice_index", 0))
        reason = str(parsed.get("reason", cleaned))
    except json.JSONDecodeError:
        logging.warning("Gemini response was not valid JSON, falling back to best-effort parse: %s", cleaned)
        # Extract first integer from response
        digits = [int(token) for token in cleaned.replace("\n", " ").split() if token.isdigit()]
        choice_index = digits[0] if digits else 0
        reason = cleaned

    return GeminiSuggestion(choice_index=choice_index, reason=reason, raw_text=output_text)


def generate(input_text: str) -> str:
    """Legacy interface for backwards compatibility."""
    if not GEMINI_API_KEY:
        raise GeminiError("GEMINI_API_KEY environment variable must be set")

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        model = "gemini-2.5-flash-lite"
        contents = [
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=input_text)],
            ),
        ]

        generate_content_config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_budget=0),
        )

        output_text = ""
        for chunk in client.models.generate_content_stream(
                model=model,
                contents=contents,
                config=generate_content_config,
        ):
            if chunk.text is not None:
                output_text += chunk.text

        return output_text

    except Exception as exc:
        raise GeminiError(f"Failed to generate content: {exc}") from exc


if __name__ == "__main__":
    if len(sys.argv) > 1:
        result = generate(sys.argv[1])
        print(result)
    else:
        print("Usage: python gemini_api.py <input_text>")
