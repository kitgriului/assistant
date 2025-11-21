#!/bin/bash
# Простой скрипт установки для сервера
# Предполагается что файлы bot.py, requirements.txt и .env уже загружены

set -e

echo "🚀 Установка Whisper Bot"
echo "========================"

# Проверка что мы в правильной директории
if [ ! -f "bot.py" ]; then
    echo "❌ Ошибка: файл bot.py не найден!"
    echo "Убедитесь что вы запускаете скрипт из директории с файлами бота"
    exit 1
fi

# Обновление системы
echo "📦 Обновляю систему..."
apt update

# Установка зависимостей
echo "📦 Устанавливаю зависимости..."
apt install -y python3 python3-pip python3-venv ffmpeg

# Создание виртуального окружения
echo "🐍 Создаю виртуальное окружение..."
python3 -m venv venv

# Активация и установка пакетов
echo "📚 Устанавливаю Python пакеты..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Проверка .env файла
if [ ! -f ".env" ]; then
    echo "❌ Файл .env не найден!"
    echo "Создайте файл .env с содержимым:"
    echo "BOT_TOKEN=ваш_токен"
    echo "OPENAI_API_KEY=ваш_ключ"
    exit 1
fi

chmod 600 .env
echo "✅ Файл .env защищен"

# Создание systemd сервиса
echo "⚙️  Создаю systemd сервис..."
WORK_DIR=$(pwd)

cat > /etc/systemd/system/whisper-bot.service << EOF
[Unit]
Description=Whisper Telegram Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$WORK_DIR
Environment="PATH=$WORK_DIR/venv/bin"
ExecStart=$WORK_DIR/venv/bin/python bot.py
Restart=always
RestartSec=10

StandardOutput=journal
StandardError=journal
SyslogIdentifier=whisper-bot

[Install]
WantedBy=multi-user.target
EOF

# Запуск сервиса
echo "🔄 Запускаю бота..."
systemctl daemon-reload
systemctl enable whisper-bot
systemctl start whisper-bot

# Ожидание запуска
sleep 3

# Проверка статуса
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
    echo ""
    
    # Показываем последние логи
    echo "📋 Последние логи:"
    journalctl -u whisper-bot -n 10 --no-pager
else
    echo ""
    echo "❌ =========================================="
    echo "❌ Ошибка при запуске бота"
    echo "❌ =========================================="
    echo ""
    echo "Просмотрите логи:"
    journalctl -u whisper-bot -n 50 --no-pager
fi
