# 🚀 GuardBot Deployment Guide

Пошаговая инструкция по развертыванию бота в production среде.

---

## 📋 Содержание

- [Требования](#требования)
- [Подготовка сервера](#подготовка-сервера)
- [Вариант 1: Docker Compose (рекомендуется)](#вариант-1-docker-compose-рекомендуется)
- [Вариант 2: Systemd Service](#вариант-2-systemd-service)
- [Вариант 3: Docker без Compose](#вариант-3-docker-без-compose)
- [Настройка логирования](#настройка-логирования)
- [Мониторинг и поддержка](#мониторинг-и-поддержка)
- [Резервное копирование](#резервное-копирование)
- [Troubleshooting](#troubleshooting)

---

## ✅ Требования

### Минимальные требования сервера:
- **CPU**: 1 core (рекомендуется 2 cores)
- **RAM**: 512 MB (рекомендуется 1 GB)
- **Storage**: 2 GB свободного места (зависит от объема медиа)
- **OS**: Ubuntu 20.04+, Debian 11+, или аналог

### Программное обеспечение:
- Docker 20.10+ и Docker Compose 2.0+ (для Docker варианта)
- Python 3.12+ (для native варианта)
- SQLite 3.31+ (встроен в Python)

---

## 🔧 Подготовка сервера

### 1. Обновление системы

```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Установка Docker (если используете Docker)

```bash
# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Установка Docker Compose
sudo apt install docker-compose-plugin

# Добавление пользователя в группу docker
sudo usermod -aG docker $USER
newgrp docker
```

### 3. Клонирование репозитория

```bash
cd /opt
sudo git clone https://github.com/yourusername/guardbot.git
sudo chown -R $USER:$USER guardbot
cd guardbot
```

### 4. Настройка переменных окружения

```bash
# Копируем шаблон
cp .env.production .env

# Редактируем конфигурацию
nano .env
```

**Обязательно измените:**
```bash
BOT_TOKEN=YOUR_ACTUAL_BOT_TOKEN_HERE
ENVIRONMENT=production
LOG_LEVEL=INFO
LOG_TO_FILE=true
```

---

## 🐳 Вариант 1: Docker Compose (рекомендуется)

### Преимущества:
- Изолированное окружение
- Простое обновление
- Автоматический рестарт
- Ротация логов

### 1. Сборка и запуск

```bash
# Сборка образа
docker compose build

# Запуск в фоновом режиме
docker compose up -d
```

### 2. Проверка статуса

```bash
# Логи в реальном времени
docker compose logs -f

# Статус контейнера
docker compose ps

# Health check
docker inspect guardbot --format='{{.State.Health.Status}}'
```

### 3. Остановка и обновление

```bash
# Остановка
docker compose down

# Обновление кода
git pull

# Пересборка и запуск
docker compose up -d --build
```

### 4. Управление логами

```bash
# Последние 100 строк
docker compose logs --tail=100

# Логи за последний час
docker compose logs --since 1h

# Очистка старых логов
docker system prune -af --volumes
```

---

## ⚙️ Вариант 2: Systemd Service

### Преимущества:
- Нативная производительность
- Легкая интеграция с системой
- Простая отладка

### 1. Установка зависимостей

```bash
# Установка Python 3.12
sudo apt install python3.12 python3.12-venv python3-pip

# Создание виртуального окружения
python3.12 -m venv venv
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt
```

### 2. Создание systemd service

```bash
sudo nano /etc/systemd/system/guardbot.service
```

**Содержимое файла:**
```ini
[Unit]
Description=GuardBot Telegram Bot
After=network.target

[Service]
Type=simple
User=guardbot
Group=guardbot
WorkingDirectory=/opt/guardbot
Environment="PATH=/opt/guardbot/venv/bin"
EnvironmentFile=/opt/guardbot/.env
ExecStart=/opt/guardbot/venv/bin/python start_bot.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/guardbot/guardbot.log
StandardError=append:/var/log/guardbot/guardbot-error.log

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/guardbot/data /opt/guardbot/guardbot.db /opt/guardbot/logs

[Install]
WantedBy=multi-user.target
```

### 3. Создание пользователя и директорий

```bash
# Создание пользователя
sudo useradd -r -s /bin/false guardbot

# Создание директорий для логов
sudo mkdir -p /var/log/guardbot
sudo chown guardbot:guardbot /var/log/guardbot

# Права на проект
sudo chown -R guardbot:guardbot /opt/guardbot
```

### 4. Запуск сервиса

```bash
# Перезагрузка systemd
sudo systemctl daemon-reload

# Включение автозапуска
sudo systemctl enable guardbot

# Запуск
sudo systemctl start guardbot

# Проверка статуса
sudo systemctl status guardbot

# Просмотр логов
sudo journalctl -u guardbot -f
```

### 5. Управление сервисом

```bash
# Перезапуск
sudo systemctl restart guardbot

# Остановка
sudo systemctl stop guardbot

# Логи за последний час
sudo journalctl -u guardbot --since "1 hour ago"

# Логи с ошибками
sudo journalctl -u guardbot -p err
```

---

## 🐋 Вариант 3: Docker без Compose

### 1. Сборка образа

```bash
docker build -t guardbot:1.0.0 .
```

### 2. Создание сети и volume

```bash
# Создание volume для данных
docker volume create guardbot_data

# Создание сети (опционально)
docker network create guardbot_network
```

### 3. Запуск контейнера

```bash
docker run -d \
  --name guardbot \
  --restart unless-stopped \
  --env-file .env \
  -v $(pwd)/guardbot.db:/app/guardbot.db \
  -v $(pwd)/data/media:/app/data/media \
  -v $(pwd)/data/export:/app/data/export \
  -v $(pwd)/logs:/app/logs \
  --memory 512m \
  --cpus 1.0 \
  guardbot:1.0.0
```

### 4. Управление

```bash
# Логи
docker logs -f guardbot

# Остановка
docker stop guardbot

# Удаление
docker rm guardbot

# Обновление
git pull
docker build -t guardbot:1.0.0 .
docker stop guardbot && docker rm guardbot
# Запустить снова с той же командой
```

---

## 📊 Настройка логирования

### Ротация логов (для systemd)

Создайте `/etc/logrotate.d/guardbot`:

```bash
sudo nano /etc/logrotate.d/guardbot
```

**Содержимое:**
```
/var/log/guardbot/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0640 guardbot guardbot
    sharedscripts
    postrotate
        systemctl reload guardbot > /dev/null 2>&1 || true
    endscript
}
```

### Просмотр логов в реальном времени

```bash
# Docker Compose
docker compose logs -f --tail=50

# Systemd
sudo journalctl -u guardbot -f

# Файловые логи
tail -f /opt/guardbot/logs/guardbot.log
```

---

## 🔍 Мониторинг и поддержка

### Health Checks

```bash
# Docker
docker inspect guardbot --format='{{.State.Health.Status}}'

# Проверка lockfile (бот работает)
ls -la /opt/guardbot/.bot.lock

# Проверка процесса
ps aux | grep start_bot.py
```

### Метрики производительности

```bash
# Docker stats
docker stats guardbot

# System resources
htop

# Database size
du -h /opt/guardbot/guardbot.db

# Media storage
du -h /opt/guardbot/data/media
```

### Alerts и уведомления

Настройте мониторинг через:
- **Prometheus + Grafana**: для метрик
- **Sentry**: для error tracking
- **UptimeRobot**: для проверки доступности

---

## 💾 Резервное копирование

### Автоматический backup с cron

```bash
# Создание скрипта backup
sudo nano /opt/guardbot/backup.sh
```

**Содержимое:**
```bash
#!/bin/bash
BACKUP_DIR="/opt/guardbot/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Создание директории
mkdir -p $BACKUP_DIR

# Backup базы данных
cp /opt/guardbot/guardbot.db "$BACKUP_DIR/guardbot_$DATE.db"

# Удаление старых бэкапов (старше 7 дней)
find $BACKUP_DIR -type f -name "guardbot_*.db" -mtime +7 -delete

echo "Backup completed: guardbot_$DATE.db"
```

```bash
# Права на выполнение
chmod +x /opt/guardbot/backup.sh

# Добавление в cron (каждый день в 3:00)
sudo crontab -e
```

Добавьте строку:
```
0 3 * * * /opt/guardbot/backup.sh >> /var/log/guardbot/backup.log 2>&1
```

### Manual backup

```bash
# Остановка бота
docker compose down  # или sudo systemctl stop guardbot

# Backup
cp guardbot.db guardbot_backup_$(date +%Y%m%d).db
tar -czf data_backup_$(date +%Y%m%d).tar.gz data/

# Запуск бота
docker compose up -d  # или sudo systemctl start guardbot
```

### Восстановление из backup

```bash
# Остановка бота
docker compose down

# Восстановление БД
cp guardbot_backup_20251107.db guardbot.db

# Восстановление данных
tar -xzf data_backup_20251107.tar.gz

# Запуск
docker compose up -d
```

---

## 🔧 Troubleshooting

### Бот не запускается

```bash
# Проверка логов
docker compose logs --tail=50
# или
sudo journalctl -u guardbot -n 50

# Проверка переменных окружения
cat .env | grep BOT_TOKEN

# Проверка прав доступа
ls -la guardbot.db data/
```

### TelegramConflictError

```bash
# Остановка всех экземпляров
docker compose down
# или
sudo systemctl stop guardbot

# Удаление lockfile
rm -f .bot.lock

# Проверка других процессов
ps aux | grep start_bot.py
```

### Проблемы с БД (MultipleResultsFound)

```bash
# Вход в контейнер
docker compose exec guardbot bash

# Проверка дубликатов
sqlite3 guardbot.db "SELECT guard_id, COUNT(*) FROM patrol_events WHERE status='in_progress' GROUP BY guard_id HAVING COUNT(*) > 1;"
```

### Медленная работа

```bash
# Проверка размера БД
ls -lh guardbot.db

# Vacuum БД (сжатие)
sqlite3 guardbot.db "VACUUM;"

# Очистка старых медиафайлов
find data/media -type f -mtime +30 -delete
```

### Нет места на диске

```bash
# Проверка использования диска
df -h

# Очистка Docker
docker system prune -af --volumes

# Очистка старых логов
docker compose logs --no-log-prefix | head -n 0
```

---

## 📝 Checklist перед деплоем

- [ ] Создан и настроен `.env` с валидным BOT_TOKEN
- [ ] Установлен Docker + Docker Compose (или Python 3.12+)
- [ ] Созданы директории: `data/media`, `data/export`, `logs`
- [ ] Настроены права доступа к файлам
- [ ] Проверена работа на dev-окружении
- [ ] Настроен firewall (только SSH и необходимые порты)
- [ ] Настроено резервное копирование
- [ ] Настроен мониторинг и alerts
- [ ] Протестирована автозагрузка при перезапуске сервера
- [ ] Документированы учетные данные админов

---

## 🆘 Получение помощи

- **GitHub Issues**: https://github.com/yourusername/guardbot/issues
- **Документация**: `docs/` директория
- **Логи**: всегда прикладывайте логи к вопросам

---

**Production Ready! 🚀**
