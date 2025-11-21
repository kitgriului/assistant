#!/bin/bash
# Скрипт автоматического деплоя Whisper Bot на Linux сервер

set -e

echo "🚀 Начинаю деплой Whisper Bot..."

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Проверка root прав
if [ "$EUID" -eq 0 ]; then 
    echo -e "${YELLOW}⚠️  Не рекомендуется запускать от root. Создайте отдельного пользователя.${NC}"
fi

# Установка системных зависимостей
echo -e "${GREEN}📦 Устанавливаю системные зависимости...${NC}"
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git ffmpeg

# Создание директории для бота
BOT_DIR="$HOME/whisper-bot"
if [ ! -d "$BOT_DIR" ]; then
    mkdir -p "$BOT_DIR"
fi

cd "$BOT_DIR"

# Копирование файлов (если запускается локально)
echo -e "${GREEN}📁 Копирую файлы...${NC}"
# Здесь должны быть ваши файлы: bot.py, requirements.txt, README.md

# Создание виртуального окружения
echo -e "${GREEN}🐍 Создаю виртуальное окружение...${NC}"
python3 -m venv venv
source venv/bin/activate

# Установка зависимостей
echo -e "${GREEN}📚 Устанавливаю Python зависимости...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

# Проверка .env файла
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  Файл .env не найден!${NC}"
    echo "Создайте файл .env с содержимым:"
    echo ""
    echo "BOT_TOKEN=your_telegram_bot_token"
    echo "OPENAI_API_KEY=your_openai_api_key"
    echo ""
    exit 1
fi

# Создание systemd сервиса
echo -e "${GREEN}⚙️  Создаю systemd сервис...${NC}"
sudo tee /etc/systemd/system/whisper-bot.service > /dev/null <<EOF
[Unit]
Description=Whisper Telegram Bot
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$BOT_DIR
Environment="PATH=$BOT_DIR/venv/bin"
ExecStart=$BOT_DIR/venv/bin/python bot.py
Restart=always
RestartSec=10

StandardOutput=journal
StandardError=journal
SyslogIdentifier=whisper-bot

[Install]
WantedBy=multi-user.target
EOF

# Перезагрузка systemd и запуск бота
echo -e "${GREEN}🔄 Запускаю бота...${NC}"
sudo systemctl daemon-reload
sudo systemctl enable whisper-bot
sudo systemctl start whisper-bot

# Проверка статуса
sleep 2
if sudo systemctl is-active --quiet whisper-bot; then
    echo -e "${GREEN}✅ Бот успешно запущен и работает!${NC}"
    echo ""
    echo "Полезные команды:"
    echo "  sudo systemctl status whisper-bot  # Статус бота"
    echo "  sudo systemctl restart whisper-bot # Перезапуск"
    echo "  sudo systemctl stop whisper-bot    # Остановка"
    echo "  sudo journalctl -u whisper-bot -f  # Просмотр логов"
else
    echo -e "${YELLOW}⚠️  Ошибка запуска бота. Проверьте логи:${NC}"
    echo "  sudo journalctl -u whisper-bot -n 50"
fi
