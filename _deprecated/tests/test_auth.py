"""Простой тест системы аутентификации без запуска бота."""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from sqlalchemy import select
from database.session import get_session, engine
from database.models import Base, User
from utils.auth import hash_password, verify_password


async def test_auth_system():
    """Тест системы аутентификации."""
    load_dotenv()
    
    print("="*60)
    print("🧪 ТЕСТ СИСТЕМЫ АУТЕНТИФИКАЦИИ")
    print("="*60)
    
    # Создаем таблицы
    print("\n1️⃣ Создание таблиц БД...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Таблицы созданы")
    
    # Создаём тестовых пользователей
    print("\n2️⃣ Создание тестовых пользователей...")
    
    test_users = [
        {
            "login": "admin",
            "password": "admin123",
            "name": "Тестовый Администратор",
            "role": "admin",
            "telegram_id": 0
        },
        {
            "login": "guard1",
            "password": "guard123",
            "name": "Тестовый Охранник 1",
            "role": "guard",
            "telegram_id": 0
        },
        {
            "telegram_id": 123456789,
            "name": "Тестовый Гость",
            "role": "guest",
            "is_authenticated": True
        }
    ]
    
    async with get_session() as session:
        for user_data in test_users:
            # Проверяем существование
            if "login" in user_data:
                result = await session.execute(
                    select(User).where(User.login == user_data["login"])
                )
            else:
                result = await session.execute(
                    select(User).where(User.telegram_id == user_data["telegram_id"])
                )
            
            existing = result.scalar_one_or_none()
            if existing:
                print(f"  ⚠️  Пользователь уже существует: {user_data.get('login') or user_data.get('name')}")
                continue
            
            # Создаём нового
            if "password" in user_data:
                password_hash = hash_password(user_data["password"])
                user = User(
                    telegram_id=user_data["telegram_id"],
                    login=user_data["login"],
                    password_hash=password_hash,
                    name=user_data["name"],
                    role=user_data["role"],
                    is_authenticated=False
                )
            else:
                user = User(
                    telegram_id=user_data["telegram_id"],
                    name=user_data["name"],
                    role=user_data["role"],
                    is_authenticated=user_data["is_authenticated"]
                )
            
            session.add(user)
            print(f"  ✅ Создан: {user_data.get('login') or user_data.get('name')} ({user_data['role']})")
        
        await session.commit()
    
    # Тестируем аутентификацию
    print("\n3️⃣ Тест проверки паролей...")
    
    async with get_session() as session:
        result = await session.execute(
            select(User).where(User.login == "admin")
        )
        admin = result.scalar_one_or_none()
        
        if admin:
            # Правильный пароль
            if verify_password("admin123", admin.password_hash):
                print("  ✅ Правильный пароль принят")
            else:
                print("  ❌ Ошибка: правильный пароль отклонён!")
            
            # Неправильный пароль
            if not verify_password("wrong_password", admin.password_hash):
                print("  ✅ Неправильный пароль отклонён")
            else:
                print("  ❌ Ошибка: неправильный пароль принят!")
    
    # Показываем всех пользователей
    print("\n4️⃣ Список пользователей в БД:")
    print("-"*60)
    
    async with get_session() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
        
        print(f"{'ID':<5} {'Login':<12} {'Name':<25} {'Role':<8} {'TG ID':<12}")
        print("-"*60)
        for user in users:
            login = user.login or "—"
            print(f"{user.id:<5} {login:<12} {user.name or '—':<25} {user.role:<8} {user.telegram_id:<12}")
    
    print("-"*60)
    print("\n✅ Тест завершён успешно!")
    print("\n📋 УЧЁТНЫЕ ДАННЫЕ ДЛЯ ТЕСТИРОВАНИЯ:")
    print("   Администратор: admin / admin123")
    print("   Охранник: guard1 / guard123")
    print("   Гость: telegram_id = 123456789")
    print("\n🚀 Теперь можно запустить бота: python run_bot.py")


if __name__ == "__main__":
    asyncio.run(test_auth_system())
