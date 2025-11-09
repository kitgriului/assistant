import sqlite3

conn = sqlite3.connect('guardbot.db')
cursor = conn.cursor()

# Получаем последнюю заявку
cursor.execute('SELECT id, name, status, qr_code, valid_until FROM requests ORDER BY id DESC LIMIT 1')
row = cursor.fetchone()

if row:
    print('\n📋 Последняя заявка:')
    print(f'  ID: {row[0]}')
    print(f'  Имя: {row[1]}')
    print(f'  Статус: {row[2]}')
    print(f'  QR UUID: {row[3]}')
    print(f'  Срок действия: {row[4]}')
    
    if row[3]:
        qr_data = f'GUARDBOT-{row[0]}-{row[3]}'
        print(f'\n📱 Данные QR-кода:')
        print(f'  {qr_data}')
        print(f'  Длина UUID: {len(row[3])} символов')
        print(f'  Длина полных данных: {len(qr_data)} символов')
        
        if len(row[3]) < 10:
            print('\n⚠️ ПРОБЛЕМА: UUID слишком короткий!')
        else:
            print('\n✅ UUID выглядит корректно')
    else:
        print('\n❌ ПРОБЛЕМА: qr_code пустой!')
else:
    print('\n❌ Нет заявок в базе')

conn.close()
