"""
Whisper Bot - Voice transcription and AI processing Telegram bot.
Version 2.0 - Refactored architecture.
"""

import asyncio
import os
import tempfile
from pathlib import Path
from typing import Optional

from aiogram import Bot, Dispatcher
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

from bot import (
    TranscriptionStorage,
    create_action_keyboard,
    register_handlers,
    constants,
)

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
        register_handlers(self)
        
        logger.info("Bot initialized successfully")
        if CALENDAR_AVAILABLE:
            logger.info("✅ Calendar features enabled")
        else:
            logger.warning("⚠️ Calendar features disabled (dependencies not installed)")
    
    async def process_media(self, message: Message, media_type: str) -> None:
        """
        Process voice/audio/video message.
        
        Args:
            message: Telegram message
            media_type: Type of media ('voice', 'audio', or 'video')
        """
        try:
            await message.answer(constants.MSG_PROCESSING)
            
            with tempfile.TemporaryDirectory(prefix="whisper_bot_") as tmpdir:
                tmpdir_path = Path(tmpdir)
                
                # Download and get file
                file_id, ext = self._get_file_info(message, media_type)
                src_path = tmpdir_path / f"input{ext}"
                
                tg_file = await self.bot.get_file(file_id)
                await self.bot.download(tg_file, destination=src_path, timeout=120)
                
                # Transcribe
                await message.answer(constants.MSG_TRANSCRIBING)
                text = await self.whisper.transcribe(src_path)
            
            if not text:
                await message.answer(constants.ERR_TRANSCRIPTION_FAILED)
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
            await message.answer(constants.ERR_PROCESSING_FAILED)
    
    def _get_file_info(self, message: Message, media_type: str) -> tuple[str, str]:
        """
        Extract file_id and extension from message.
        
        Args:
            message: Telegram message
            media_type: Type of media
            
        Returns:
            Tuple of (file_id, extension)
        """
        if media_type == "voice":
            return message.voice.file_id, ".oga"
        elif media_type == "audio":
            ext = Path(message.audio.file_name).suffix or ".mp3"
            return message.audio.file_id, ext
        else:  # video
            return message.video.file_id, ".mp4"
    
    async def create_note(self, callback: CallbackQuery) -> None:
        """Create a structured note from transcription."""
        text = self._get_transcription(callback.message.chat.id)
        if not text:
            await callback.message.answer(constants.ERR_PROCESSING_FAILED)
            return
        
        processing_msg = await callback.message.answer(constants.MSG_CREATING_NOTE)
        
        try:
            result = await self.gpt.create_note(text)
            await processing_msg.edit_text(
                f"🗒 **Заметка:**\n\n{result}",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.exception(f"Note creation failed: {e}")
            await processing_msg.edit_text(constants.ERR_PROCESSING_FAILED)
    
    async def create_meeting(self, callback: CallbackQuery) -> None:
        """Extract and create meeting information."""
        text = self._get_transcription(callback.message.chat.id)
        if not text:
            await callback.message.answer(constants.ERR_PROCESSING_FAILED)
            return
        
        processing_msg = await callback.message.answer(constants.MSG_CREATING_EVENT)
        
        if not CALENDAR_AVAILABLE:
            await processing_msg.edit_text(constants.ERR_CALENDAR_DISABLED)
            return
        
        try:
            await self._handle_calendar_action(callback, text, processing_msg)
        except Exception as e:
            logger.exception(f"Meeting creation failed: {e}")
            await processing_msg.edit_text(constants.ERR_PROCESSING_FAILED)
    
    async def create_summary(self, callback: CallbackQuery) -> None:
        """Create a summary from transcription."""
        text = self._get_transcription(callback.message.chat.id)
        if not text:
            await callback.message.answer(constants.ERR_PROCESSING_FAILED)
            return
        
        processing_msg = await callback.message.answer(constants.MSG_CREATING_SUMMARY)
        
        try:
            result = await self.gpt.create_summary(text)
            await processing_msg.edit_text(
                f"📊 **Саммари:**\n\n{result}",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.exception(f"Summary creation failed: {e}")
            await processing_msg.edit_text(constants.ERR_PROCESSING_FAILED)
    
    def _get_transcription(self, chat_id: int) -> Optional[str]:
        """Get saved transcription for chat."""
        text = self.storage.get(chat_id)
        if not text:
            logger.warning(f"No transcription found for chat {chat_id}")
        return text
    
    async def _handle_calendar_action(self, callback: CallbackQuery, text: str, processing_msg: Message):
        """Handle calendar event creation."""
        if not CALENDAR_AVAILABLE:
            await processing_msg.edit_text("❌ Календарная функция недоступна")
            return
        
        logger.info("Extracting meeting info from text")
        # Extract meeting info using GPT
        meeting_info = await asyncio.to_thread(
            extract_meeting_info,
            OpenAI(api_key=self.config.openai_api_key),
            text
        )
        
        if not meeting_info:
            logger.warning("No meeting info extracted")
            await processing_msg.edit_text(
                "❌ Не удалось найти информацию о встрече.\n\n"
                "Убедитесь что указаны дата и время."
            )
            return
        
        logger.info(f"Meeting info extracted: {meeting_info}")
        
        # Format summary
        summary = format_meeting_summary(meeting_info)
        
        logger.info("Creating ICS file")
        # Create .ics file
        ics_path = await asyncio.to_thread(create_ics_file, meeting_info)
        logger.info(f"ICS file created: {ics_path}")
        
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
