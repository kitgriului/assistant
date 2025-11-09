"""
Скрипт для создания тестовых пользователей напрямую в базе данных
"""
import asyncio
import sys
import os
from sqlalchemy import select
from database.session import init_db, get_session
from database.models import User
from utils.auth import hash_password


async def create_test_users():
    """Создать тестовых пользователей"""
    # Инициализируем базу данных
    await init_db('sqlite+aiosqlite:///guardbot.db')
    
    async with get_session() as session:
        # Проверяем существующих пользователей
        result = await session.execute(select(User))
        existing_users = result.scalars().all()
        
        print(f"\n📋 Существующих пользователей: {len(existing_users)}")
        for user in existing_users:
            print(f"  - {user.role}: {user.login or user.name} (telegram_id={user.telegram_id})")
        
        # Создаём админа
        admin_result = await session.execute(
            select(User).where(User.login == 'admin')
        )
        admin = admin_result.scalar_one_or_none()
        
        if not admin:
            admin = User(
                telegram_id=0,  # Временно, обновится при первом логине
                role='admin',
                name='Администратор',
                login='admin',
                password_hash=hash_password('admin123'),
                is_authenticated=False
            )
            session.add(admin)
            print(f"\n✅ Создан админ: login=admin, password=admin123")
        else:
            print(f"\n⚠️  Админ уже существует: {admin.login}")
        
        # Создаём охранников
        for i in range(1, 3):
            guard_login = f'guard{i}'
            guard_result = await session.execute(
                select(User).where(User.login == guard_login)
            )
            guard = guard_result.scalar_one_or_none()
            
            if not guard:
                guard = User(
                    telegram_id=0,
                    role='guard',
                    name=f'Охранник {i}',
                    login=guard_login,
                    password_hash=hash_password('guard123'),
                    is_authenticated=False
                )
                session.add(guard)
                print(f"✅ Создан охранник: login={guard_login}, password=guard123")
            else:
                print(f"⚠️  Охранник уже существует: {guard.login}")
        
        await session.commit()
        print("\n✅ Тестовые пользователи готовы!")
        print("\n📝 Для входа используйте:")
        print("   Админ:     login=admin   password=admin123")
        print("   Охранник:  login=guard1  password=guard123")
        print("   Охранник:  login=guard2  password=guard123")


if __name__ == '__main__':
    asyncio.run(create_test_users())
