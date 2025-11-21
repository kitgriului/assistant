# 🚀 Деплой на ваш сервер 37.233.85.194

## Способ 1: Автоматический деплой (Рекомендуется)

### Шаг 1: Подключитесь к серверу

```bash
ssh root@37.233.85.194
# Пароль: atDqr*!ippr2
```

### Шаг 2: Скачайте и запустите скрипт деплоя

```bash
# Скачиваем скрипт
curl -o deploy.sh https://raw.githubusercontent.com/otg-tech/bots/main/whisper-bot/deploy-to-server.sh

# Или если репозиторий приватный, создайте файл вручную:
nano deploy.sh
# Скопируйте содержимое из deploy-to-server.sh

# Даем права на выполнение
chmod +x deploy.sh

# Запускаем
./deploy.sh
```

Скрипт запросит:
1. **BOT_TOKEN** - получите у @BotFather
2. **OPENAI_API_KEY** - с platform.openai.com

### Шаг 3: Готово! 🎉

Проверьте бота отправив `/start` в Telegram.

---

## Способ 2: Ручная установка

### 1. Подключение к серверу

```bash
ssh root@37.233.85.194
```

### 2. Установка зависимостей

```bash
apt update && apt upgrade -y
apt install -y python3 python3-pip python3-venv git ffmpeg
```

### 3. Создание директории и файлов

```bash
cd /root
mkdir whisper-bot
cd whisper-bot
```

### 4. Создание bot.py

```bash
nano bot.py
```

Скопируйте содержимое файла `bot.py` из проекта и вставьте в редактор.
Сохраните: `Ctrl+O`, `Enter`, `Ctrl+X`

### 5. Создание requirements.txt

```bash
nano requirements.txt
```

Содержимое:
```
aiogram==3.7.0
openai>=1.54.0
python-dotenv==1.0.1
httpx>=0.27.0
```

### 6. Создание виртуального окружения

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 7. Создание .env файла

```bash
nano .env
```

Содержимое (замените на свои токены):
```
BOT_TOKEN=ваш_токен_от_BotFather
OPENAI_API_KEY=ваш_ключ_OpenAI
```

Сохраните и защитите файл:
```bash
chmod 600 .env
```

### 8. Тестовый запуск

```bash
python bot.py
```

Если бот запустился, нажмите `Ctrl+C` для остановки.

### 9. Создание systemd сервиса

```bash
nano /etc/systemd/system/whisper-bot.service
```

Содержимое:
```ini
[Unit]
Description=Whisper Telegram Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/whisper-bot
Environment="PATH=/root/whisper-bot/venv/bin"
ExecStart=/root/whisper-bot/venv/bin/python bot.py
Restart=always
RestartSec=10

StandardOutput=journal
StandardError=journal
SyslogIdentifier=whisper-bot

[Install]
WantedBy=multi-user.target
```

### 10. Запуск сервиса

```bash
systemctl daemon-reload
systemctl enable whisper-bot
systemctl start whisper-bot
```

### 11. Проверка статуса

```bash
systemctl status whisper-bot
```

Должно быть: `Active: active (running)`

---

## 📊 Управление ботом

### Основные команды

```bash
# Просмотр статуса
systemctl status whisper-bot

# Перезапуск
systemctl restart whisper-bot

# Остановка
systemctl stop whisper-bot

# Запуск
systemctl start whisper-bot

# Просмотр логов в реальном времени
journalctl -u whisper-bot -f

# Последние 50 строк логов
journalctl -u whisper-bot -n 50

# Логи за последний час
journalctl -u whisper-bot --since "1 hour ago"
```

---

## 🔄 Обновление бота

Если вы внесли изменения в код:

```bash
# 1. Остановите бота
systemctl stop whisper-bot

# 2. Загрузите новый код на сервер (например, через git или scp)
# Или отредактируйте bot.py напрямую:
nano /root/whisper-bot/bot.py

# 3. Перезапустите
systemctl start whisper-bot
systemctl status whisper-bot
```

---

## 🔐 Безопасность

### Рекомендации:

1. **Смените пароль root**
```bash
passwd
```

2. **Создайте нового пользователя (не root)**
```bash
adduser botuser
usermod -aG sudo botuser
```

3. **Настройте SSH ключи**
```bash
# На вашем локальном компьютере:
ssh-keygen -t ed25519
ssh-copy-id root@37.233.85.194
```

4. **Настройте firewall**
```bash
ufw allow 22
ufw enable
```

5. **Отключите вход по паролю (после настройки SSH ключей)**
```bash
nano /etc/ssh/sshd_config
# Найдите и измените:
# PasswordAuthentication no
systemctl restart sshd
```

---

## 🐛 Troubleshooting

### Бот не запускается

```bash
# Проверьте логи
journalctl -u whisper-bot -n 100

# Попробуйте запустить вручную
cd /root/whisper-bot
source venv/bin/activate
python bot.py
```

### Проверка токенов

```bash
# Убедитесь что .env файл существует и содержит токены
cat /root/whisper-bot/.env
```

### Проверка ffmpeg

```bash
which ffmpeg
ffmpeg -version
```

### Проверка Python пакетов

```bash
cd /root/whisper-bot
source venv/bin/activate
pip list
```

---

## ✅ Проверка работы

1. Отправьте боту `/start` - должен ответить приветствием
2. Отправьте голосовое сообщение - должен расшифровать
3. Проверьте кнопки действий (Заметка, Встреча, Саммари)

Если все работает - **поздравляю! 🎉** Ваш бот работает 24/7!

---

## 📞 Дополнительная помощь

Если возникли проблемы:
1. Проверьте логи: `journalctl -u whisper-bot -f`
2. Убедитесь что порт 443/80 открыт (для Telegram API)
3. Проверьте подключение к интернету: `ping api.telegram.org`
