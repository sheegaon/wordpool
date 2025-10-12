#!/usr/bin/env python3
"""Auto-seed prompts if database is empty (non-interactive)."""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.prompt_seeder import auto_seed_prompts_if_empty


if __name__ == "__main__":
    asyncio.run(auto_seed_prompts_if_empty())
