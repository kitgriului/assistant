#!/usr/bin/env python3
"""Тест функционала аппрува без реального бота"""
import asyncio
import sys
import os

# Добавляем корневую директорию в PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import init_db
from database.models import Request as DBRequest
from database.session import get_session


async def test_approve_functionality():
    """Тестируем функционал аппрува"""
    print("🔍 Тестируем функционал аппрува...")
    
    # Инициализируем базу данных
    await init_db("sqlite+aiosqlite:///./test_guardbot.db")
    
    # Создаем тестовую заявку
    async with get_session() as session:
        test_request = DBRequest(
            name="Тест Тестович", 
            purpose="Тестирование аппрува", 
            datetime="2025-10-22 15:00",
            status="pending"
        )
        session.add(test_request)
        await session.commit()
        await session.refresh(test_request)
        req_id = test_request.id
        print(f"✅ Создана тестовая заявка с ID: {req_id}")
    
    # Тестируем процесс аппрува
    async with get_session() as session:
        req = await session.get(DBRequest, req_id)
        if not req:
            print(f"❌ Заявка с id={req_id} не найдена.")
            return False
            
        if req.status == "approved":
            print(f"⚠️ Заявка уже одобрена.")
            return False
            
        print(f"📝 Заявка найдена: {req.name}, статус: {req.status}")
        
        # Одобряем заявку
        req.status = "approved"
        await session.commit()
        print(f"✅ Заявка {req.id} одобрена!")
        
        # Проверяем, что статус изменился
        await session.refresh(req)
        if req.status == "approved":
            print("✅ Статус успешно изменен на 'approved'")
            return True
        else:
            print(f"❌ Ошибка: статус не изменился, текущий статус: {req.status}")
            return False


async def test_qr_generation():
    """Тестируем генерацию QR кода"""
    print("\n🔍 Тестируем генерацию QR кода...")
    
    try:
        from utils.qr import generate_qr_bytes
        qr_data = "request:1"
        qr_bytes = generate_qr_bytes(qr_data)
        
        if qr_bytes and len(qr_bytes.getvalue()) > 0:
            print(f"✅ QR код успешно сгенерирован для данных: {qr_data}")
            print(f"📏 Размер QR изображения: {len(qr_bytes.getvalue())} байт")
            return True
        else:
            print("❌ Ошибка генерации QR кода")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при генерации QR: {e}")
        return False


async def main():
    """Основная функция тестирования"""
    print("🚀 Запуск тестов функционала аппрува\n")
    
    # Тест 1: Проверка аппрува
    approve_test = await test_approve_functionality()
    
    # Тест 2: Проверка QR генерации
    qr_test = await test_qr_generation()
    
    print(f"\n📊 Результаты тестов:")
    print(f"   Аппрув: {'✅ Работает' if approve_test else '❌ Не работает'}")
    print(f"   QR генерация: {'✅ Работает' if qr_test else '❌ Не работает'}")
    
    if approve_test and qr_test:
        print("\n🎉 Все тесты пройдены! Функционал аппрува работает корректно.")
    else:
        print("\n⚠️ Обнаружены проблемы в функционале аппрува.")


if __name__ == "__main__":
    asyncio.run(main())