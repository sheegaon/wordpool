"""Seed prompt library from PROMPT_LIBRARY.md."""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import AsyncSessionLocal
from backend.models.prompt import Prompt
from sqlalchemy import select
import uuid


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


async def seed_prompts():
    """Seed prompt library."""
    async with AsyncSessionLocal() as db:
        # Check if prompts already exist
        result = await db.execute(select(Prompt))
        existing = result.scalars().all()

        if existing:
            print(f"Found {len(existing)} existing prompts")
            response = input("Clear and reseed? (y/N): ")
            if response.lower() != 'y':
                print("Aborted")
                return

            # Delete existing
            for prompt in existing:
                await db.delete(prompt)
            await db.commit()
            print("Cleared existing prompts")

        # Insert new prompts
        for text, category in PROMPTS:
            prompt = Prompt(
                text=text,
                category=category,
            )
            db.add(prompt)

        await db.commit()
        print(f"Seeded {len(PROMPTS)} prompts")

        # Show summary
        from sqlalchemy import func
        result = await db.execute(
            select(Prompt.category, func.count(Prompt.prompt_id))
            .group_by(Prompt.category)
        )
        print("\nPrompts by category:")
        for category, count in result:
            print(f"  {category}: {count}")


if __name__ == "__main__":
    print("Seeding prompt library...")
    asyncio.run(seed_prompts())
    print("Done!")
