"""Прямое добавление пользователей в SQLite БД"""
import sqlite3
from utils.auth import hash_password

# Подключаемся к базе
conn = sqlite3.connect('guardbot.db')
cursor = conn.cursor()

# Удаляем старых тестовых пользователей если есть
cursor.execute("DELETE FROM users WHERE login IN ('admin', 'guard1', 'guard2')")

# Добавляем админа
cursor.execute("""
    INSERT INTO users (telegram_id, role, name, login, password_hash, is_authenticated, registered_at)
    VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
""", (999999991, 'admin', 'Администратор', 'admin', hash_password('admin123'), 0))

# Добавляем охранников
for i in range(1, 3):
    cursor.execute("""
        INSERT INTO users (telegram_id, role, name, login, password_hash, is_authenticated, registered_at)
        VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
    """, (999999990 + i + 1, 'guard', f'Охранник {i}', f'guard{i}', hash_password('guard123'), 0))

conn.commit()

# Проверяем
cursor.execute("SELECT login, role, name FROM users WHERE login IN ('admin', 'guard1', 'guard2')")
users = cursor.fetchall()

print("\n✅ Добавлены пользователи:")
for login, role, name in users:
    print(f"  - {role}: {login} ({name})")

print("\n📝 Для входа:")
print("   Админ:     login=admin   password=admin123")
print("   Охранник:  login=guard1  password=guard123")
print("   Охранник:  login=guard2  password=guard123")

conn.close()
