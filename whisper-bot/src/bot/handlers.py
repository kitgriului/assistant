"""Bot message handlers."""

from typing import TYPE_CHECKING

from aiogram import F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery

from .constants import (
    WELCOME_MESSAGE,
    MSG_PROCESSING,
    CALLBACK_NOTE,
    CALLBACK_PROMPT,
    CALLBACK_MEETING,
    CALLBACK_SUMMARY,
)

if TYPE_CHECKING:
    from ..main import WhisperBot


def register_handlers(bot: "WhisperBot") -> None:
    """
    Register all bot handlers.
    
    Args:
        bot: WhisperBot instance
    """
    
    @bot.dp.message(CommandStart())
    async def cmd_start(message: Message) -> None:
        """Handle /start command."""
        await message.answer(WELCOME_MESSAGE, parse_mode="Markdown")
    
    @bot.dp.message(F.voice)
    async def handle_voice(message: Message) -> None:
        """Handle voice messages."""
        await bot.process_media(message, "voice")
    
    @bot.dp.message(F.audio)
    async def handle_audio(message: Message) -> None:
        """Handle audio files."""
        await bot.process_media(message, "audio")
    
    @bot.dp.message(F.video)
    async def handle_video(message: Message) -> None:
        """Handle video files."""
        await bot.process_media(message, "video")
    
    @bot.dp.message(F.text)
    async def handle_text(message: Message) -> None:
        """Handle text messages (for custom prompts)."""
        await bot.handle_prompt_input(message)
    
    @bot.dp.callback_query(F.data.startswith("action:"))
    async def handle_action(callback: CallbackQuery) -> None:
        """Handle action button callbacks."""
        import logging
        logger = logging.getLogger(__name__)
        
        if not callback.data:
            logger.warning("Received callback with no data")
            return
        
        logger.info(f"Received callback: {callback.data}")
        await callback.answer()
        
        if callback.data == CALLBACK_PROMPT:
            logger.info("Calling request_prompt")
            await bot.request_prompt(callback)
        elif callback.data == CALLBACK_NOTE:
            logger.info("Calling create_note")
            await bot.create_note(callback)
        elif callback.data == CALLBACK_MEETING:
            logger.info("Calling create_meeting")
            await bot.create_meeting(callback)
        elif callback.data == CALLBACK_SUMMARY:
            logger.info("Calling create_summary")
            await bot.create_summary(callback)
        else:
            logger.warning(f"Unknown callback data: {callback.data}")
