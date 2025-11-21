"""
Inline keyboards for bot interactions.
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def create_action_keyboard(calendar_enabled: bool = False) -> InlineKeyboardMarkup:
    """
    Create inline keyboard with action buttons after transcription.
    
    Args:
        calendar_enabled: Whether to show calendar button
        
    Returns:
        Inline keyboard markup
    """
    buttons = [
        [InlineKeyboardButton(text="🗒 Создать заметку", callback_data="action:note")],
        [InlineKeyboardButton(text="📅 Создать встречу", callback_data="action:meeting")],
        [InlineKeyboardButton(text="📊 Сделать саммари", callback_data="action:summary")],
    ]
    
    if calendar_enabled:
        buttons.append([
            InlineKeyboardButton(
                text="📆 Создать событие в календаре",
                callback_data="action:calendar"
            )
        ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)
