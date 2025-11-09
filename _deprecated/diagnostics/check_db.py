"""Быстрая проверка состояния БД."""
import asyncio
from database.session import get_session
from database.models import User, Request
from sqlalchemy import select


async def main():
    async with get_session() as session:
        # Пользователи
        users_result = await session.execute(select(User))
        users = users_result.scalars().all()
        
        print("\n" + "="*60)
        print("👥 ПОЛЬЗОВАТЕЛИ В БД:")
        print("="*60)
        if users:
            for user in users:
                print(f"ID: {user.id} | {user.name} | Роль: {user.role} | Логин: {user.login or 'N/A'}")
        else:
            print("  Нет пользователей")
        
        # Заявки
        requests_result = await session.execute(select(Request))
        requests = requests_result.scalars().all()
        
        print("\n" + "="*60)
        print("📋 ЗАЯВКИ:")
        print("="*60)
        if requests:
            for req in requests:
                print(f"ID: {req.id} | {req.name} | Статус: {req.status}")
        else:
            print("  Нет заявок")
        
        print("\n" + "="*60)
        print(f"✅ Всего пользователей: {len(users)}")
        print(f"✅ Всего заявок: {len(requests)}")
        print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
