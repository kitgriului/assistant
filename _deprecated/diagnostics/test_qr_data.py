"""Тестирование генерации QR-кода для проверки данных."""
import asyncio
import sys
from database.session import get_session
from database.models import Request
from sqlalchemy import select


async def check_qr_data():
    """Проверяем данные QR-кода последней заявки."""
    async with get_session() as session:
        # Получаем последнюю утверждённую заявку
        result = await session.execute(
            select(Request)
            .where(Request.status == 'approved')
            .order_by(Request.id.desc())
            .limit(1)
        )
        req = result.scalar_one_or_none()
        
        if not req:
            print("❌ Нет утверждённых заявок")
            return
        
        print(f"\n📋 Заявка #{req.id}")
        print(f"👤 Имя: {req.name}")
        print(f"📅 Создана: {req.created_at}")
        print(f"✅ Утверждена: {req.processed_at}")
        print(f"⏰ Действительна до: {req.valid_until}")
        print(f"\n🔑 UUID для QR: {req.qr_code}")
        print(f"\n📱 Данные QR-кода:")
        qr_data = f"request:{req.id}:{req.qr_code}"
        print(f"   {qr_data}")
        print(f"\n📏 Длина данных: {len(qr_data)} символов")
        
        if not req.qr_code:
            print("\n⚠️ ПРОБЛЕМА: qr_code пустой!")
        elif len(req.qr_code) < 10:
            print(f"\n⚠️ ПРОБЛЕМА: qr_code слишком короткий ({len(req.qr_code)} символов)")
        else:
            print(f"\n✅ QR-код корректный, длина UUID: {len(req.qr_code)} символов")


if __name__ == "__main__":
    asyncio.run(check_qr_data())
