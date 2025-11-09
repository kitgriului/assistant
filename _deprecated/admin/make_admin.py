"""Скрипт для назначения пользователя администратором"""
import sqlite3
import sys

def make_admin(telegram_id):
    """Назначить пользователя администратором по telegram_id"""
    conn = sqlite3.connect('guardbot.db')
    cursor = conn.cursor()
    
    # Проверяем, есть ли пользователь
    cursor.execute("SELECT id, name, role, phone_number FROM users WHERE telegram_id = ?", (telegram_id,))
    user = cursor.fetchone()
    
    if not user:
        print(f"❌ Пользователь с telegram_id={telegram_id} не найден")
        print("   Сначала зарегистрируйтесь в боте через /start")
        conn.close()
        return False
    
    user_id, name, role, phone = user
    print(f"\n👤 Найден пользователь:")
    print(f"   ID: {user_id}")
    print(f"   Имя: {name}")
    print(f"   Телефон: {phone}")
    print(f"   Текущая роль: {role}")
    
    if role == 'admin':
        print(f"\n✅ Пользователь уже является администратором!")
        conn.close()
        return True
    
    # Назначаем роль admin
    cursor.execute("UPDATE users SET role = 'admin' WHERE telegram_id = ?", (telegram_id,))
    conn.commit()
    
    print(f"\n✅ Роль успешно изменена: {role} → admin")
    print(f"\n🔑 Теперь пользователь {name} имеет права администратора!")
    print(f"   Доступные команды:")
    print(f"   • /users - управление пользователями")
    print(f"   • /request - подать заявку на пропуск")
    
    conn.close()
    return True


if __name__ == '__main__':
    # Ваш telegram_id
    ADMIN_TELEGRAM_ID = 83579209
    
    print("=" * 60)
    print("🔧 Назначение администратора")
    print("=" * 60)
    
    make_admin(ADMIN_TELEGRAM_ID)
