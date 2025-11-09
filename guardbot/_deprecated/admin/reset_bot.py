"""Сброс webhook и очистка конфликтов Telegram бота."""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from bot.config import settings


async def reset_bot():
    """Сбросить webhook и удалить pending updates."""
    print("🔧 Сброс состояния бота...")
    
    bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode="HTML"))
    
    try:
        # Удаляем webhook
        print("📍 Удаление webhook...")
        await bot.delete_webhook(drop_pending_updates=True)
        print("✅ Webhook удалён, pending updates очищены")
        
        # Получаем информацию о боте
        me = await bot.get_me()
        print(f"\n✅ Бот готов к запуску:")
        print(f"   ID: {me.id}")
        print(f"   Username: @{me.username}")
        print(f"   Name: {me.full_name}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        await bot.session.close()
    
    print("\n🚀 Теперь можно запустить бота: .\.venv\bin\python run_bot.py")


if __name__ == "__main__":
    asyncio.run(reset_bot())
