"""Bot entrypoint: initializes bot, dispatcher, and registers handlers.

This is the main entry point for the GuardBot application. It handles:
- Environment loading (.env file)
- Logging configuration
- Database initialization
- Bot and dispatcher setup
- Handler registration
- Graceful shutdown

Usage:
    python -m bot.main
    
    Or with custom environment:
    BOT_TOKEN=xxx python -m bot.main
"""
import asyncio
import logging
import os
import sys
from typing import NoReturn

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import init_db
from handlers import register_handlers
from bot.config import settings


logger = logging.getLogger(__name__)


def setup_logging() -> None:
    """Configure application logging.
    
    Sets up structured logging with timestamps and appropriate levels.
    Uses log level from settings.
    """
    logging.basicConfig(
        level=settings.log_level_int,
        format="%(asctime)s [%(levelname)8s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    
    # Reduce noise from external libraries
    logging.getLogger("aiogram").setLevel(logging.WARNING)
    logging.getLogger("aiosqlite").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)


async def on_startup() -> None:
    """Execute startup tasks.
    
    Initializes database and logs startup information.
    """
    logger.info("=" * 60)
    logger.info("GuardBot starting up")
    logger.info("=" * 60)
    logger.info(f"Database: {settings.db_url}")
    logger.info(f"Log level: {settings.log_level}")
    logger.info(f"Debug mode: {settings.debug}")
    
    # Initialize database
    await init_db(settings.db_url)
    logger.info("Database initialized successfully")


async def on_shutdown(bot: Bot) -> None:
    """Execute shutdown tasks.
    
    Args:
        bot: Bot instance to clean up
    """
    logger.info("GuardBot shutting down...")
    await bot.session.close()
    logger.info("Bot session closed")


async def main() -> NoReturn:
    """Main application entry point.
    
    Sets up and runs the bot with proper error handling and cleanup.
    """
    # Load environment variables from .env file
    load_dotenv()
    
    # Setup logging
    setup_logging()
    
    # Run startup tasks
    await on_startup()
    
    # Create bot instance with HTML parse mode
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    # Create dispatcher with memory storage
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Register all handlers
    register_handlers(dp)
    logger.info("All handlers registered")
    
    try:
        # Start polling
        logger.info("Starting bot polling...")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.exception(f"Unexpected error during polling: {e}")
        raise
    finally:
        # Cleanup
        await on_shutdown(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)
