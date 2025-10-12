"""Auto-seed prompt library if empty."""
from backend.database import AsyncSessionLocal
from backend.models.prompt import Prompt
from sqlalchemy import select, func
import logging

logger = logging.getLogger(__name__)


# Prompts from PROMPT_LIBRARY.md
PROMPTS = [
    # Straightforward
    ("my deepest desire is to be (a/an)", "simple"),
    ("success means being", "simple"),
    ("the secret to happiness is (a/an)", "simple"),
    ("every day I", "simple"),
    ("I feel most alive when I'm", "simple"),
    ("the world needs more", "simple"),
    ("my favorite way to relax is with (a/an)", "simple"),
    ("a perfect day starts with", "simple"),

    # Deep
    ("beauty is fundamentally", "deep"),
    ("the meaning of life is", "deep"),
    ("art should be", "deep"),
    ("freedom means", "deep"),
    ("true wisdom comes from", "deep"),
    ("the essence of friendship is", "deep"),
    ("courage is facing", "deep"),
    ("happiness is ultimately", "deep"),

    # Silly
    ("the best superpower would be to turn into (a/an)", "silly"),
    ("if animals could talk, a cat would say", "silly"),
    ("the weirdest invention ever is (a/an)", "silly"),
    ("my spirit animal is (a/an)", "silly"),
    ("a zombie's favorite food is", "silly"),
    ("if I were a superhero, my weakness would be", "silly"),
    ("the secret ingredient in magic potions is", "silly"),
    ("aliens probably think humans are", "silly"),

    # Fun/Action
    ("a spy's best gadget is (a/an)", "fun"),
    ("the ultimate adventure involves", "fun"),
    ("in a fairy tale, the hero always finds (a/an)", "fun"),
    ("my dream job would be (a/an)", "fun"),
    ("the key to winning a game is", "fun"),
    ("a robot's daily routine includes", "fun"),
    ("if I could time travel, I'd visit the", "fun"),

    # Abstract
    ("time feels like (a/an)", "abstract"),
    ("dreams are made of", "abstract"),
    ("silence can be", "abstract"),
    ("innovation starts with (a/an)", "abstract"),
    ("the color of joy is", "abstract"),
    ("echoes remind me of", "abstract"),
]


async def auto_seed_prompts_if_empty():
    """Automatically seed prompts if the database is empty.

    This runs on application startup and only seeds if no prompts exist.
    Safe to run multiple times - idempotent operation.
    """
    try:
        async with AsyncSessionLocal() as db:
            # Check if prompts already exist
            result = await db.execute(select(func.count(Prompt.prompt_id)))
            count = result.scalar()

            if count > 0:
                logger.info(f"Prompt library already seeded with {count} prompts")
                return

            logger.info("No prompts found, auto-seeding prompt library...")

            # Insert new prompts
            for text, category in PROMPTS:
                prompt = Prompt(
                    text=text,
                    category=category,
                )
                db.add(prompt)

            await db.commit()
            logger.info(f"✓ Auto-seeded {len(PROMPTS)} prompts")

            # Show summary
            result = await db.execute(
                select(Prompt.category, func.count(Prompt.prompt_id))
                .group_by(Prompt.category)
            )
            logger.info("Prompts by category:")
            for category, prompt_count in result:
                logger.info(f"  {category}: {prompt_count}")

    except Exception as e:
        logger.error(f"Failed to auto-seed prompts: {e}")
        logger.error("You can manually seed with: python3 scripts/seed_prompts.py")
