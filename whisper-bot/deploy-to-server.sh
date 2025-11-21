#!/bin/bash
# Скрипт деплоя Whisper Bot на сервер 37.233.85.194

set -e

echo "🚀 Деплой Whisper Bot на Ubuntu 24.04"
echo "==========================================="

# Обновление системы
echo "📦 Обновляю систему..."
apt update && apt upgrade -y

# Установка зависимостей
echo "📦 Устанавливаю зависимости..."
apt install -y python3 python3-pip python3-venv git ffmpeg

# Создание директории для бота
echo "📁 Создаю директорию для бота..."
cd /root
mkdir -p whisper-bot
cd whisper-bot

# Создание виртуального окружения
echo "🐍 Создаю виртуальное окружение..."
python3 -m venv venv
source venv/bin/activate

# Установка Python зависимостей
echo "📚 Устанавливаю Python пакеты..."
cat > requirements.txt << 'EOF'
aiogram==3.7.0
openai>=1.54.0
python-dotenv==1.0.1
httpx>=0.27.0
EOF

pip install --upgrade pip
pip install -r requirements.txt

# Создание .env файла
echo "⚙️  Создаю .env файл..."
echo "Введите BOT_TOKEN из @BotFather:"
read -r BOT_TOKEN
echo "Введите OPENAI_API_KEY:"
read -r OPENAI_API_KEY

cat > .env << EOF
BOT_TOKEN=$BOT_TOKEN
OPENAI_API_KEY=$OPENAI_API_KEY
EOF

chmod 600 .env

echo "✅ .env файл создан"

# Создание systemd сервиса
echo "⚙️  Создаю systemd сервис..."
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

# Активация и запуск сервиса
echo "🔄 Запускаю бота..."
systemctl daemon-reload
systemctl enable whisper-bot
systemctl start whisper-bot

# Проверка статуса
sleep 3
if systemctl is-active --quiet whisper-bot; then
    echo ""
    echo "✅ =========================================="
    echo "✅ Бот успешно запущен и работает!"
    echo "✅ =========================================="
    echo ""
    echo "📊 Полезные команды:"
    echo "  systemctl status whisper-bot   # Проверить статус"
    echo "  systemctl restart whisper-bot  # Перезапустить"
    echo "  systemctl stop whisper-bot     # Остановить"
    echo "  journalctl -u whisper-bot -f   # Просмотр логов"
    echo ""
    echo "🎉 Отправьте /start боту в Telegram для проверки!"
else
    echo ""
    echo "❌ Ошибка при запуске бота"
    echo "Просмотрите логи: journalctl -u whisper-bot -n 50"
fi
