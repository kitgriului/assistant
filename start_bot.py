"""
GuardBot Launcher - единая точка входа с защитой от конфликтов
"""
import asyncio
import logging
import sys
import os
import signal
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

from database import init_db
from handlers import register_handlers
from bot.config import settings
from utils.middlewares import (
    CallbackDeduplicationMiddleware,
    UserActionLockMiddleware,
    RateLimitMiddleware,
    ErrorHandlerMiddleware,
    RequestLoggingMiddleware,
    AlbumMiddleware,
    CommandInterruptMiddleware
)

logger = logging.getLogger(__name__)

# ============================================================================
# LOCKFILE MECHANISM - защита от multiple instances
# ============================================================================

LOCKFILE = project_root / ".bot.lock"

def create_lockfile() -> bool:
    """Создать lockfile, вернуть True если успешно (нет других экземпляров)"""
    if LOCKFILE.exists():
        try:
            # Проверяем возраст lockfile
            lock_age = datetime.now().timestamp() - LOCKFILE.stat().st_mtime
            if lock_age < 60:  # Меньше минуты
                print(f"❌ Обнаружен активный экземпляр бота (lockfile: {lock_age:.0f}s)")
                print(f"   Удалите {LOCKFILE} если бот не запущен")
                return False
            else:
                print(f"⚠️  Найден старый lockfile ({lock_age:.0f}s), удаляю...")
                LOCKFILE.unlink()
        except Exception as e:
            print(f"⚠️  Ошибка проверки lockfile: {e}")
    
    try:
        LOCKFILE.write_text(str(os.getpid()))
        return True
    except Exception as e:
        print(f"❌ Не могу создать lockfile: {e}")
        return False

def remove_lockfile():
    """Удалить lockfile при выходе"""
    try:
        if LOCKFILE.exists():
            LOCKFILE.unlink()
            logger.info("Lockfile removed")
    except Exception as e:
        logger.error(f"Error removing lockfile: {e}")

# ============================================================================
# LOGGING SETUP
# ============================================================================

def setup_logging():
    """Настройка логирования с поддержкой production режима"""
    import logging.handlers
    from pathlib import Path
    
    # Определяем уровень логирования из .env
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_to_file = os.getenv("LOG_TO_FILE", "false").lower() == "true"
    environment = os.getenv("ENVIRONMENT", "development")
    
    # Базовая настройка
    handlers = []
    
    # Console handler (всегда)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s [%(levelname)8s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    )
    handlers.append(console_handler)
    
    # File handler для production
    if log_to_file or environment == "production":
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Ротация логов: 10MB, 5 файлов
        max_bytes = int(os.getenv("LOG_MAX_BYTES", "10485760"))  # 10MB
        backup_count = int(os.getenv("LOG_BACKUP_COUNT", "5"))
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_dir / "guardbot.log",
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8"
        )
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s [%(levelname)8s] %(name)s:%(lineno)d - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
        )
        handlers.append(file_handler)
    
    # Настройка root logger
    logging.basicConfig(
        level=getattr(logging, log_level),
        handlers=handlers
    )
    
    # Уменьшаем verbose библиотек в production
    if environment == "production":
        logging.getLogger("aiogram").setLevel(logging.ERROR)
        logging.getLogger("aiosqlite").setLevel(logging.ERROR)
        logging.getLogger("sqlalchemy").setLevel(logging.ERROR)
        logging.getLogger("aiohttp").setLevel(logging.ERROR)
    else:
        logging.getLogger("aiogram").setLevel(logging.WARNING)
        logging.getLogger("aiosqlite").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
        logging.getLogger("aiohttp").setLevel(logging.WARNING)

# ============================================================================
# STARTUP & SHUTDOWN
# ============================================================================

async def on_startup():
    """Инициализация при запуске"""
    logger.info("=" * 60)
    logger.info("GuardBot Starting")
    logger.info("=" * 60)
    
    # Инициализируем БД
    await init_db(settings.db_url)
    logger.info("✅ Database initialized")

async def on_shutdown(bot: Bot):
    """Cleanup при остановке"""
    logger.info("Shutting down bot...")
    
    try:
        await bot.session.close()
        logger.info("✅ Bot session closed")
    except Exception as e:
        logger.error(f"Error closing bot session: {e}")
    
    remove_lockfile()
    logger.info("=" * 60)
    logger.info("GuardBot Stopped")
    logger.info("=" * 60)

# ============================================================================
# MAIN LOOP
# ============================================================================

async def main():
    """Главный цикл бота с защитой от конфликтов"""
    # Load environment
    load_dotenv()
    
    # Setup logging
    setup_logging()
    
    # Check lockfile
    if not create_lockfile():
        sys.exit(1)
    
    # Startup tasks
    await on_startup()
    
    print(f"🔍 Проверка токена...")
    print(f"🔑 Токен: {settings.bot_token[:10]}...{settings.bot_token[-10:]}")
    
    # Create bot without custom session (aiogram handles it internally)
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode="HTML")
    )
    
    # Test bot token
    try:
        me = await bot.get_me()
        logger.info(f"✅ Bot connected: @{me.username} ({me.full_name})")
    except Exception as e:
        logger.error(f"❌ Failed to connect to Telegram: {e}")
        remove_lockfile()
        sys.exit(1)
    
    # Force clear webhook
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("✅ Webhook cleared, pending updates dropped")
    except Exception as e:
        logger.warning(f"⚠️  Failed to clear webhook: {e}")
    
    # Create dispatcher
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Register middleware (order matters!)
    # CommandInterrupt должен быть первым для прерывания FSM
    dp.message.middleware(CommandInterruptMiddleware())
    
    # Album middleware должен быть вторым для обработки media_group
    dp.message.middleware(AlbumMiddleware(latency=0.5))
    
    dp.message.middleware(RequestLoggingMiddleware())
    dp.callback_query.middleware(RequestLoggingMiddleware())
    
    dp.message.middleware(RateLimitMiddleware(max_actions=5, window_seconds=1))
    dp.callback_query.middleware(RateLimitMiddleware(max_actions=10, window_seconds=1))
    
    dp.message.middleware(UserActionLockMiddleware())
    dp.callback_query.middleware(UserActionLockMiddleware())
    
    dp.callback_query.middleware(CallbackDeduplicationMiddleware(ttl_seconds=3))
    
    dp.message.middleware(ErrorHandlerMiddleware())
    dp.callback_query.middleware(ErrorHandlerMiddleware())
    
    logger.info("✅ Middleware registered")
    
    # Register handlers
    register_handlers(dp)
    logger.info("✅ Handlers registered")
    
    print("\n" + "=" * 60)
    print("📱 Бот запущен и готов к работе!")
    print("   Отправьте /start в Telegram для начала")
    print("   Нажмите Ctrl+C для остановки")
    print("=" * 60 + "\n")
    
    # Start polling with optimized settings
    try:
        await dp.start_polling(
            bot,
            drop_pending_updates=False,  # Уже очистили выше
            allowed_updates=["message", "callback_query", "my_chat_member"],
            polling_timeout=20,  # Reduced from 30
            handle_signals=False  # We handle signals manually
        )
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except asyncio.CancelledError:
        logger.info("Polling cancelled")
    except Exception as e:
        logger.exception(f"Unexpected error during polling: {e}")
    finally:
        await on_shutdown(bot)

# ============================================================================
# ENTRY POINT
# ============================================================================

def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
    print("\n\n⚠️  Получен сигнал остановки...")
    remove_lockfile()
    sys.exit(0)

if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен пользователем")
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        remove_lockfile()
        sys.exit(1)
