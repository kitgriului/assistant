"""
Main menu handlers.

Provides a consistent role-based main menu for Admin and Guard:
- 📂 Управление заявками (Requests management)
- 🛡️ Управление обходами (Patrol management)

Guests only see: 📝 Подать заявку
"""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy import select

from database.session import get_session
from database.models import User
from utils.constants import Role
from utils.build import BUILD_STAMP
import logging

router = Router()
logger = logging.getLogger(__name__)


@router.message(Command("menu"))
@router.message(Command("profile"))
async def show_menu_command(message: Message):
    """Show the main menu for the current user role."""
    telegram_id = message.from_user.id
    async with get_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
    if not user:
        await message.answer("❌ Пользователь не найден. Отправьте /start")
        return
    await show_main_menu(message, user.role, user.name)


@router.message(Command("whoami"))
async def whoami(message: Message):
    """Diagnostic command: show role and identifiers."""
    telegram_id = message.from_user.id
    async with get_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
    if not user:
        await message.answer("guest (нет записи в БД)")
        return
    await message.answer(
        f"role={user.role}\nname={user.name or '-'}\nid={user.id}\ntg={user.telegram_id}"
    )


@router.message(Command("help"))
async def show_help(message: Message):
    """Show available commands based on user role."""
    telegram_id = message.from_user.id
    async with get_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
    
    if not user:
        help_text = (
            "📖 <b>Справка GuardBot</b>\n\n"
            "Вы не зарегистрированы.\n\n"
            "<b>Доступные команды:</b>\n"
            "/start - Начать работу и зарегистрироваться\n"
            "/help - Показать эту справку"
        )
    elif user.role == Role.ADMIN.value:
        help_text = (
            "📖 <b>Справка GuardBot</b>\n\n"
            "🔑 Ваша роль: <b>Администратор</b>\n\n"
            "<b>Основные команды:</b>\n"
            "/start - Главное меню\n"
            "/menu - Открыть главное меню\n"
            "/help - Показать эту справку\n\n"
            "<b>Команды обходов:</b>\n"
            "/patrol_[ID] - Просмотр конкретного патруля (например: /patrol_15)\n\n"
            "<b>Административные:</b>\n"
            "/whoami - Информация о вашем профиле\n\n"
            "💡 <i>Вы можете вызвать меню в любой момент командой /menu или /start</i>"
        )
    elif user.role == Role.GUARD.value:
        help_text = (
            "📖 <b>Справка GuardBot</b>\n\n"
            "🔑 Ваша роль: <b>Охранник</b>\n\n"
            "<b>Основные команды:</b>\n"
            "/start - Главное меню\n"
            "/menu - Открыть главное меню\n"
            "/help - Показать эту справку\n\n"
            "<b>Команды обходов:</b>\n"
            "/patrol_[ID] - Просмотр конкретного патруля (например: /patrol_15)\n\n"
            "<b>Дополнительно:</b>\n"
            "/whoami - Информация о вашем профиле\n\n"
            "💡 <i>Вы можете вызвать меню в любой момент командой /menu или /start</i>"
        )
    else:  # guest
        help_text = (
            "📖 <b>Справка GuardBot</b>\n\n"
            "🔑 Ваша роль: <b>Гость</b>\n\n"
            "<b>Доступные команды:</b>\n"
            "/start - Главное меню\n"
            "/menu - Открыть главное меню\n"
            "/help - Показать эту справку\n\n"
            "💡 <i>Вы можете подать заявку на пропуск через главное меню</i>"
        )
    
    # Добавляем кнопку главного меню
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ])
    
    await message.answer(help_text, reply_markup=keyboard, parse_mode="HTML")


async def show_main_menu(callback_or_message, user_role: str, user_name: str):
    """Render the main menu according to the user role."""
    # Determine user id for logging
    try:
        telegram_id = (
            callback_or_message.from_user.id
            if hasattr(callback_or_message, "from_user") and callback_or_message.from_user
            else getattr(getattr(callback_or_message, "message", None), "chat", None).id  # type: ignore[attr-defined]
        )
    except Exception:
        telegram_id = None

    logger.info(
        "render_main_menu role=%s user=%s tg=%s build=%s",
        user_role,
        user_name,
        telegram_id,
        BUILD_STAMP,
    )
    if user_role == Role.ADMIN.value:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📂 Управление заявками", callback_data="menu_requests_management")],
            [InlineKeyboardButton(text="🛡️ Управление обходами", callback_data="menu_patrol_management")],
            [InlineKeyboardButton(text="👥 Управление пользователями", callback_data="menu_users")],
            [InlineKeyboardButton(text="📝 Подать заявку", callback_data="menu_request")],
        ])
        text = (
            f"👋 {user_name}\n🔑 Ваша роль: <b>Администратор</b>\n\n"
            f"Выберите действие:\n\n<code>{BUILD_STAMP}</code>"
        )
    elif user_role == Role.GUARD.value:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📂 Управление заявками", callback_data="menu_requests_management")],
            [InlineKeyboardButton(text="🛡️ Управление обходами", callback_data="menu_patrol_management")],
        ])
        text = (
            f"👋 {user_name}\n🔑 Ваша роль: <b>Охранник</b>\n\n"
            f"Выберите действие:\n\n<code>{BUILD_STAMP}</code>"
        )
    else:  # guest
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📝 Подать заявку", callback_data="menu_request")],
        ])
        text = f"👋 {user_name}\n\nВыберите действие:\n\n<code>{BUILD_STAMP}</code>"

    # Safety net: if role is admin/guard but button is missing (e.g., from stale cache), insert it
    if user_role in (Role.ADMIN.value, Role.GUARD.value):
        has_patrol = any(
            any(getattr(btn, 'callback_data', '') == 'menu_patrol_management' for btn in row)
            for row in keyboard.inline_keyboard
        )
        if not has_patrol:
            keyboard.inline_keyboard.insert(1, [InlineKeyboardButton(text="🛡️ Управление обходами", callback_data="menu_patrol_management")])

    if isinstance(callback_or_message, CallbackQuery):
        await callback_or_message.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    else:  # Message
        await callback_or_message.answer(text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data == "main_menu")
async def back_to_main_menu(callback: CallbackQuery):
    """Return to the main menu for the current user."""
    telegram_id = callback.from_user.id
    async with get_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
    if not user:
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return

    await show_main_menu(callback, user.role, user.name)
    logger.info("back_to_main_menu tg=%s build=%s", telegram_id, BUILD_STAMP)
    await callback.answer()


@router.callback_query(F.data == "menu_users")
async def menu_users(callback: CallbackQuery):
    """Open users management (admin only UI)."""
    from handlers.admin import show_users_list
    logger.info("menu_users tg=%s build=%s", callback.from_user.id, BUILD_STAMP)
    await show_users_list(callback)


@router.callback_query(F.data == "menu_request")
async def menu_request(callback: CallbackQuery, state: FSMContext):
    """Start applicant flow (guest request creation)."""
    from states.applicant import ApplicantStates

    telegram_id = callback.from_user.id
    async with get_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
    if not user:
        await callback.answer("❌ Ошибка: пользователь не найден", show_alert=True)
        return
    if user.is_blocked:
        await callback.answer("⛔ Доступ ограничен", show_alert=True)
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🚶 Пешеход", callback_data="passtype_pedestrian"),
            InlineKeyboardButton(text="🚗 Транспорт", callback_data="passtype_vehicle"),
        ],
        [InlineKeyboardButton(text="↩️ Отмена", callback_data="cancel_request")],
    ])

    await state.set_state(ApplicantStates.pass_type)
    await callback.message.edit_text(
        "📝 <b>Создание пропуска на территорию</b>\n\n"
        "Выберите тип пропуска:",
        reply_markup=keyboard,
        parse_mode="HTML",
    )
    await callback.answer()
    logger.info("menu_request tg=%s build=%s", telegram_id, BUILD_STAMP)


@router.callback_query(F.data == "menu_active")
async def menu_active(callback: CallbackQuery):
    """Open active passes list (existing implementation)."""
    from handlers.guard import show_active_passes
    logger.info("menu_active tg=%s build=%s", callback.from_user.id, BUILD_STAMP)
    await show_active_passes(callback)


@router.callback_query(F.data == "menu_archive")
async def menu_archive(callback: CallbackQuery):
    """Open archive passes list (existing implementation)."""
    from handlers.guard import show_archive
    logger.info("menu_archive tg=%s build=%s", callback.from_user.id, BUILD_STAMP)
    await show_archive(callback)
