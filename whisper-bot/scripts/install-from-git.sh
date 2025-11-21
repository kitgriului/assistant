#!/bin/bash
# Установка/переустановка бота из Git репозитория

echo "========================================="
echo " Установка Whisper Bot из Git"
echo "========================================="
echo ""

# Остановить бот если запущен
echo "Останавливаю бота..."
systemctl stop whisper-bot 2>/dev/null || true

# Сохранить .env если существует
if [ -f /root/whisper-bot/.env ]; then
    echo "Сохраняю .env файл..."
    cp /root/whisper-bot/.env /tmp/whisper-bot-env-backup
fi

# Создать backup старой версии
if [ -d /root/whisper-bot ]; then
    echo "Создаю backup старой версии..."
    mv /root/whisper-bot /root/whisper-bot-backup-$(date +%Y%m%d-%H%M%S)
fi

# Клонировать репозиторий
echo "Клонирую репозиторий из GitHub..."
cd /root
git clone https://github.com/kitgriului/assistant.git

# Создать символическую ссылку
echo "Создаю символическую ссылку..."
ln -s /root/assistant/whisper-bot /root/whisper-bot

# Восстановить .env
if [ -f /tmp/whisper-bot-env-backup ]; then
    echo "Восстанавливаю .env файл..."
    cp /tmp/whisper-bot-env-backup /root/whisper-bot/.env
    rm /tmp/whisper-bot-env-backup
else
    echo "ВНИМАНИЕ: Необходимо создать .env файл!"
fi

# Создать виртуальное окружение
echo "Создаю виртуальное окружение..."
cd /root/whisper-bot
python3 -m venv venv

# Установить зависимости
echo "Устанавливаю зависимости..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Обновить systemd сервис
echo "Обновляю systemd сервис..."
cp scripts/whisper-bot.service /etc/systemd/system/
systemctl daemon-reload

# Запустить бота
echo "Запускаю бота..."
systemctl start whisper-bot
systemctl enable whisper-bot

# Проверить статус
sleep 3
echo ""
echo "========================================="
if systemctl is-active --quiet whisper-bot; then
    echo "✅ Бот успешно установлен и запущен!"
    echo "========================================="
    echo ""
    systemctl status whisper-bot --no-pager -l | head -15
else
    echo "❌ Ошибка! Бот не запустился"
    echo "========================================="
    echo ""
    journalctl -u whisper-bot -n 30 --no-pager
    exit 1
fi
