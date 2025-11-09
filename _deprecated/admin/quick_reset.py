"""Быстрый скрипт для сброса webhook."""
import requests
import os
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("BOT_TOKEN")

print("🔧 Сброс webhook для бота...")
print(f"🔑 Токен: {token[:10]}...")

# Удаляем webhook
url = f"https://api.telegram.org/bot{token}/deleteWebhook?drop_pending_updates=true"
response = requests.get(url)

if response.status_code == 200:
    result = response.json()
    if result.get("ok"):
        print("✅ Webhook удалён успешно!")
        print(f"   Результат: {result.get('result')}")
        print(f"   Описание: {result.get('description', 'N/A')}")
    else:
        print(f"❌ Ошибка: {result}")
else:
    print(f"❌ HTTP ошибка: {response.status_code}")

print("\n🚀 Теперь можно запустить бота!")
