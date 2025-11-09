"""
Админские команды: управление пользователями
"""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from database.session import get_session
from database.models import User
from utils.constants import Role

router = Router()


@router.message(Command("users"))
async def cmd_users(message: Message):
    """Список всех пользователей (только для админа)"""
    telegram_id = message.from_user.id
    
    async with get_session() as session:
        # Проверяем, что пользователь - админ
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        current_user = result.scalar_one_or_none()
        
        if not current_user or current_user.role != Role.ADMIN.value:
            await message.answer("❌ Эта команда доступна только администраторам.")
            return
        
        # Получаем всех пользователей
        result = await session.execute(select(User).order_by(User.registered_at.desc()))
        users = result.scalars().all()
    
    if not users:
        await message.answer("📋 Пользователей пока нет.")
        return
    
    # Показываем каждого пользователя с кнопками
    for user in users:
        status = "🔴 Заблокирован" if user.is_blocked else "🟢 Активен"
        role_emoji = {"admin": "👑", "guard": "🛡", "guest": "👤"}.get(user.role, "❓")
        
        text = (
            f"{role_emoji} <b>{user.name}</b>\n"
            f"   ID: {user.id} | TG: {user.telegram_id}\n"
            f"   📱 {user.phone_number or 'N/A'}\n"
            f"   Роль: {user.role} | {status}\n"
        )
        
        # Кнопки управления пользователем
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="👑 Admin", callback_data=f"setrole_{user.id}_admin"),
                InlineKeyboardButton(text="🛡 Guard", callback_data=f"setrole_{user.id}_guard"),
                InlineKeyboardButton(text="👤 Guest", callback_data=f"setrole_{user.id}_guest"),
            ],
            [
                InlineKeyboardButton(
                    text="🔓 Разблокировать" if user.is_blocked else "🔒 Заблокировать",
                    callback_data=f"toggleblock_{user.id}"
                )
            ],
            [
                InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
            ]
        ])
        
        await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


async def show_users_list(callback: CallbackQuery, page: int = 0):
    """Показать список пользователей (вызывается из меню)"""
    telegram_id = callback.from_user.id
    
    async with get_session() as session:
        # Проверяем, что пользователь - админ
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        current_user = result.scalar_one_or_none()
        
        if not current_user or current_user.role != Role.ADMIN.value:
            await callback.answer("❌ Недостаточно прав", show_alert=True)
            return
        
        # Получаем всех пользователей
        result = await session.execute(select(User).order_by(User.registered_at.desc()))
        users = result.scalars().all()
    
    if not users:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
        ])
        await callback.message.edit_text("📋 Пользователей пока нет.", reply_markup=keyboard)
        await callback.answer()
        return
    
    # Проверяем границы страницы
    total_users = len(users)
    if page < 0:
        page = 0
    elif page >= total_users:
        page = total_users - 1
    
    # Показываем пользователя на текущей странице
    user = users[page]
    status = "🔴 Заблокирован" if user.is_blocked else "🟢 Активен"
    role_emoji = {"admin": "👑", "guard": "🛡", "guest": "👤"}.get(user.role, "❓")
    
    text = (
        f"👥 <b>Управление пользователями</b> ({page + 1} из {total_users})\n\n"
        f"{role_emoji} <b>{user.name}</b>\n"
        f"   ID: {user.id} | TG: {user.telegram_id}\n"
        f"   📱 {user.phone_number or 'N/A'}\n"
        f"   Роль: {user.role} | {status}\n"
    )
    
    # Кнопки управления пользователем
    buttons = [
        [
            InlineKeyboardButton(text="👑 Admin", callback_data=f"setrole_{user.id}_admin_{page}"),
            InlineKeyboardButton(text="🛡 Guard", callback_data=f"setrole_{user.id}_guard_{page}"),
            InlineKeyboardButton(text="👤 Guest", callback_data=f"setrole_{user.id}_guest_{page}"),
        ],
        [
            InlineKeyboardButton(
                text="🔓 Разблокировать" if user.is_blocked else "🔒 Заблокировать",
                callback_data=f"toggleblock_{user.id}_{page}"
            )
        ]
    ]
    
    # ВСЕГДА показываем кнопки навигации, если пользователей больше одного
    if total_users > 1:
        nav_buttons = []
        # Кнопка "Назад" (активна если не на первой странице)
        nav_buttons.append(
            InlineKeyboardButton(
                text="◀️ Назад" if page > 0 else "◀️ —",
                callback_data=f"users_page_{page - 1}" if page > 0 else "noop"
            )
        )
        # Показываем номер страницы
        nav_buttons.append(
            InlineKeyboardButton(text=f"· {page + 1}/{total_users} ·", callback_data="noop")
        )
        # Кнопка "Вперед" (активна если не на последней странице)
        nav_buttons.append(
            InlineKeyboardButton(
                text="Вперед ▶️" if page < total_users - 1 else "— ▶️",
                callback_data=f"users_page_{page + 1}" if page < total_users - 1 else "noop"
            )
        )
        buttons.append(nav_buttons)
    
    # Кнопка возврата в главное меню
    buttons.append([
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("users_page_"))
async def callback_users_pagination(callback: CallbackQuery):
    """Обработка навигации по пользователям"""
    page = int(callback.data.split("_")[-1])
    await callback.answer()
    await show_users_list(callback, page)


@router.callback_query(F.data == "noop")
async def callback_noop(callback: CallbackQuery):
    """Пустое действие (для неактивных кнопок)"""
    await callback.answer()


@router.callback_query(F.data.startswith("setrole_"))
async def callback_set_role(callback: CallbackQuery):
    """Изменение роли пользователя"""
    parts = callback.data.split("_")
    user_id = int(parts[1])
    new_role = parts[2]
    page = int(parts[3]) if len(parts) > 3 else 0
    
    # Проверяем, что вызывающий - админ
    telegram_id = callback.from_user.id
    
    async with get_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        current_user = result.scalar_one_or_none()
        
        if not current_user or current_user.role != Role.ADMIN.value:
            await callback.answer("❌ Недостаточно прав", show_alert=True)
            return
        
        # Получаем целевого пользователя
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        target_user = result.scalar_one_or_none()
        
        if not target_user:
            await callback.answer("❌ Пользователь не найден", show_alert=True)
            return
        
        # Обновляем роль
        old_role = target_user.role
        target_user.role = new_role
        await session.commit()
    
    # Показываем уведомление БЕЗ алерта
    await callback.answer(f"✅ {old_role} → {new_role}")
    
    # Обновляем список с текущей страницей
    await show_users_list(callback, page)


@router.callback_query(F.data.startswith("toggleblock_"))
async def callback_toggle_block(callback: CallbackQuery):
    """Блокировка/разблокировка пользователя"""
    parts = callback.data.split("_")
    user_id = int(parts[1])
    page = int(parts[2]) if len(parts) > 2 else 0
    
    # Проверяем, что вызывающий - админ
    telegram_id = callback.from_user.id
    
    async with get_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        current_user = result.scalar_one_or_none()
        
        if not current_user or current_user.role != Role.ADMIN.value:
            await callback.answer("❌ Недостаточно прав", show_alert=True)
            return
        
        # Получаем целевого пользователя
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        target_user = result.scalar_one_or_none()
        
        if not target_user:
            await callback.answer("❌ Пользователь не найден", show_alert=True)
            return
        
        # Переключаем статус блокировки
        target_user.is_blocked = not target_user.is_blocked
        await session.commit()
        
        status_text = "🔒 Заблокирован" if target_user.is_blocked else "🔓 Разблокирован"
    
    # Показываем уведомление БЕЗ алерта
    await callback.answer(f"✅ {status_text}")
    
    # Обновляем список с текущей страницей
    await show_users_list(callback, page)
