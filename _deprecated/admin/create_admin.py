"""Скрипт для быстрой регистрации админа"""
import asyncio
import sys
from database.session import get_session, init_db
from database.models import User

async def create_admin():
    # Инициализируем БД
    await init_db("sqlite+aiosqlite:///./guardbot.db")
    print("✅ База данных инициализирована")
    
    telegram_id = 83579209  # Ваш Telegram ID
    phone_number = "+79999812358"
    name = "Седых Никита Дмитриевич"
    
    async with get_session() as session:
        # Проверяем, существует ли пользователь
        from sqlalchemy import select
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        
        if user:
            # Обновляем роль
            user.role = "admin"
            print(f"✅ Пользователь {name} обновлен. Роль: admin")
        else:
            # Создаем нового
            user = User(
                telegram_id=telegram_id,
                phone_number=phone_number,
                name=name,
                role="admin"
            )
            session.add(user)
            print(f"✅ Создан новый админ: {name}")
        
        await session.commit()
        print(f"📱 Telegram ID: {telegram_id}")
        print(f"☎️ Телефон: {phone_number}")
        print(f"👤 ФИО: {name}")
        print(f"🔑 Роль: admin")

if __name__ == "__main__":
    asyncio.run(create_admin())
