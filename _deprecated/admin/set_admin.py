import sqlite3

conn = sqlite3.connect('guardbot.db')
c = conn.cursor()

# Обновляем роль
c.execute("UPDATE users SET role='admin' WHERE telegram_id=83579209")
conn.commit()

# Проверяем
c.execute('SELECT id, telegram_id, name, phone_number, role FROM users WHERE telegram_id=83579209')
user = c.fetchone()

print(f'\n✅ Роль обновлена!\n')
print(f'👤 {user[2]}')
print(f'   telegram_id: {user[1]}')
print(f'   phone: {user[3]}')
print(f'   🔑 Роль: {user[4]}')

conn.close()
