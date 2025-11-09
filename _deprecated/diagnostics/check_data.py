"""Проверка данных в БД"""
import sqlite3

conn = sqlite3.connect('guardbot.db')
cursor = conn.cursor()

print("\n" + "="*60)
print("👤 ПОЛЬЗОВАТЕЛИ:")
print("="*60)
cursor.execute("SELECT id, telegram_id, role, name, login, is_authenticated FROM users")
for row in cursor.fetchall():
    user_id, tg_id, role, name, login, auth = row
    print(f"  [{user_id}] {role:8} | {login or 'N/A':10} | {name:20} | TG:{tg_id} | Auth:{auth}")

print("\n" + "="*60)
print("📋 ЗАЯВКИ НА ПРОПУСК:")
print("="*60)
cursor.execute("""
    SELECT r.id, r.applicant_name, r.purpose, r.status, r.created_at, r.applicant_id
    FROM requests r
    ORDER BY r.created_at DESC
""")
requests = cursor.fetchall()

if requests:
    for row in requests:
        req_id, name, purpose, status, created, applicant_id = row
        print(f"\n  Заявка #{req_id}")
        print(f"    Заявитель: {name} (user_id={applicant_id})")
        print(f"    Цель: {purpose}")
        print(f"    Статус: {status}")
        print(f"    Создана: {created}")
else:
    print("  Заявок пока нет")

print("\n" + "="*60)

conn.close()
