"""Auto-seed prompt library if empty."""
from backend.database import AsyncSessionLocal
from backend.models.prompt import Prompt
from sqlalchemy import select, func
import logging

logger = logging.getLogger(__name__)


PROMPTS = [
    # Straightforward (daily life, personal goals, simple emotions)
    ("my deepest desire is to be", "simple"),
    ("success means being", "simple"),
    ("the secret to happiness is", "simple"),
    ("every day I", "simple"),
    ("I feel most alive when I'm", "simple"),
    ("the world needs more", "simple"),
    ("my favorite way to relax is with", "simple"),
    ("a perfect day starts with", "simple"),
    ("I'm most grateful for", "simple"),
    ("my biggest fear is", "simple"),
    ("when I'm stressed, I", "simple"),
    ("the best advice I ever got was", "simple"),
    ("my proudest moment was when I", "simple"),
    ("I laugh the hardest when", "simple"),
    ("my comfort food is", "simple"),
    ("the one thing I can't live without is", "simple"),
    ("on weekends I love to", "simple"),
    ("my guilty pleasure is", "simple"),
    ("I wish I had more time for", "simple"),
    ("the best part of my day is", "simple"),
    ("I feel peaceful when I", "simple"),
    ("my favorite childhood memory involves", "simple"),
    ("the thing that motivates me most is", "simple"),
    ("when I retire, I want to", "simple"),

    # Deep (philosophical, meaningful, introspective)
    ("beauty is fundamentally", "deep"),
    ("the meaning of life is", "deep"),
    ("art should be", "deep"),
    ("freedom means", "deep"),
    ("true wisdom comes from", "deep"),
    ("the essence of friendship is", "deep"),
    ("courage is facing", "deep"),
    ("happiness is ultimately", "deep"),
    ("love is best described as", "deep"),
    ("suffering teaches us about", "deep"),
    ("the purpose of education is to", "deep"),
    ("justice requires", "deep"),
    ("we are defined by our", "deep"),
    ("faith is believing in", "deep"),
    ("mortality reminds us to", "deep"),
    ("compassion begins with", "deep"),
    ("truth is found through", "deep"),
    ("legacy means leaving behind", "deep"),
    ("the human condition is defined by", "deep"),
    ("moral strength comes from", "deep"),
    ("peace is achieved through", "deep"),
    ("identity is shaped by", "deep"),
    ("hope sustains us when we", "deep"),
    ("forgiveness is ultimately about", "deep"),

    # Silly (absurd, humorous, playful nonsense)
    ("the best superpower would be to turn into", "silly"),
    ("if animals could talk, a cat would say", "silly"),
    ("the weirdest invention ever is", "silly"),
    ("my spirit animal is", "silly"),
    ("a zombie's favorite food is", "silly"),
    ("if I were a superhero, my weakness would be", "silly"),
    ("the secret ingredient in magic potions is", "silly"),
    ("aliens probably think humans are", "silly"),
    ("a pirate's worst nightmare is", "silly"),
    ("if dogs ruled the world, they would ban", "silly"),
    ("the strangest thing in my refrigerator is", "silly"),
    ("a vampire's biggest problem is", "silly"),
    ("my imaginary friend is", "silly"),
    ("if trees could move, they would", "silly"),
    ("a unicorn's favorite hobby is", "silly"),
    ("the worst superpower would be", "silly"),
    ("if socks had feelings, they would", "silly"),
    ("a dragon's biggest fear is probably", "silly"),
    ("my evil twin would definitely", "silly"),
    ("if gravity stopped working, I would", "silly"),
    ("a wizard's biggest regret is", "silly"),
    ("the monster under my bed wants", "silly"),
    ("if pizza could talk, it would say", "silly"),
    ("a ninja's biggest embarrassment is", "silly"),

    # Fun/Action (adventures, games, exciting scenarios)
    ("a spy's best gadget is", "fun"),
    ("the ultimate adventure involves", "fun"),
    ("in a fairy tale, the hero always finds", "fun"),
    ("my dream job would be", "fun"),
    ("the key to winning a game is", "fun"),
    ("a robot's daily routine includes", "fun"),
    ("if I could time travel, I'd visit the", "fun"),
    ("the coolest treasure would be", "fun"),
    ("every quest begins with", "fun"),
    ("the ultimate challenge is to", "fun"),
    ("a champion's secret weapon is", "fun"),
    ("the most exciting journey leads to", "fun"),
    ("in a competition, I always", "fun"),
    ("the perfect teammate has", "fun"),
    ("winning requires", "fun"),
    ("the greatest discovery would be finding", "fun"),
    ("every explorer needs", "fun"),
    ("the best strategy is to", "fun"),
    ("a legendary warrior carries", "fun"),
    ("the hidden level contains", "fun"),
    ("the final boss is defeated by", "fun"),
    ("the mystery is solved with", "fun"),
    ("an epic story always includes", "fun"),
    ("the power-up gives you", "fun"),

    # Abstract (conceptual, artistic, sensory, metaphorical)
    ("time feels like", "abstract"),
    ("dreams are made of", "abstract"),
    ("silence can be", "abstract"),
    ("innovation starts with", "abstract"),
    ("the color of joy is", "abstract"),
    ("echoes remind me of", "abstract"),
    ("memory tastes like", "abstract"),
    ("the shape of sadness is", "abstract"),
    ("winter sounds like", "abstract"),
    ("creativity smells like", "abstract"),
    ("the texture of hope is", "abstract"),
    ("music looks like", "abstract"),
    ("tomorrow feels like", "abstract"),
    ("loneliness tastes like", "abstract"),
    ("the weight of words is", "abstract"),
    ("inspiration arrives as", "abstract"),
    ("the rhythm of nature is", "abstract"),
    ("infinity smells like", "abstract"),
    ("the temperature of love is", "abstract"),
    ("chaos sounds like", "abstract"),
    ("the flavor of nostalgia is", "abstract"),
    ("serenity looks like", "abstract"),
    ("the speed of thought is", "abstract"),
    ("wonder feels like", "abstract"),
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
