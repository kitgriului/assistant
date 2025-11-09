"""Script to initialize staff users (guards and admins) in the database."""
import asyncio
import sys
import os

# Добавляем корневую директорию в PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from sqlalchemy import select
from database.session import get_session, engine
from database.models import Base, User
from utils.auth import hash_password
from bot.config import settings


async def init_staff_users():
    """Инициализация сотрудников (охранников и администраторов)."""
    load_dotenv()
    
    # Создаем таблицы если их нет
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    print("🔧 Инициализация пользователей системы...\n")
    
    # Список пользователей для создания
    staff_users = [
        {
            "login": "admin",
            "password": "admin123",  # ВАЖНО: Сменить после первого входа!
            "name": "Администратор системы",
            "role": "admin"
        },
        {
            "login": "guard1",
            "password": "guard123",  # ВАЖНО: Сменить после первого входа!
            "name": "Охранник 1",
            "role": "guard"
        },
        {
            "login": "guard2",
            "password": "guard123",  # ВАЖНО: Сменить после первого входа!
            "name": "Охранник 2",
            "role": "guard"
        }
    ]
    
    async with get_session() as session:
        for user_data in staff_users:
            # Проверяем, существует ли пользователь
            result = await session.execute(
                select(User).where(User.login == user_data["login"])
            )
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                print(f"⚠️  Пользователь '{user_data['login']}' уже существует, пропускаем...")
                continue
            
            # Создаем нового пользователя
            password_hash = hash_password(user_data["password"])
            
            new_user = User(
                telegram_id=0,  # Будет обновлен при первом логине
                login=user_data["login"],
                password_hash=password_hash,
                name=user_data["name"],
                role=user_data["role"],
                is_authenticated=False
            )
            
            session.add(new_user)
            print(f"✅ Создан {user_data['role']}: {user_data['login']} ({user_data['name']})")
        
        await session.commit()
    
    print("\n" + "="*60)
    print("📋 УЧЕТНЫЕ ДАННЫЕ ДЛЯ ВХОДА:")
    print("="*60)
    for user_data in staff_users:
        print(f"\n{user_data['role'].upper()}: {user_data['name']}")
        print(f"  Логин:  {user_data['login']}")
        print(f"  Пароль: {user_data['password']}")
    print("\n" + "="*60)
    print("⚠️  ВАЖНО: Смените пароли после первого входа!")
    print("="*60)


async def add_custom_user():
    """Интерактивное добавление пользователя."""
    print("\n📝 Добавление нового пользователя\n")
    
    login = input("Введите логин: ").strip()
    if not login:
        print("❌ Логин не может быть пустым!")
        return
    
    # Проверяем существование
    async with get_session() as session:
        result = await session.execute(
            select(User).where(User.login == login)
        )
        if result.scalar_one_or_none():
            print(f"❌ Пользователь с логином '{login}' уже существует!")
            return
    
    password = input("Введите пароль: ").strip()
    if len(password) < 4:
        print("❌ Пароль должен содержать минимум 4 символа!")
        return
    
    name = input("Введите ФИО: ").strip()
    if not name:
        print("❌ ФИО не может быть пустым!")
        return
    
    print("\nВыберите роль:")
    print("1. Admin (администратор)")
    print("2. Guard (охранник)")
    role_choice = input("Введите номер (1 или 2): ").strip()
    
    role = "admin" if role_choice == "1" else "guard"
    
    # Создаем пользователя
    async with get_session() as session:
        password_hash = hash_password(password)
        new_user = User(
            telegram_id=0,
            login=login,
            password_hash=password_hash,
            name=name,
            role=role,
            is_authenticated=False
        )
        session.add(new_user)
        await session.commit()
    
    print(f"\n✅ Пользователь успешно создан!")
    print(f"   Логин: {login}")
    print(f"   Роль: {role}")


async def list_users():
    """Показать список всех пользователей."""
    async with get_session() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
        
        if not users:
            print("📭 Пользователей не найдено.")
            return
        
        print("\n" + "="*80)
        print(f"{'ID':<5} {'Login':<15} {'Name':<25} {'Role':<10} {'TG ID':<12}")
        print("="*80)
        
        for user in users:
            print(f"{user.id:<5} {user.login or 'N/A':<15} {user.name or 'N/A':<25} "
                  f"{user.role:<10} {user.telegram_id:<12}")
        
        print("="*80)


async def main():
    """Главная функция."""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "init":
            await init_staff_users()
        elif command == "add":
            await add_custom_user()
        elif command == "list":
            await list_users()
        else:
            print(f"❌ Неизвестная команда: {command}")
            print_usage()
    else:
        print_usage()


def print_usage():
    """Показать справку по использованию."""
    print("\n📖 Использование:")
    print("  python init_users.py init  - Создать начальных пользователей")
    print("  python init_users.py add   - Добавить пользователя")
    print("  python init_users.py list  - Показать список пользователей")
    print()


if __name__ == "__main__":
    asyncio.run(main())
