# 🎙️ Whisper Voice Transcription Bot

Telegram-бот для расшифровки голосовых сообщений, аудио и видео с помощью OpenAI Whisper API.

## ✨ Возможности

- 🔊 Расшифровка голосовых сообщений Telegram
- 🎵 Поддержка аудиофайлов (MP3, M4A, WAV, OGG и др.)
- 🎬 Извлечение и расшифровка аудио из видео
- 🗒 Создание структурированных заметок из расшифровки
- 📅 Извлечение информации о встречах
- 📊 Генерация кратких саммари

## 🚀 Установка

### Требования

- Python 3.10+
- ffmpeg (для конвертации аудио/видео)

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

## 🎯 Запуск

```bash
python bot.py
```

## 📖 Использование

1. Запустите бота командой `/start`
2. Отправьте голосовое сообщение, аудио или видео файл
3. Дождитесь расшифровки
4. Выберите одно из действий:
   - 🗒 **Создать заметку** - структурированная заметка в Markdown
   - 📅 **Создать встречу** - извлечение информации о встрече
   - 📊 **Сделать саммари** - краткое содержание

## ⚠️ Ограничения

- Максимальный размер файла: **20 МБ** (ограничение Telegram Bot API)
- Поддерживаемые форматы: OGG, MP3, MP4, M4A, WAV и другие (через ffmpeg)

## 🛠️ Технологии

- [aiogram](https://github.com/aiogram/aiogram) - асинхронный фреймворк для Telegram Bot API
- [OpenAI Whisper API](https://platform.openai.com/docs/guides/speech-to-text) - распознавание речи
- [OpenAI GPT-4](https://platform.openai.com/docs/models/gpt-4) - обработка текста
- [ffmpeg](https://ffmpeg.org/) - конвертация аудио/видео

## 📝 Лицензия

MIT

## 👨‍💻 Автор

Создано с ❤️ для упрощения работы с голосовыми заметками
