# 🛠️ Deployment Scripts

Автоматические скрипты для развертывания и обновления GuardBot на сервере.

## 📁 Файлы

- **deploy.sh** - Полный автоматический деплой
- **update.sh** - Быстрое обновление бота
- **create_first_admin.py** - Создание первого администратора

## 🚀 deploy.sh - Полный деплой

Автоматически настраивает и запускает бота на сервере.

### Что делает:
1. ✅ Проверяет Docker и Docker Compose
2. ✅ Устанавливает недостающие компоненты
3. ✅ Клонирует/обновляет репозиторий
4. ✅ Копирует .env файл
5. ✅ Собирает Docker образ
6. ✅ Запускает бота
7. ✅ Проверяет статус и показывает логи

### Использование:
```bash
# Первый раз - дайте права на выполнение
chmod +x deploy.sh

# Запуск
./deploy.sh
```

### Требования:
- SSH доступ к серверу
- Git репозиторий настроен
- .env файл создан

---

## ⚡ update.sh - Быстрое обновление

Обновляет код и перезапускает бота (без пересборки).

### Что делает:
1. ✅ Получает последние изменения из GitHub
2. ✅ Перезапускает бота
3. ✅ Показывает логи

### Использование:
```bash
# Первый раз
chmod +x update.sh

# Запуск
./update.sh
```

**Когда использовать:**
- После изменений в коде
- Для быстрого обновления без пересборки
- При мелких исправлениях

---

## 👤 create_first_admin.py - Создание админа

Создает первого администратора в базе данных.

### Использование:

**На сервере:**
```bash
# Войдите на сервер
ssh root@37.233.85.194

# Перейдите в папку проекта
cd /opt/guardbot

# Создайте админа (замените TELEGRAM_ID)
docker compose exec guardbot python create_first_admin.py TELEGRAM_ID admin
```

**Удаленно:**
```bash
ssh root@37.233.85.194 'cd /opt/guardbot && docker compose exec guardbot python create_first_admin.py TELEGRAM_ID admin'
```

### Параметры:
- `TELEGRAM_ID` - ваш Telegram ID (обязательно)
- `admin` - username (опционально)

### Как узнать Telegram ID:
1. Откройте [@userinfobot](https://t.me/userinfobot)
2. Отправьте `/start`
3. Скопируйте ваш ID

### Пример:
```bash
# Создать админа с ID 123456789
docker compose exec guardbot python create_first_admin.py 123456789 admin

# Создать админа только с ID (username будет admin_123456789)
docker compose exec guardbot python create_first_admin.py 123456789
```

---

## 🔄 Типичный workflow

### Первый деплой:
```bash
# 1. Загрузить код на GitHub
git add .
git commit -m "Production ready"
git push origin main

# 2. Развернуть на сервере
./deploy.sh

# 3. Создать администратора
ssh root@37.233.85.194 'cd /opt/guardbot && docker compose exec guardbot python create_first_admin.py YOUR_ID admin'
```

### Обновление кода:
```bash
# 1. Внести изменения
git add .
git commit -m "Update feature X"
git push origin main

# 2. Быстрое обновление
./update.sh

# Или полная пересборка (если изменились зависимости)
./deploy.sh
```

---

## 🐛 Отладка

### Посмотреть логи:
```bash
ssh root@37.233.85.194 'cd /opt/guardbot && docker compose logs -f'
```

### Проверить статус:
```bash
ssh root@37.233.85.194 'cd /opt/guardbot && docker compose ps'
```

### Перезапустить вручную:
```bash
ssh root@37.233.85.194 'cd /opt/guardbot && docker compose restart'
```

### Пересобрать образ:
```bash
ssh root@37.233.85.194 'cd /opt/guardbot && docker compose down && docker compose up -d --build'
```

---

## ⚙️ Конфигурация

Все настройки в скриптах:

```bash
SERVER="37.233.85.194"
USER="root"
REPO="git@github.com:otg-tech/bots.git"
DEPLOY_PATH="/opt/guardbot"
BRANCH="main"
```

Если нужно изменить - отредактируйте в начале каждого скрипта.

---

## 📝 Примечания

- **Windows:** Используйте Git Bash для запуска .sh скриптов
- **SSH ключи:** Убедитесь, что у вас есть доступ к серверу через SSH
- **.env файл:** Токен и настройки уже сконфигурированы
- **Backup:** Перед обновлением делайте резервную копию БД

---

## 🆘 Помощь

Если возникли проблемы:
1. Проверьте логи: `docker compose logs`
2. Проверьте статус: `docker compose ps`
3. Проверьте .env файл
4. Смотрите [FIRST_DEPLOYMENT.md](FIRST_DEPLOYMENT.md)
