#!/usr/bin/env python3
"""Проверка базы данных и тест команды approve"""
import asyncio
import sys
import os

# Добавляем корневую директорию в PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import init_db
from database.models import Request as DBRequest
from database.session import get_session


async def check_database():
    """Проверяем состояние базы данных"""
    print("🔍 Проверка базы данных...")
    
    await init_db("sqlite+aiosqlite:///./guardbot.db")
    
    async with get_session() as session:
        # Получаем все заявки
        result = await session.execute(DBRequest.__table__.select())
        rows = result.fetchall()
        
        if not rows:
            print("📝 База данных пуста. Создаем тестовую заявку...")
            # Создаем тестовую заявку
            test_request = DBRequest(
                name="Тест Тестович", 
                purpose="Тестирование аппрува", 
                datetime="2025-10-22 15:00",
                photo="data/media/test.jpg",
                status="pending"
            )
            session.add(test_request)
            await session.commit()
            await session.refresh(test_request)
            print(f"✅ Создана заявка с ID: {test_request.id}")
        else:
            print(f"📋 Найдено заявок: {len(rows)}")
            for row in rows:
                print(f"   ID: {row.id}, Имя: {row.name}, Статус: {row.status}")


async def test_approve_logic():
    """Тестируем логику команды approve"""
    print("\n🔧 Тест логики команды /approve...")
    
    # Имитируем команду "/approve 1"
    message_text = "/approve 1"
    args = message_text.split()
    
    if len(args) != 2 or not args[1].isdigit():
        print("❌ Неправильный формат команды")
        return False
        
    req_id = int(args[1])
    print(f"🎯 Ищем заявку с ID: {req_id}")
    
    async with get_session() as session:
        req = await session.get(DBRequest, req_id)
        if not req:
            print(f"❌ Заявка с id={req_id} не найдена.")
            return False
            
        print(f"✅ Заявка найдена: {req.name}, статус: {req.status}")
        
        if req.status == "approved":
            print(f"⚠️ Заявка уже одобрена.")
            return True
            
        # Одобряем заявку
        req.status = "approved"
        await session.commit()
        print(f"✅ Заявка {req.id} одобрена!")
        
        # Тестируем генерацию QR
        try:
            from utils.qr import generate_qr_bytes
            import tempfile
            
            qr = generate_qr_bytes(f"request:{req.id}")
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                tmp.write(qr.read())
                tmp_path = tmp.name
            
            print(f"✅ QR код сгенерирован: {tmp_path}")
            print(f"📏 Размер файла: {os.path.getsize(tmp_path)} байт")
            
            # Удаляем временный файл
            os.remove(tmp_path)
            return True
            
        except Exception as e:
            print(f"❌ Ошибка генерации QR: {e}")
            return False


async def main():
    print("🚀 Диагностика команды /approve\n")
    
    await check_database()
    success = await test_approve_logic()
    
    if success:
        print("\n🎉 Логика команды /approve работает корректно!")
        print("\n💡 Возможные причины отсутствия QR кода:")
        print("   1. Бот не получает команды из-за конфликта соединений")
        print("   2. Заявка с указанным ID не существует")
        print("   3. Заявка уже была одобрена")
        print("\n🔧 Рекомендации:")
        print("   1. Подождите 5 минут перед запуском бота")
        print("   2. Проверьте ID заявки командой /list_requests")
        print("   3. Убедитесь, что используете /approve [число]")
    else:
        print("\n⚠️ Обнаружены проблемы в логике команды.")


if __name__ == "__main__":
    asyncio.run(main())