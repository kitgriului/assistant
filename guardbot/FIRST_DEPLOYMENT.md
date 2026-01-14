# 🚀 Инструкция по первому запуску GuardBot

## 📋 Что уже готово

✅ `.env` файл создан с вашим токеном  
✅ Docker конфигурация готова  
✅ Скрипты автоматического деплоя созданы  
✅ GitHub Actions настроен (опционально)

---

## 🎯 Вариант 1: Автоматический деплой (рекомендуется)

### Шаг 1: Загрузите код на GitHub

```bash
# В папке проекта на вашем компьютере
git add .
git commit -m "Production ready configuration"
git push origin main
```

### Шаг 2: Запустите скрипт деплоя

```bash
# Сделайте скрипт исполняемым (только один раз)
chmod +x deploy.sh update.sh

# Запустите автоматический деплой
./deploy.sh
```

**Что делает скрипт:**
- Проверяет наличие Docker на сервере (устанавливает если нет)
- Клонирует репозиторий на сервер
- Копирует .env файл
- Собирает Docker образ
- Запускает бота
- Показывает логи

---

## 🎯 Вариант 2: Ручной деплой

### Шаг 1: Подключитесь к серверу

```bash
ssh root@37.233.85.194
```

### Шаг 2: Установите Docker (если нет)

```bash
curl -fsSL https://get.docker.com | sh
apt-get install -y docker-compose-plugin
systemctl enable docker && systemctl start docker
```

### Шаг 3: Клонируйте проект

```bash
cd /opt
git clone git@github.com:otg-tech/bots.git guardbot
cd guardbot
git checkout main
```

### Шаг 4: Создайте .env файл

```bash
nano .env
```

Вставьте:
```env
BOT_TOKEN=8213953486:AAGMm7ayWkivh1cw-kdR8ippxoZhfgXeiqY
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
LOG_TO_FILE=true
DB_URL=sqlite+aiosqlite:///./guardbot.db
TZ=Europe/Moscow
```

Сохраните: `Ctrl+O`, `Enter`, `Ctrl+X`

### Шаг 5: Запустите бота

```bash
docker compose up -d --build
```

### Шаг 6: Проверьте работу

```bash
# Статус контейнера
docker compose ps

# Логи
docker compose logs -f
```

---

## 🔧 Полезные команды

### Управление ботом

```bash
# Остановить бота
docker compose down

# Перезапустить бота
docker compose restart

# Посмотреть логи
docker compose logs -f

# Посмотреть последние 100 строк
docker compose logs --tail=100

# Обновить бота после git push
./update.sh
```

### Удаленное управление

```bash
# Посмотреть логи с компьютера
ssh root@37.233.85.194 'cd /opt/guardbot && docker compose logs --tail=50'

# Перезапустить с компьютера
ssh root@37.233.85.194 'cd /opt/guardbot && docker compose restart'

# Обновить код
ssh root@37.233.85.194 'cd /opt/guardbot && git pull && docker compose restart'
```

---

## 🎨 Настройка GitHub Actions (автодеплой при push)

### Шаг 1: Настройте SSH ключ

На сервере:
```bash
# Создайте SSH ключ (если нет)
ssh-keygen -t rsa -b 4096 -C "github-actions"

# Добавьте публичный ключ в authorized_keys
cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys

# Скопируйте приватный ключ
cat ~/.ssh/id_rsa
```

### Шаг 2: Добавьте секрет в GitHub

1. Откройте https://github.com/otg-tech/bots/settings/secrets/actions
2. Нажмите "New repository secret"
3. Name: `SSH_PRIVATE_KEY`
4. Value: вставьте содержимое `~/.ssh/id_rsa`
5. Нажмите "Add secret"

### Шаг 3: Готово!

Теперь при каждом `git push` бот автоматически обновится на сервере! 🎉

---

## 🔍 Первая настройка бота

После запуска:

1. **Создайте первого администратора:**
   ```bash
   docker compose exec guardbot python -c "
   from database.session import get_db
   from database.models import User
   from utils.roles import Role
   import asyncio
   
   async def create_admin():
       async for db in get_db():
           user = User(
               telegram_id=123456789,  # ВАШ Telegram ID
               username='admin',
               role=Role.ADMIN,
               is_active=True
           )
           db.add(user)
           await db.commit()
           print('Admin created!')
   
   asyncio.run(create_admin())
   "
   ```

2. **Найдите свой Telegram ID:**
   - Напишите боту [@userinfobot](https://t.me/userinfobot)
   - Скопируйте ваш ID

3. **Проверьте работу:**
   - Откройте вашего бота в Telegram
   - Отправьте `/start`
   - Должно появиться меню администратора

---

## ❗ Troubleshooting

### Бот не отвечает

```bash
# Проверьте логи
docker compose logs --tail=100

# Проверьте статус
docker compose ps

# Перезапустите
docker compose restart
```

### Ошибка "Address already in use"

```bash
# Найдите процесс
docker ps -a

# Остановите старый контейнер
docker compose down
docker compose up -d
```

### Проблемы с базой данных

```bash
# Сделайте backup
cp guardbot.db guardbot.db.backup

# Проверьте права
ls -la guardbot.db
```

---

## 📞 Что дальше?

После запуска:
- ✅ Проверьте все функции бота
- ✅ Создайте резервную копию базы данных
- ✅ Настройте мониторинг (опционально)
- ✅ Добавьте других администраторов

**Бот готов к работе!** 🎉
