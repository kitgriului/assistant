# 🎙️ Whisper Voice Transcription Bot

Telegram-бот для расшифровки голосовых сообщений, аудио и видео с помощью OpenAI Whisper API.

**Версия:** 2.0 (модульная архитектура)  
**Репозиторий:** [kitgriului/assistant](https://github.com/kitgriului/assistant)

## ✨ Возможности

- 🔊 Расшифровка голосовых сообщений Telegram
- 🎵 Поддержка аудиофайлов (MP3, M4A, WAV, OGG и др.)
- 🎬 Извлечение и расшифровка аудио из видео
- 🤖 AI-обработка текста через GPT-4
- 🗒 Создание структурированных заметок из расшифровки
- 📅 Извлечение информации о встречах и создание ICS файлов
- 📊 Генерация кратких саммари
- 🔄 Git-based deployment workflow

## 🏗️ Архитектура

```
whisper-bot/
├── run.py              # Точка входа
├── src/
│   ├── main.py         # Основная логика бота
│   ├── config.py       # Конфигурация
│   ├── bot/            # Компоненты Telegram бота
│   ├── services/       # Сервисы (Whisper, GPT, Media, Calendar)
│   └── utils/          # Утилиты (логирование)
├── scripts/            # Скрипты деплоя
├── docs/               # Документация
└── tests/              # Тесты
```

## 🚀 Быстрый старт

### Требования

- Python 3.10+
- ffmpeg (для конвертации аудио/видео)
- Git

### Установка зависимостей

```bash
pip install -r requirements.txt
```

### Установка ffmpeg

**Windows:**
```bash
# Используя Chocolatey
choco install ffmpeg

# Или скачайте с https://ffmpeg.org/download.html
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

## ⚙️ Настройка

1. Создайте файл `.env` в корне проекта:

```env
BOT_TOKEN=your_telegram_bot_token_here
OPENAI_API_KEY=your_openai_api_key_here
```

2. Получите токены:
   - **BOT_TOKEN**: создайте бота через [@BotFather](https://t.me/botfather) в Telegram
   - **OPENAI_API_KEY**: получите на [platform.openai.com](https://platform.openai.com/api-keys)

### Локальная разработка

```bash
# 1. Клонируйте репозиторий
git clone https://github.com/kitgriului/assistant.git
cd assistant/whisper-bot

# 2. Создайте виртуальное окружение
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# или
.venv\Scripts\Activate.ps1  # Windows

# 3. Установите зависимости
pip install -r requirements.txt

# 4. Создайте .env файл
cp .env.example .env
# Отредактируйте .env и добавьте свои токены

# 5. Запустите бота
python run.py
```

### Деплой на сервер

См. документацию:
- [📘 QUICK-DEPLOY.md](docs/QUICK-DEPLOY.md) - Быстрая шпаргалка
- [📗 DEPLOY-FROM-GIT.md](docs/DEPLOY-FROM-GIT.md) - Подробная инструкция
- [📕 DEPLOYMENT.md](docs/DEPLOYMENT.md) - Полное руководство

**Быстрый деплой:**
```powershell
.\scripts\quick-update.ps1
```

## 📖 Использование

1. Запустите бота командой `/start`
2. Отправьте голосовое сообщение, аудио или видео файл
3. Дождитесь расшифровки
4. Выберите одно из действий:
   - 🗒 **Создать заметку** - структурированная заметка в Markdown
   - 📅 **Создать встречу** - извлечение информации о встрече + ICS файл
   - 📊 **Сделать саммари** - краткое содержание

## 🛠️ Разработка

### Workflow

```bash
# 1. Внесите изменения в код
# 2. Протестируйте локально
python run.py

# 3. Закоммитьте и запушьте
git add .
git commit -m "Описание изменений"
git push origin main

# 4. Задеплойте на сервер
.\scripts\quick-update.ps1
```

См. [WORKFLOW.md](docs/WORKFLOW.md) для деталей.

## 📚 Документация

- [📘 QUICK-DEPLOY.md](docs/QUICK-DEPLOY.md) - Шпаргалка по деплою
- [📗 DEPLOY-FROM-GIT.md](docs/DEPLOY-FROM-GIT.md) - Git-based deployment
- [📕 DEPLOYMENT.md](docs/DEPLOYMENT.md) - Полное руководство по деплою
- [📙 CALENDAR_SETUP.md](docs/CALENDAR_SETUP.md) - Настройка Google Calendar
- [📔 WORKFLOW.md](docs/WORKFLOW.md) - Процессы разработки
- [✅ MIGRATION-COMPLETE.md](docs/MIGRATION-COMPLETE.md) - Статус миграции

## ⚠️ Требования и ограничения

- Python 3.10+
- ffmpeg
- Максимальный размер файла: **20 МБ** (ограничение Telegram Bot API)
- Поддерживаемые форматы: OGG, MP3, MP4, M4A, WAV и другие

## 📄 Лицензия

MIT

## 🤝 Контакты

Telegram: [@softmachina_bot](https://t.me/softmachina_bot)

## 🛠️ Технологии

- [aiogram](https://github.com/aiogram/aiogram) - асинхронный фреймворк для Telegram Bot API
- [OpenAI Whisper API](https://platform.openai.com/docs/guides/speech-to-text) - распознавание речи
- [OpenAI GPT-4](https://platform.openai.com/docs/models/gpt-4) - обработка текста
- [ffmpeg](https://ffmpeg.org/) - конвертация аудио/видео

## 📝 Лицензия

MIT

## 👨‍💻 Автор

Создано с ❤️ для упрощения работы с голосовыми заметками
