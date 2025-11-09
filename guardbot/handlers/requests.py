"""Requests management handlers: common flows for guard and admin.

This module centralizes request-related menus and actions entrypoints,
so both Guard and Admin follow the same paths from the main menu.
Actual approve/reject callbacks remain implemented in existing modules
to avoid behavior changes; we just route to them.
"""
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


router = Router()


@router.callback_query(F.data == "menu_requests_management")
async def menu_requests_management(callback: types.CallbackQuery):
    """Show the requests management submenu (for guard and admin)."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Заявки на утверждение", callback_data="menu_pending")],
        [InlineKeyboardButton(text="✅ Активные пропуска", callback_data="menu_active")],
        [InlineKeyboardButton(text="📦 Архив", callback_data="menu_archive")],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="main_menu")],
    ])

    await callback.message.edit_text(
        "🗂 <b>Управление заявками</b>\n\nВыберите раздел:",
        reply_markup=keyboard,
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(Command("requests"))
async def menu_requests_management_cmd(message: types.Message):
    """Команда для открытия подменю управления заявками."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Заявки на утверждение", callback_data="menu_pending")],
        [InlineKeyboardButton(text="✅ Активные пропуска", callback_data="menu_active")],
        [InlineKeyboardButton(text="📦 Архив", callback_data="menu_archive")],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="main_menu")],
    ])

    await message.answer(
        "🗂 <b>Управление заявками</b>\n\nВыберите раздел:",
        reply_markup=keyboard,
        parse_mode="HTML",
    )


@router.callback_query(F.data == "menu_pending")
async def menu_pending(callback: types.CallbackQuery):
    """Entry to the pending requests list (first item)."""
    # Reuse existing rendering from guard module to avoid logic drift
    from handlers.guard import show_pending_requests

    await show_pending_requests(callback)
