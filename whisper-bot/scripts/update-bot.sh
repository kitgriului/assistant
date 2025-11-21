#!/bin/bash
# Скрипт обновления бота на сервере
# Расположение: /root/whisper-bot/scripts/update-bot.sh (symlink to /root/assistant/whisper-bot)

set -e

echo "🔄 Обновление Whisper Bot..."
echo ""

cd /root/whisper-bot

# Останавливаем бота
echo "⏸️  Останавливаю бота..."
systemctl stop whisper-bot

# Сохраняем .env на случай изменений в репозитории
if [ -f .env ]; then
    cp .env .env.backup
    echo "✅ .env сохранен в .env.backup"
fi

# Обновляем код
echo "📥 Загружаю изменения с GitHub..."
git remote set-url origin git@github.com:kitgriului/assistant.git 2>/dev/null || true
git fetch origin
git reset --hard origin/main

# Восстанавливаем .env
if [ -f .env.backup ]; then
    mv .env.backup .env
    echo "✅ .env восстановлен"
fi

# Обновляем зависимости если нужно
echo "📦 Проверяю зависимости..."
source venv/bin/activate
pip install -r requirements.txt --upgrade --quiet

# Запускаем бота
echo "▶️  Запускаю бота..."
systemctl start whisper-bot

# Ждем запуска
sleep 3

# Проверяем статус
echo ""
echo "====================================="
if systemctl is-active --quiet whisper-bot; then
    echo "✅ Бот успешно обновлен и запущен!"
    echo "====================================="
    echo ""
    echo "📊 Статус:"
    systemctl status whisper-bot --no-pager -l | head -15
    echo ""
    echo "📋 Последние логи:"
    journalctl -u whisper-bot -n 10 --no-pager
else
    echo "❌ Ошибка! Бот не запустился"
    echo "====================================="
    echo ""
    echo "Просмотрите логи: journalctl -u whisper-bot -n 50"
    exit 1
fi
