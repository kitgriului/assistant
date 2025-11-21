# 🚀 БЫСТРЫЙ СТАРТ - Деплой на ваш сервер

## Информация о сервере
- IP: `37.233.85.194`
- User: `root`
- OS: `Ubuntu 24.04`
- Password: `atDqr*!ippr2`

---

## ⚡ Способ 1: Самый быстрый (через SSH одной командой)

### Windows (PowerShell):

```powershell
# 1. Убедитесь что у вас есть токены:
# BOT_TOKEN из @BotFather
# OPENAI_API_KEY с platform.openai.com

# 2. Загрузите файлы на сервер:
scp bot.py requirements.txt .env setup.sh root@37.233.85.194:/root/whisper-bot/

# 3. Подключитесь и установите:
ssh root@37.233.85.194
cd /root/whisper-bot
chmod +x setup.sh
./setup.sh
```

---

## 📋 Способ 2: Пошаговый (если нет файлов локально)

### 1. Подключение к серверу

```bash
ssh root@37.233.85.194
# Пароль: atDqr*!ippr2
```

### 2. Создание файлов на сервере

```bash
# Создаем директорию
mkdir -p /root/whisper-bot
cd /root/whisper-bot

# Создаем bot.py
nano bot.py
# Скопируйте код из bot.py и вставьте
# Ctrl+O для сохранения, Ctrl+X для выхода

# Создаем requirements.txt
cat > requirements.txt << 'EOF'
aiogram==3.7.0
openai>=1.54.0
python-dotenv==1.0.1
httpx>=0.27.0
EOF

# Создаем .env (ЗАМЕНИТЕ НА СВОИ ТОКЕНЫ!)
cat > .env << 'EOF'
BOT_TOKEN=ваш_токен_от_BotFather
OPENAI_API_KEY=ваш_ключ_OpenAI
EOF
```

### 3. Запуск установки

```bash
# Устанавливаем зависимости
apt update
apt install -y python3 python3-pip python3-venv ffmpeg

# Создаем виртуальное окружение
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Создание systemd сервиса

```bash
cat > /etc/systemd/system/whisper-bot.service << 'EOF'
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
EOF
```

### 5. Запуск бота

```bash
systemctl daemon-reload
systemctl enable whisper-bot
systemctl start whisper-bot
systemctl status whisper-bot
```

### 6. Проверка логов

```bash
journalctl -u whisper-bot -f
```

---

## 🎯 Проверка работы

1. Откройте Telegram
2. Найдите вашего бота
3. Отправьте `/start`
4. Отправьте голосовое сообщение

Если бот отвечает - **все работает!** 🎉

---

## 📊 Команды управления

```bash
# Статус бота
systemctl status whisper-bot

# Перезапуск
systemctl restart whisper-bot

# Остановка
systemctl stop whisper-bot

# Логи в реальном времени
journalctl -u whisper-bot -f

# Последние 50 строк логов
journalctl -u whisper-bot -n 50
```

---

## 🔧 Если что-то пошло не так

### Проблема: Бот не запускается

```bash
# Проверьте логи
journalctl -u whisper-bot -n 100

# Запустите вручную для диагностики
cd /root/whisper-bot
source venv/bin/activate
python bot.py
```

### Проблема: Неправильные токены

```bash
# Отредактируйте .env
nano /root/whisper-bot/.env
# Исправьте токены
# Ctrl+O, Enter, Ctrl+X

# Перезапустите бота
systemctl restart whisper-bot
```

### Проблема: Нет ffmpeg

```bash
# Установите ffmpeg
apt update
apt install -y ffmpeg
systemctl restart whisper-bot
```

---

## 🔐 Рекомендации по безопасности

После успешного запуска:

```bash
# 1. Смените пароль root
passwd

# 2. Настройте firewall
ufw allow 22
ufw enable

# 3. Регулярно обновляйте систему
apt update && apt upgrade -y
```

---

## ✅ Готово!

Ваш бот теперь работает 24/7 на сервере `37.233.85.194`

**Важно:** Сохраните новый пароль root в надежном месте!
