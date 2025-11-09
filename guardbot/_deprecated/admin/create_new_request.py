#!/usr/bin/env python3
"""Создание новой тестовой заявки"""
import asyncio
import sys
import os

# Добавляем корневую директорию в PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import init_db
from database.models import Request as DBRequest
from database.session import get_session


async def create_test_request():
    """Создаем новую тестовую заявку"""
    print("🔍 Создание новой тестовой заявки...")
    
    await init_db("sqlite+aiosqlite:///./guardbot.db")
    
    async with get_session() as session:
        # Создаем новую заявку
        test_request = DBRequest(
            name="Новый Тестер", 
            purpose="Тестирование нового аппрува", 
            datetime="2025-10-22 22:00",
            photo="data/media/new_test.jpg",
            status="pending"
        )
        session.add(test_request)
        await session.commit()
        await session.refresh(test_request)
        
        print(f"✅ Создана новая заявка с ID: {test_request.id}")
        print(f"📝 Имя: {test_request.name}")
        print(f"📝 Статус: {test_request.status}")
        
        return test_request.id


async def list_all_requests():
    """Показываем все заявки"""
    print("\n📋 Все заявки в базе данных:")
    
    async with get_session() as session:
        result = await session.execute(DBRequest.__table__.select())
        rows = result.fetchall()
        
        for row in rows:
            status_emoji = "✅" if row.status == "approved" else "⏳"
            print(f"   {status_emoji} ID: {row.id} | {row.name} | {row.status}")


async def main():
    print("🚀 Создание новой заявки для тестирования\n")
    
    new_id = await create_test_request()
    await list_all_requests()
    
    print(f"\n🎯 Теперь используйте команду: /approve {new_id}")
    print("   Эта заявка имеет статус 'pending' и должна сгенерировать QR код")


if __name__ == "__main__":
    asyncio.run(main())