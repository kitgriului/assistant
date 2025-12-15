"""Bot text messages and constants."""

# Welcome message
WELCOME_MESSAGE = """🎙 **Бот для расшифровки аудио с помощью Whisper**

Я умею расшифровывать:
- Голосовые сообщения
- Аудиофайлы (MP3, M4A, WAV и др.)
- Видео (извлеку звук)

Отправь мне аудио, и я:
1. Расшифрую его с помощью Whisper
2. Предложу создать заметку, встречу или саммари
3. Могу создать событие в календаре 📆

Просто отправь мне голосовое сообщение или аудиофайл!"""

# Status messages
MSG_PROCESSING = "⌛ Обрабатываю..."
MSG_TRANSCRIBING = "🎙 Расшифровываю аудио..."
MSG_CONVERTING = "🔄 Конвертирую медиа..."
MSG_CREATING_NOTE = "🗒 Создаю заметку..."
MSG_CREATING_EVENT = "📅 Создаю событие..."
MSG_CREATING_SUMMARY = "📊 Создаю саммари..."
MSG_WAITING_FOR_PROMPT = "✏️ Напишите, что нужно сделать с расшифровкой."
MSG_PROCESSING_PROMPT = "🧠 Обрабатываю по вашему промпту..."

# Error messages
ERR_FILE_TOO_LARGE = "❌ Файл слишком большой. Максимальный размер: {max_size} МБ"
ERR_TRANSCRIPTION_FAILED = "❌ Ошибка при расшифровке. Попробуйте снова."
ERR_PROCESSING_FAILED = "❌ Ошибка при обработке. Попробуйте снова."
ERR_MEDIA_CONVERSION = "❌ Не удалось сконвертировать медиа."
ERR_CALENDAR_DISABLED = "❌ Функция календаря недоступна. Установите зависимости: pip install icalendar google-api-python-client google-auth-httplib2 google-auth-oauthlib"
ERR_NO_MEETING_INFO = "❌ Не удалось извлечь информацию о встрече из текста."

# Callback data prefixes
CALLBACK_NOTE = "action:note"
CALLBACK_PROMPT = "action:prompt"
CALLBACK_MEETING = "action:meeting"
CALLBACK_SUMMARY = "action:summary"
