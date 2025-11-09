"""Скрипт для проверки и сброса webhook"""
import asyncio
import os
from dotenv import load_dotenv
from aiogram import Bot

load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')

async def fix_webhook():
    bot = Bot(token=BOT_TOKEN)
    
    try:
        # Проверяем текущий webhook
        webhook_info = await bot.get_webhook_info()
        print(f"\n📡 Текущий webhook: {webhook_info.url or 'НЕТ'}")
        
        if webhook_info.url:
            print(f"⚠️  Webhook активен! Удаляю...")
            await bot.delete_webhook(drop_pending_updates=True)
            print("✅ Webhook удалён")
        else:
            print("✅ Webhook не установлен")
        
        # Проверяем pending updates
        print(f"\n📬 Ожидающих обновлений: {webhook_info.pending_update_count}")
        
        # Очищаем pending updates
        await bot.delete_webhook(drop_pending_updates=True)
        print("✅ Все ожидающие обновления очищены")
        
        # Проверяем информацию о боте
        me = await bot.get_me()
        print(f"\n🤖 Бот: @{me.username} ({me.first_name})")
        print(f"   ID: {me.id}")
        
    finally:
        await bot.session.close()

if __name__ == '__main__':
    asyncio.run(fix_webhook())
