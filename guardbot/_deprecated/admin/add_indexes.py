# -*- coding: utf-8 -*-
"""
Добавление индексов для оптимизации запросов
"""
import asyncio
import sqlite3

async def add_indexes():
    """Добавить индексы в таблицы для ускорения запросов"""
    conn = sqlite3.connect('guardbot.db')
    cursor = conn.cursor()
    
    print("🔧 Добавление индексов...")
    
    try:
        # Индекс для быстрого поиска по telegram_id
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_users_telegram_id 
            ON users(telegram_id)
        ''')
        print("✅ Индекс idx_users_telegram_id создан")
        
        # Индекс для быстрого поиска заявок по статусу
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_requests_status 
            ON requests(status)
        ''')
        print("✅ Индекс idx_requests_status создан")
        
        # Индекс для быстрого поиска активных пропусков
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_requests_status_valid 
            ON requests(status, valid_until)
        ''')
        print("✅ Индекс idx_requests_status_valid создан")
        
        # Индекс для сортировки по дате обработки
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_requests_processed_at 
            ON requests(processed_at)
        ''')
        print("✅ Индекс idx_requests_processed_at создан")
        
        # Индекс для сортировки по дате создания
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_requests_created_at 
            ON requests(created_at)
        ''')
        print("✅ Индекс idx_requests_created_at создан")
        
        conn.commit()
        print("\n✅ Все индексы успешно добавлены!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    asyncio.run(add_indexes())
