"""Генерация тестового QR-кода для проверки сканирования."""
import uuid
from utils.qr import generate_qr_bytes
from PIL import Image


def test_qr():
    """Создаём тестовый QR-код и сохраняем как PNG."""
    
    # Тестовые данные разных форматов
    test_cases = [
        ("Простой текст", "GUARDBOT-123-456789"),
        ("С UUID", f"GUARDBOT-1-{str(uuid.uuid4())}"),
        ("URL формат", "https://t.me/SK_GuardBot?start=pass_1"),
        ("Только цифры", "12345678901234567890"),
    ]
    
    print("\n🔍 Генерация тестовых QR-кодов...\n")
    
    for name, data in test_cases:
        print(f"📱 {name}:")
        print(f"   Данные: {data}")
        print(f"   Длина: {len(data)} символов")
        
        # Генерируем QR
        qr_bytes = generate_qr_bytes(data)
        
        # Сохраняем в файл
        filename = f"test_qr_{name.replace(' ', '_').lower()}.png"
        with open(filename, 'wb') as f:
            f.write(qr_bytes.read())
        
        print(f"   ✅ Сохранён: {filename}\n")
    
    print("🎉 Готово! Отсканируйте файлы камерой телефона.")
    print("   Если хотя бы один читается - QR генератор работает.")
    print("   Если не читается ни один - проблема в библиотеке qrcode.")


if __name__ == "__main__":
    test_qr()
