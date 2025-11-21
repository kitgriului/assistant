"""
Whisper Bot - Voice transcription and AI processing Telegram bot.
Version 2.0 - Refactored architecture.
"""

import asyncio
import os
import tempfile
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, FSInputFile
from openai import OpenAI

from config import Config
from utils import setup_logging, get_logger
from services import (
    WhisperService,
    GPTService,
    MediaProcessor,
    CALENDAR_AVAILABLE,
)

if CALENDAR_AVAILABLE:
    from services.calendar import (
        extract_meeting_info,
        format_meeting_summary,
        create_ics_file,
    )

from .bot import TranscriptionStorage, create_action_keyboard

logger = get_logger(__name__)


class WhisperBot:
    """Main bot application class."""
    
    def __init__(self, config: Config):
        """
        Initialize the bot.
        
        Args:
            config: Application configuration
        """
        self.config = config
        
        # Initialize services
        openai_client = OpenAI(api_key=config.openai_api_key)
        self.whisper = WhisperService(openai_client, config.whisper_model)
        self.gpt = GPTService(openai_client, config.gpt_model, config.gpt_temperature)
        self.media = MediaProcessor()
        
        # Bot components
        self.bot = Bot(token=config.bot_token)
        self.dp = Dispatcher()
        self.storage = TranscriptionStorage()
        
        # Register handlers
        self._register_handlers()
        
        logger.info("Bot initialized successfully")
        if CALENDAR_AVAILABLE:
            logger.info("✅ Calendar features enabled")
        else:
            logger.warning("⚠️ Calendar features disabled (dependencies not installed)")
    
    def _register_handlers(self):
        """Register all message and callback handlers."""
        
        @self.dp.message(CommandStart())
        async def cmd_start(message: Message):
            await message.answer(
                "🎙 **Бот для расшифровки аудио с помощью Whisper**\n\n"
                "Я умею расшифровывать:\n"
                "- Голосовые сообщения\n"
                "- Аудиофайлы (MP3, M4A, WAV и др.)\n"
                "- Видео (извлеку звук)\n\n"
                "Отправь мне аудио, и я:\n"
                "1. Расшифрую его с помощью Whisper\n"
                "2. Предложу создать заметку, встречу или саммари\n"
                "3. Могу создать событие в календаре 📆\n\n"
                "Просто отправь мне голосовое сообщение или аудиофайл!",
                parse_mode="Markdown"
            )
        
        @self.dp.message(F.voice)
        async def handle_voice(message: Message):
            await self._process_media(message, "voice")
        
        @self.dp.message(F.audio)
        async def handle_audio(message: Message):
            await self._process_media(message, "audio")
        
        @self.dp.message(F.video)
        async def handle_video(message: Message):
            await self._process_media(message, "video")
        
        @self.dp.callback_query(F.data.startswith("action:"))
        async def handle_action(callback: CallbackQuery):
            await self._process_action(callback)
    
    async def _process_media(self, message: Message, media_type: str):
        """Process voice/audio/video message."""
        try:
            await message.answer("Принял файл. Расшифровываю…")
            
            with tempfile.TemporaryDirectory(prefix="whisper_bot_") as tmpdir:
                tmpdir_path = Path(tmpdir)
                
                # Download file
                if media_type == "voice":
                    file_id = message.voice.file_id
                    ext = ".oga"
                elif media_type == "audio":
                    file_id = message.audio.file_id
                    ext = Path(message.audio.file_name).suffix or ".mp3"
                else:  # video
                    file_id = message.video.file_id
                    ext = ".mp4"
                
                src_path = tmpdir_path / f"input{ext}"
                tg_file = await self.bot.get_file(file_id)
                await self.bot.download(tg_file, destination=src_path, timeout=120)
                
                # Transcribe
                text = await self.whisper.transcribe(src_path)
            
            if not text:
                await message.answer("Не удалось распознать речь в аудио.")
                return
            
            # Save transcription
            self.storage.save(message.chat.id, text)
            
            # Send result with action buttons
            keyboard = create_action_keyboard(CALENDAR_AVAILABLE)
            await message.answer(
                f"✅ Расшифровка готова:\n\n{text}\n\nВыберите действие:",
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.exception(f"Failed to process {media_type}: {e}")
            await message.answer(
                "❌ Произошла ошибка при обработке файла.\n"
                "Попробуйте ещё раз или отправьте другой файл."
            )
    
    async def _process_action(self, callback: CallbackQuery):
        """Process action button callback."""
        await callback.answer()
        
        chat_id = callback.message.chat.id
        action = callback.data.split(":")[1]
        
        # Get saved transcription
        text = self.storage.get(chat_id)
        if not text:
            await callback.message.answer(
                "❌ Расшифровка не найдена. Отправьте новое сообщение."
            )
            return
        
        processing_msg = await callback.message.answer("⏳ Обрабатываю...")
        
        try:
            if action == "note":
                result = await self.gpt.create_note(text)
                await processing_msg.edit_text(
                    f"🗒 **Заметка:**\n\n{result}",
                    parse_mode="Markdown"
                )
            
            elif action == "meeting":
                result = await self.gpt.extract_meeting_info(text)
                await processing_msg.edit_text(
                    f"📅 **Информация о встрече:**\n\n{result}",
                    parse_mode="Markdown"
                )
            
            elif action == "summary":
                result = await self.gpt.create_summary(text)
                await processing_msg.edit_text(
                    f"📊 **Саммари:**\n\n{result}",
                    parse_mode="Markdown"
                )
            
            elif action == "calendar":
                await self._handle_calendar_action(callback, text, processing_msg)
            
            else:
                await processing_msg.edit_text("❌ Неизвестное действие")
        
        except Exception as e:
            logger.exception(f"Action processing failed: {e}")
            await processing_msg.edit_text(
                "❌ Произошла ошибка. Попробуйте ещё раз."
            )
    
    async def _handle_calendar_action(self, callback: CallbackQuery, text: str, processing_msg: Message):
        """Handle calendar event creation."""
        if not CALENDAR_AVAILABLE:
            await processing_msg.edit_text("❌ Календарная функция недоступна")
            return
        
        # Extract meeting info using GPT
        meeting_info = await asyncio.to_thread(
            extract_meeting_info,
            OpenAI(api_key=self.config.openai_api_key),
            text
        )
        
        if not meeting_info:
            await processing_msg.edit_text(
                "❌ Не удалось найти информацию о встрече.\n\n"
                "Убедитесь что указаны дата и время."
            )
            return
        
        # Format summary
        summary = format_meeting_summary(meeting_info)
        
        # Create .ics file
        ics_path = await asyncio.to_thread(create_ics_file, meeting_info)
        
        if ics_path:
            await processing_msg.edit_text(
                f"✅ Событие создано!\n\n{summary}\n\n"
                "📎 Отправляю файл для календаря..."
            )
            
            # Send .ics file
            ics_file = FSInputFile(ics_path)
            await callback.message.answer_document(
                document=ics_file,
                caption="📆 Откройте файл чтобы добавить событие в календарь"
            )
            
            # Cleanup
            try:
                os.unlink(ics_path)
            except:
                pass
        else:
            await processing_msg.edit_text("❌ Ошибка при создании файла календаря")
    
    async def start(self):
        """Start the bot."""
        logger.info("Starting bot polling...")
        await self.dp.start_polling(self.bot)
    
    async def stop(self):
        """Stop the bot."""
        logger.info("Stopping bot...")
        await self.bot.session.close()


async def main():
    """Main entry point."""
    # Load configuration
    try:
        config = Config.from_env()
        config.validate()
    except ValueError as e:
        print(f"Configuration error: {e}")
        return 1
    
    # Setup logging
    setup_logging(config.log_level)
    logger.info(f"Starting Whisper Bot v2.0")
    logger.info(f"GPT Model: {config.gpt_model}")
    logger.info(f"Whisper Model: {config.whisper_model}")
    
    # Create and start bot
    bot = WhisperBot(config)
    
    try:
        await bot.start()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    finally:
        await bot.stop()
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
