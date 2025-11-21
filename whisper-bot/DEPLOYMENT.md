# 🚀 Деплой Whisper Bot на сервер

## 📋 Требования

- VPS/Dedicated сервер с Ubuntu 20.04+ или Debian 11+
- Минимум 1GB RAM
- Python 3.10+
- Доступ по SSH
- Домен (опционально)

## 🎯 Быстрый старт

### 1. Подключение к серверу

```bash
ssh user@your-server-ip
```

### 2. Автоматический деплой

```bash
# Загрузите файлы проекта на сервер
cd ~
git clone https://github.com/otg-tech/bots.git
cd bots/whisper-bot

# Создайте .env файл с вашими токенами
nano .env
# Вставьте:
# BOT_TOKEN=your_telegram_bot_token
# OPENAI_API_KEY=your_openai_api_key

# Запустите скрипт деплоя
chmod +x deploy.sh
./deploy.sh
```

### 3. Готово! 🎉

Бот автоматически запустится и будет работать 24/7.

---

## 🛠️ Ручная установка

### Шаг 1: Установка зависимостей

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv git ffmpeg
```

### Шаг 2: Клонирование репозитория

```bash
cd ~
git clone https://github.com/otg-tech/bots.git
cd bots/whisper-bot
```

### Шаг 3: Создание виртуального окружения

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Шаг 4: Настройка переменных окружения

```bash
nano .env
```

Содержимое:
```env
BOT_TOKEN=your_telegram_bot_token_here
OPENAI_API_KEY=your_openai_api_key_here
```

### Шаг 5: Тестовый запуск

```bash
python bot.py
```

Нажмите `Ctrl+C` для остановки.

### Шаг 6: Настройка systemd сервиса

```bash
# Создайте сервис-файл
sudo nano /etc/systemd/system/whisper-bot.service
```

Содержимое (замените `USER` и пути):
```ini
[Unit]
Description=Whisper Telegram Bot
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/home/YOUR_USERNAME/bots/whisper-bot
Environment="PATH=/home/YOUR_USERNAME/bots/whisper-bot/venv/bin"
ExecStart=/home/YOUR_USERNAME/bots/whisper-bot/venv/bin/python bot.py
Restart=always
RestartSec=10

StandardOutput=journal
StandardError=journal
SyslogIdentifier=whisper-bot

[Install]
WantedBy=multi-user.target
```

### Шаг 7: Запуск сервиса

```bash
# Перезагрузка конфигурации systemd
sudo systemctl daemon-reload

# Включение автозапуска при загрузке системы
sudo systemctl enable whisper-bot

# Запуск бота
sudo systemctl start whisper-bot

# Проверка статуса
sudo systemctl status whisper-bot
```

---

## 📊 Управление ботом

### Основные команды

```bash
# Просмотр статуса
sudo systemctl status whisper-bot

# Перезапуск
sudo systemctl restart whisper-bot

# Остановка
sudo systemctl stop whisper-bot

# Запуск
sudo systemctl start whisper-bot

# Просмотр логов (последние 50 строк)
sudo journalctl -u whisper-bot -n 50

# Просмотр логов в реальном времени
sudo journalctl -u whisper-bot -f

# Просмотр логов за последний час
sudo journalctl -u whisper-bot --since "1 hour ago"
```

---

## 🔄 Обновление бота

```bash
# Остановка бота
sudo systemctl stop whisper-bot

# Переход в директорию
cd ~/bots/whisper-bot

# Обновление кода
git pull origin main

# Активация виртуального окружения
source venv/bin/activate

# Обновление зависимостей
pip install -r requirements.txt --upgrade

# Перезапуск бота
sudo systemctl start whisper-bot

# Проверка статуса
sudo systemctl status whisper-bot
```

---

## 🐳 Альтернатива: Docker (рекомендуется)

### Создание Dockerfile

```dockerfile
FROM python:3.12-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Создание рабочей директории
WORKDIR /app

# Копирование файлов
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bot.py .
COPY .env .

# Запуск бота
CMD ["python", "bot.py"]
```

### Запуск с Docker

```bash
# Сборка образа
docker build -t whisper-bot .

# Запуск контейнера
docker run -d \
  --name whisper-bot \
  --restart unless-stopped \
  -v $(pwd)/.env:/app/.env \
  whisper-bot

# Просмотр логов
docker logs -f whisper-bot

# Перезапуск
docker restart whisper-bot
```

### Docker Compose

```yaml
version: '3.8'

services:
  whisper-bot:
    build: .
    container_name: whisper-bot
    restart: unless-stopped
    env_file:
      - .env
    volumes:
      - ./logs:/app/logs
```

Запуск:
```bash
docker-compose up -d
```

---

## 🌐 Размещение в облаке

### AWS EC2

1. Создайте EC2 инстанс (t2.micro для начала)
2. Подключитесь по SSH
3. Следуйте инструкциям выше

### DigitalOcean

1. Создайте Droplet (Basic Plan, $4/мес)
2. Выберите Ubuntu 22.04
3. Подключитесь по SSH
4. Следуйте инструкциям выше

### Heroku (бесплатный tier закрыт)

Больше не рекомендуется для постоянной работы.

### Railway.app / Render.com

Современные альтернативы с бесплатными планами.

---

## 🔐 Безопасность

### Рекомендации

1. **Используйте SSH ключи вместо паролей**
```bash
ssh-keygen -t ed25519
ssh-copy-id user@your-server
```

2. **Настройте firewall**
```bash
sudo ufw allow ssh
sudo ufw enable
```

3. **Обновляйте систему**
```bash
sudo apt update && sudo apt upgrade -y
```

4. **Защитите .env файл**
```bash
chmod 600 .env
```

5. **Используйте отдельного пользователя для бота**
```bash
sudo useradd -m -s /bin/bash botuser
sudo su - botuser
```

---

## 📈 Мониторинг

### Установка Prometheus + Grafana (опционально)

Для продвинутого мониторинга можно настроить Prometheus и Grafana.

### Простой мониторинг

Создайте скрипт проверки:

```bash
#!/bin/bash
# check_bot.sh

if ! systemctl is-active --quiet whisper-bot; then
    echo "Bot is down! Restarting..."
    sudo systemctl restart whisper-bot
    
    # Отправка уведомления (настройте под себя)
    # curl -X POST "https://api.telegram.org/bot<TOKEN>/sendMessage" \
    #   -d "chat_id=<YOUR_CHAT_ID>&text=Bot was down and restarted"
fi
```

Добавьте в crontab:
```bash
crontab -e
# Добавьте строку:
*/5 * * * * /path/to/check_bot.sh
```

---

## 🆘 Troubleshooting

### Бот не запускается

```bash
# Проверьте логи
sudo journalctl -u whisper-bot -n 100

# Проверьте .env файл
cat .env

# Попробуйте запустить вручную
cd ~/bots/whisper-bot
source venv/bin/activate
python bot.py
```

### Ошибки с ffmpeg

```bash
# Переустановите ffmpeg
sudo apt remove ffmpeg
sudo apt install ffmpeg
```

### Проблемы с памятью

```bash
# Проверьте использование памяти
free -h

# Увеличьте swap (если нужно)
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

---

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи: `sudo journalctl -u whisper-bot -f`
2. Убедитесь что все зависимости установлены
3. Проверьте что .env файл содержит корректные токены
4. Убедитесь что сервер имеет доступ к интернету

---

## 📝 Чеклист деплоя

- [ ] Сервер настроен и доступен по SSH
- [ ] Установлены Python 3.10+ и ffmpeg
- [ ] Репозиторий склонирован
- [ ] Создан .env файл с токенами
- [ ] Установлены Python зависимости
- [ ] Создан и запущен systemd сервис
- [ ] Бот работает и отвечает в Telegram
- [ ] Настроен автозапуск при перезагрузке
- [ ] Настроен мониторинг (опционально)

**Готово! 🎉 Ваш бот работает 24/7**
