"""
Shared prompt building utilities for AI copy generation.

This module provides reusable prompt construction logic used by both
Gemini and OpenAI AI providers, eliminating code duplication.
"""


def build_copy_prompt(original_phrase: str, prompt_text: str) -> str:
    """
    Build structured prompt for Think Alike gameplay copy generation.

    Args:
        original_phrase: The original phrase that was submitted for the prompt
        prompt_text: The prompt text that the original phrase was created for

    Returns:
        A formatted prompt string for AI copy generation
    """
    return f"""You are playing a word game. Given an original phrase for a prompt,
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

Generate ONE alternative phrase only:"""
