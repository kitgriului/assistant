"""Безопасная миграция базы данных - добавление новых полей"""
import sqlite3

def migrate():
    conn = sqlite3.connect('guardbot.db')
    cursor = conn.cursor()
    
    # Проверяем текущую структуру
    cursor.execute("PRAGMA table_info(requests)")
    columns = [row[1] for row in cursor.fetchall()]
    print(f"📋 Текущие колонки в таблице requests: {columns}")
    
    # Добавляем pass_type если его нет
    if 'pass_type' not in columns:
        print("➕ Добавляем колонку pass_type...")
        cursor.execute("ALTER TABLE requests ADD COLUMN pass_type TEXT DEFAULT 'pedestrian'")
        print("✅ Колонка pass_type добавлена")
    else:
        print("✓ Колонка pass_type уже существует")
    
    # Добавляем car_number если его нет
    if 'car_number' not in columns:
        print("➕ Добавляем колонку car_number...")
        cursor.execute("ALTER TABLE requests ADD COLUMN car_number TEXT")
        print("✅ Колонка car_number добавлена")
    else:
        print("✓ Колонка car_number уже существует")
    
    conn.commit()
    
    # Проверяем финальную структуру
    cursor.execute("PRAGMA table_info(requests)")
    print("\n📊 Финальная структура таблицы requests:")
    for row in cursor.fetchall():
        print(f"  {row[1]} ({row[2]})")
    
    # Проверяем данные
    cursor.execute("SELECT COUNT(*) FROM requests")
    count = cursor.fetchone()[0]
    print(f"\n📈 Количество заявок в базе: {count}")
    
    conn.close()
    print("\n✅ Миграция завершена успешно!")

if __name__ == "__main__":
    migrate()
