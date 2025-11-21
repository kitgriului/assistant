#!/usr/bin/env python3
"""
Entry point for Whisper Bot.
This script adds the src directory to Python path and starts the bot.
"""

import sys
import asyncio
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Import and run main
from main import main

if __name__ == "__main__":
    asyncio.run(main())
