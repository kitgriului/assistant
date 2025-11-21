# 🚀 Быстрый деплой Whisper Bot

## Вариант 1: VPS с systemd (Ubuntu/Debian)

```bash
# 1. Подключитесь к серверу
ssh user@your-server-ip

# 2. Клонируйте репозиторий
git clone https://github.com/otg-tech/bots.git
cd bots/whisper-bot

# 3. Создайте .env файл
nano .env
# BOT_TOKEN=your_token
# OPENAI_API_KEY=your_key

# 4. Запустите скрипт деплоя
chmod +x deploy.sh
./deploy.sh

# 5. Готово! Проверьте статус:
sudo systemctl status whisper-bot
```

## Вариант 2: Docker (Рекомендуется)

```bash
# 1. Установите Docker и Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo apt install docker-compose -y

# 2. Клонируйте и настройте
git clone https://github.com/otg-tech/bots.git
cd bots/whisper-bot
nano .env  # Добавьте токены

# 3. Запустите
docker-compose up -d

# 4. Проверьте логи
docker logs -f whisper-bot
```

## Вариант 3: DigitalOcean App Platform

1. Создайте аккаунт на DigitalOcean
2. Подключите GitHub репозиторий
3. Добавьте переменные окружения (BOT_TOKEN, OPENAI_API_KEY)
4. Нажмите Deploy

## Полезные команды

### systemd
```bash
sudo systemctl status whisper-bot   # Статус
sudo systemctl restart whisper-bot  # Перезапуск
sudo journalctl -u whisper-bot -f   # Логи
```

### Docker
```bash
docker-compose logs -f              # Логи
docker-compose restart              # Перезапуск
docker-compose down                 # Остановка
docker-compose up -d                # Запуск
```

## Требования к серверу

- **Минимум:** 1GB RAM, 1 CPU, 10GB диск
- **Рекомендуется:** 2GB RAM, 2 CPU, 20GB диск
- **OS:** Ubuntu 20.04+, Debian 11+

## Стоимость VPS

- **Hetzner:** от €4/мес (2GB RAM)
- **DigitalOcean:** от $6/мес (1GB RAM)
- **AWS EC2 t2.micro:** бесплатно 1 год (750 часов/мес)
- **Contabo:** от €4/мес (4GB RAM)

## Проверка работы

После деплоя отправьте боту в Telegram:
1. `/start` - должен ответить приветствием
2. Голосовое сообщение - должен расшифровать

✅ Если бот отвечает - все работает!

---

📚 Полная документация: [DEPLOYMENT.md](DEPLOYMENT.md)
