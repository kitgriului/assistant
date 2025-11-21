import asyncio
import logging
import os
import tempfile
import subprocess
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, FSInputFile
from dotenv import load_dotenv

try:
    from openai import OpenAI
except Exception:  # pragma: no cover - safety fallback if package missing during static checks
    OpenAI = None  # type: ignore

# Настройка логирования ПЕРВАЯ
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("voice-whisper-bot")

# Импорт модулей календаря
try:
    from calendar_parser import extract_meeting_info, format_meeting_summary
    from calendar_integration import create_ics_file, create_google_calendar_event, check_calendar_auth
    CALENDAR_ENABLED = True
    logger.info("✅ Calendar modules loaded successfully")
except ImportError as e:
    CALENDAR_ENABLED = False
    logger.warning(f"⚠️ Calendar modules not available: {e}")

# Временное хранилище расшифрованных текстов (chat_id -> text)
transcription_storage: dict[int, str] = {}


def _ensure_env() -> tuple[str, str]:
    load_dotenv()
    bot_token = os.getenv("BOT_TOKEN", "").strip()
    openai_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not bot_token:
        raise RuntimeError("BOT_TOKEN is not set in .env")
    if not openai_key:
        raise RuntimeError("OPENAI_API_KEY is not set in .env")
    return bot_token, openai_key


async def _run_ffmpeg_to_wav(src: Path, dst_wav: Path) -> None:
    """Convert any audio/video file to mono 16kHz WAV using ffmpeg."""
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(src),
        "-ac",
        "1",
        "-ar",
        "16000",
        str(dst_wav),
    ]
    logger.info("Running ffmpeg: %s", " ".join(cmd))
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except FileNotFoundError as e:
        raise RuntimeError(
            "ffmpeg is not installed or not found in PATH"
        ) from e

    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        logger.error("ffmpeg failed: %s", stderr.decode(errors="ignore"))
        raise RuntimeError("ffmpeg failed to convert audio to WAV")


async def _transcribe_with_whisper(client: "OpenAI", audio_path: Path) -> str:
    logger.info("Sending audio to OpenAI Whisper: %s", audio_path)
    with open(audio_path, "rb") as f:
        resp = client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
        )
    # The SDK returns an object with a 'text' attribute
    text = getattr(resp, "text", None)
    if not text:
        # In rare cases a plain string may be returned depending on response_format
        text = str(resp)
    return text


async def _create_note_from_text(client: "OpenAI", text: str) -> str:
    """Создать заметку в формате Markdown из расшифровки."""
    logger.info("Creating note from transcription")
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "Ты помощник, который оформляет расшифровки аудио в структурированные заметки в формате Markdown. "
                    "Твоя задача: создать чёткую, читаемую заметку с заголовками, списками и форматированием. "
                    "Убери слова-паразиты, повторы, сохрани все факты и смысл. Используй эмодзи для улучшения читаемости."
                )
            },
            {
                "role": "user",
                "content": f"Создай структурированную заметку из этого текста:\n\n{text}"
            }
        ],
        temperature=0.7
    )
    return response.choices[0].message.content or "Не удалось создать заметку"


async def _create_meeting_from_text(client: "OpenAI", text: str) -> str:
    """Извлечь информацию о встрече из расшифровки."""
    logger.info("Extracting meeting information from transcription")
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "Ты помощник, который извлекает информацию о встрече из текста. "
                    "Определи и структурируй: тему встречи, дату и время (если есть), участников, повестку/задачи. "
                    "Оформи результат в Markdown с чёткой структурой. Если какая-то информация отсутствует, укажи это."
                )
            },
            {
                "role": "user",
                "content": f"Извлеки информацию о встрече из этого текста:\n\n{text}"
            }
        ],
        temperature=0.5
    )
    return response.choices[0].message.content or "Не удалось извлечь информацию о встрече"


async def _create_summary_from_text(client: "OpenAI", text: str) -> str:
    """Создать структурированное саммари текста."""
    logger.info("Creating summary from transcription")
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "Ты помощник, который создаёт структурированные саммари из текста. "
                    "Убери все повторы, слова-паразиты, шум и лишние слова. "
                    "Сохрани все факты, смысл и последовательность. Оформи текст в виде чётких тезисов с эмодзи."
                )
            },
            {
                "role": "user",
                "content": f"Создай структурированное саммари из этого текста:\n\n{text}"
            }
        ],
        temperature=0.5
    )
    return response.choices[0].message.content or "Не удалось создать саммари"


def _create_action_keyboard() -> InlineKeyboardMarkup:
    """Создать клавиатуру с действиями после расшифровки."""
    buttons = [
        [InlineKeyboardButton(text="🗒 Создать заметку", callback_data="action:note")],
        [InlineKeyboardButton(text="📅 Создать встречу", callback_data="action:meeting")],
        [InlineKeyboardButton(text="📊 Сделать саммари", callback_data="action:summary")],
    ]
    
    # Добавляем кнопку календаря если модуль доступен
    if CALENDAR_ENABLED:
        buttons.append([InlineKeyboardButton(text="� Создать событие в календаре", callback_data="action:calendar")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def _guess_extension_from_message(message: Message) -> str:
    if message.voice:
        return ".oga"  # Telegram voice notes are OGG/Opus
    if message.audio and message.audio.file_name:
        return Path(message.audio.file_name).suffix or ".audio"
    if message.video and message.video.file_name:
        return Path(message.video.file_name).suffix or ".mp4"
    # Fallback
    return ".bin"


async def _download_telegram_file(bot: Bot, message: Message, dst_path: Path) -> None:
    if message.voice:
        file_id = message.voice.file_id
    elif message.audio:
        file_id = message.audio.file_id
    elif message.video:
        file_id = message.video.file_id
    else:
        raise RuntimeError("Unsupported message type for download")

    tg_file = await bot.get_file(file_id)
    # Увеличиваем таймаут для больших файлов до 120 секунд
    await bot.download(tg_file, destination=dst_path, timeout=120)


async def handle_media_for_transcription(message: Message, bot: Bot, client: "OpenAI") -> None:
    try:
        await message.answer("Принял файл. Расшифровываю…")

        with tempfile.TemporaryDirectory(prefix="whisper_bot_") as tmpdir:
            tmpdir_path = Path(tmpdir)
            src_ext = _guess_extension_from_message(message)
            src_path = tmpdir_path / f"input{src_ext}"

            await _download_telegram_file(bot, message, src_path)

            # Whisper API supports many audio formats directly (OGG, MP3, MP4, etc.)
            text = await _transcribe_with_whisper(client, src_path)

        text = (text or "").strip()
        if not text:
            await message.answer("Не удалось распознать речь в аудио.")
            return

        # Сохраняем расшифровку для дальнейшей обработки
        chat_id = message.chat.id
        transcription_storage[chat_id] = text

        # Отправляем расшифровку с клавиатурой действий
        keyboard = _create_action_keyboard()
        await message.answer(
            f"✅ Расшифровка готова:\n\n{text}\n\n"
            "Выберите действие:",
            reply_markup=keyboard
        )
    except Exception as e:
        logger.exception("Failed to process media: %s", e)
        
        # Специфичная обработка ошибок
        error_message = str(e)
        if "file is too big" in error_message.lower():
            await message.answer(
                "❌ Файл слишком большой!\n\n"
                "Telegram Bot API ограничивает размер файлов до 20 МБ.\n"
                "Пожалуйста, отправьте более короткую запись или сожмите файл."
            )
        elif "timeout" in error_message.lower():
            await message.answer(
                "❌ Превышено время ожидания при загрузке файла.\n\n"
                "Файл слишком большой или медленное соединение.\n"
                "Попробуйте отправить файл меньшего размера."
            )
        else:
            await message.answer(
                "❌ Произошла ошибка при обработке аудио.\n"
                "Попробуй ещё раз позже или отправь другой файл."
            )


async def main() -> None:
    bot_token, openai_key = _ensure_env()
    if OpenAI is None:
        raise RuntimeError(
            "openai package is not available. Install dependencies from requirements.txt"
        )

    client = OpenAI(api_key=openai_key)

    bot = Bot(token=bot_token)
    dp = Dispatcher()

    @dp.message(CommandStart())
    async def on_start(message: Message):
        await message.answer(
            "🎙 **Бот для расшифровки аудио с помощью Whisper**\n\n"
            "Я умею расшифровывать:\n"
            "• 🔊 Голосовые сообщения\n"
            "• 🎵 Аудиофайлы (MP3, M4A, WAV и др.)\n"
            "• 🎬 Видео (извлекаю аудиодорожку)\n\n"
            "После расшифровки я предложу:\n"
            "• 🗒 Создать структурированную заметку\n"
            "• 📅 Извлечь информацию о встрече\n"
            "• 📊 Сделать краткое саммари\n\n"
            "⚠️ Максимальный размер файла: **20 МБ**\n\n"
            "Отправь мне аудио или видео, и я начну работу!",
            parse_mode="Markdown"
        )

    # Voice messages (OGG/Opus)
    @dp.message(F.voice)
    async def on_voice(message: Message, bot: Bot):
        await handle_media_for_transcription(message, bot, client)

    # Optional: audio files (mp3/m4a/wav/etc.)
    @dp.message(F.audio)
    async def on_audio(message: Message, bot: Bot):
        await handle_media_for_transcription(message, bot, client)

    # Optional: videos (mp4), Whisper will try to extract audio
    @dp.message(F.video)
    async def on_video(message: Message, bot: Bot):
        await handle_media_for_transcription(message, bot, client)

    # Обработчик нажатий на кнопки действий
    @dp.callback_query(F.data.startswith("action:"))
    async def on_action_callback(callback: CallbackQuery):
        await callback.answer()  # Убираем "часики" на кнопке
        
        chat_id = callback.message.chat.id
        action = callback.data.split(":")[1]
        
        # Получаем сохранённый текст расшифровки
        text = transcription_storage.get(chat_id)
        if not text:
            await callback.message.answer(
                "❌ Расшифровка не найдена. Отправьте новое голосовое сообщение."
            )
            return
        
        # Показываем индикатор обработки
        processing_msg = await callback.message.answer("⏳ Обрабатываю...")
        
        try:
            if action == "note":
                result = await _create_note_from_text(client, text)
                await processing_msg.edit_text(f"🗒 **Заметка:**\n\n{result}", parse_mode="Markdown")
            
            elif action == "meeting":
                result = await _create_meeting_from_text(client, text)
                await processing_msg.edit_text(f"📅 **Информация о встрече:**\n\n{result}", parse_mode="Markdown")
            
            elif action == "summary":
                result = await _create_summary_from_text(client, text)
                await processing_msg.edit_text(f"📊 **Саммари:**\n\n{result}", parse_mode="Markdown")
            
            elif action == "calendar":
                if not CALENDAR_ENABLED:
                    await processing_msg.edit_text("❌ Модуль календаря недоступен")
                    return
                
                # Извлекаем информацию о встрече из текста (используем client из замыкания)
                meeting_info = await asyncio.to_thread(extract_meeting_info, client, text)
                
                if not meeting_info:
                    await processing_msg.edit_text(
                        "❌ Не удалось найти информацию о встрече в тексте.\n\n"
                        "Убедитесь что в сообщении указаны дата и время встречи."
                    )
                    return
                
                # Форматируем информацию о встрече
                summary = format_meeting_summary(meeting_info)
                
                # Создаем .ics файл (обернем в thread для IO операций)
                ics_path = await asyncio.to_thread(create_ics_file, meeting_info)
                
                if ics_path:
                    await processing_msg.edit_text(
                        f"✅ Событие создано!\n\n{summary}\n\n"
                        "📎 Отправляю файл для добавления в календарь..."
                    )
                    
                    # Отправляем .ics файл
                    ics_file = FSInputFile(ics_path)
                    await callback.message.answer_document(
                        document=ics_file,
                        caption="📆 Откройте этот файл чтобы добавить событие в ваш календарь"
                    )
                    
                    # Удаляем временный файл
                    try:
                        os.unlink(ics_path)
                    except:
                        pass
                else:
                    await processing_msg.edit_text("❌ Ошибка при создании файла календаря")
            
            else:
                await processing_msg.edit_text("❌ Неизвестное действие")
        
        except Exception as e:
            logger.exception("Failed to process action: %s", e)
            await processing_msg.edit_text(
                "❌ Произошла ошибка при обработке. Попробуйте ещё раз."
            )

    logger.info("Starting polling…")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except Exception as e:
        logger.error("Polling error: %s", e)
        raise


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
    except Exception as e:
        logger.error("Fatal error: %s", e)
        raise

