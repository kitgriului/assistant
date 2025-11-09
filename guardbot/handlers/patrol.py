"""
Модуль обходов - простой и понятный интерфейс
"""
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    ReplyKeyboardMarkup, 
    KeyboardButton,
    ReplyKeyboardRemove
)
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload
import datetime
import logging

from states.guard import PatrolStates
from database.session import get_session
from database.models import User, PatrolEvent, PatrolCheckpoint, CheckpointPhoto, PatrolQuestion, PatrolAnswer
from utils.media import save_file
from utils.user_helpers import check_user_access
from utils.constants import Role

logger = logging.getLogger(__name__)
router = Router()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def safe_edit_message(
    message: types.Message,
    text: str,
    reply_markup: InlineKeyboardMarkup = None,
    parse_mode: str = "HTML"
):
    """
    Безопасное редактирование сообщения с fallback на answer
    Если редактирование не удалось - отправляем новое сообщение
    """
    try:
        await message.edit_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
    except TelegramBadRequest as e:
        if "message can't be edited" in str(e).lower() or "message to edit not found" in str(e).lower():
            logger.warning(f"Can't edit message, sending new one: {e}")
            await message.answer(text, reply_markup=reply_markup, parse_mode=parse_mode)
        else:
            raise


# ============================================================================
# ГЛАВНОЕ МЕНЮ ОБХОДОВ
# ============================================================================

@router.callback_query(F.data == "menu_patrol_management")
async def patrol_main_menu(callback: types.CallbackQuery, state: FSMContext):
    """Главное меню обходов"""
    telegram_id = callback.from_user.id
    has_access, user = await check_user_access(telegram_id, [Role.GUARD.value, Role.ADMIN.value])
    if not has_access:
        await callback.answer("❌ Нет прав", show_alert=True)
        return

    # Закрываем старые незавершенные патрули (старше 24 часов)
    async with get_session() as session:
        cutoff_time = datetime.datetime.utcnow() - datetime.timedelta(hours=24)
        old_patrols = await session.execute(
            select(PatrolEvent)
            .where(
                PatrolEvent.guard_id == user.id,
                PatrolEvent.status == 'in_progress',
                PatrolEvent.started_at < cutoff_time
            )
        )
        for old_patrol in old_patrols.scalars():
            old_patrol.status = 'completed'
            old_patrol.completed_at = datetime.datetime.utcnow()
            logger.warning(f"Auto-closed old patrol {old_patrol.id} for user {user.id}")
        await session.commit()
    
    # Проверяем активный обход (берем последний если их несколько)
    async with get_session() as session:
        result = await session.execute(
            select(PatrolEvent)
            .where(
                PatrolEvent.guard_id == user.id,
                PatrolEvent.status == 'in_progress'
            )
            .options(selectinload(PatrolEvent.checkpoints))
            .order_by(PatrolEvent.started_at.desc())  # Последний по дате
            .limit(1)
        )
        active_patrol = result.scalar_one_or_none()  # Теперь внутри сессии

    if active_patrol:
        # Есть активный обход
        points_count = len(active_patrol.checkpoints)
        started = active_patrol.started_at.strftime('%d.%m %H:%M')
        
        text = (
            f"🛡️ <b>Обходы</b>\n\n"
            f"▶️ <b>Активный обход</b>\n"
            f"Начат: {started}\n"
            f"Точек: {points_count}\n"
        )
        
        buttons = [
            [InlineKeyboardButton(text="➕ Добавить точку", callback_data="patrol_add_point")],
            [InlineKeyboardButton(text="📋 Список точек", callback_data="patrol_show_points")],
            [InlineKeyboardButton(text="✅ Завершить обход", callback_data="patrol_finish")],
            [InlineKeyboardButton(text="📂 Архив", callback_data="patrol_archive")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
        ]
    else:
        # Нет активного обхода
        text = "🛡️ <b>Обходы</b>\n\nНет активного обхода"
        
        buttons = [
            [InlineKeyboardButton(text="🚶 Начать обход", callback_data="patrol_start")],
            [InlineKeyboardButton(text="📂 Архив", callback_data="patrol_archive")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
        ]
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await safe_edit_message(callback.message, text, reply_markup=keyboard)
    await callback.answer()


# ============================================================================
# НАЧАТЬ ОБХОД
# ============================================================================

@router.callback_query(F.data == "patrol_start")
async def patrol_start(callback: types.CallbackQuery, state: FSMContext):
    """Начать новый обход"""
    telegram_id = callback.from_user.id
    has_access, user = await check_user_access(telegram_id, [Role.GUARD.value, Role.ADMIN.value])
    if not has_access:
        await callback.answer("❌ Нет прав", show_alert=True)
        return

    # Создаём обход
    async with get_session() as session:
        new_patrol = PatrolEvent(
            guard_id=user.id,
            started_at=datetime.datetime.utcnow(),
            status='in_progress'
        )
        session.add(new_patrol)
        await session.commit()
        await session.refresh(new_patrol)
        patrol_id = new_patrol.id

    await state.update_data(patrol_id=patrol_id)
    await callback.answer("✅ Обход начат!")
    
    # Возвращаемся в главное меню обходов
    await patrol_main_menu(callback, state)


# ============================================================================
# ДОБАВИТЬ ТОЧКУ
# ============================================================================

@router.callback_query(F.data == "patrol_add_point")
async def patrol_add_point(callback: types.CallbackQuery, state: FSMContext):
    """Начать добавление точки обхода"""
    telegram_id = callback.from_user.id
    has_access, user = await check_user_access(telegram_id, [Role.GUARD.value, Role.ADMIN.value])
    if not has_access:
        await callback.answer("❌ Нет прав", show_alert=True)
        return

    try:
        # Получаем активный обход
        async with get_session() as session:
            result = await session.execute(
                select(PatrolEvent)
                .where(
                    PatrolEvent.guard_id == user.id,
                    PatrolEvent.status == 'in_progress'
                )
            )
            patrol = result.scalar_one_or_none()
            
            if not patrol:
                await callback.answer("❌ Нет активного обхода", show_alert=True)
                return
            
            # Получаем количество точек
            count_result = await session.execute(
                select(func.count(PatrolCheckpoint.id))
                .where(PatrolCheckpoint.event_id == patrol.id)
            )
            checkpoint_count = count_result.scalar() or 0
            
            # Создаём точку
            new_point = PatrolCheckpoint(
                event_id=patrol.id,
                checkpoint_number=checkpoint_count + 1,
                timestamp=datetime.datetime.utcnow()
            )
            session.add(new_point)
            await session.commit()
            await session.refresh(new_point)
            point_id = new_point.id
            point_num = new_point.checkpoint_number

        await state.update_data(point_id=point_id, photos_count=0, has_location=False)
        await state.set_state(PatrolStates.waiting_photo)  # Сразу переходим к фото
        
        text = (
            f"📍 <b>Новая точка #{point_num}</b>\n\n"
            f"<b>Шаг 1/3: Фотографии</b>\n"
            f"� Отправьте фото точки обхода\n\n"
            f"<i>� Можете отправить несколько фото подряд (до 10)</i>\n"
            f"<i>⚠️ Обязательно: минимум 1 фото</i>"
        )
        
        buttons = [
            [InlineKeyboardButton(text="❌ Отменить точку", callback_data="point_cancel")]
        ]
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        await safe_edit_message(callback.message, text, reply_markup=keyboard)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error adding patrol point: {e}")
        await callback.answer("❌ Ошибка при добавлении точки. Попробуйте снова.", show_alert=True)


@router.callback_query(F.data == "point_add_photo")
async def point_add_photo(callback: types.CallbackQuery, state: FSMContext):
    """Запросить фото для точки"""
    data = await state.get_data()
    photos_count = data.get('photos_count', 0)
    
    if photos_count >= 10:
        await callback.answer("❌ Максимум 10 фото на точку", show_alert=True)
        return
    
    await state.set_state(PatrolStates.waiting_photo)
    
    buttons = [
        [InlineKeyboardButton(text="◀️ Назад в меню точки", callback_data="point_back")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await callback.message.answer(
        f"📸 <b>Добавление фото ({photos_count}/10)</b>\n\n"
        f"Отправьте фото.\n"
        f"Можете добавить ещё {10 - photos_count} фото.",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(PatrolStates.waiting_photo, F.photo)
async def handle_photo(message: types.Message, state: FSMContext, album: list = None, is_album: bool = False):
    """Сохранить фото точки (поддержка одиночных фото и альбомов)"""
    data = await state.get_data()
    point_id = data.get('point_id')
    
    if not point_id:
        await message.answer("❌ Ошибка: точка не найдена")
        return
    
    # Определяем список фото для обработки
    if is_album and album:
        # Альбом - несколько фото
        photos_to_save = [msg.photo[-1] for msg in album]
        logger.info(f"Processing album: {len(photos_to_save)} photos")
    else:
        # Одиночное фото
        photos_to_save = [message.photo[-1]]
    
    # Сохраняем фото
    async with get_session() as session:
        # Проверяем текущее количество фото
        count_result = await session.execute(
            select(func.count(CheckpointPhoto.id))
            .where(CheckpointPhoto.checkpoint_id == point_id)
        )
        current_photos = count_result.scalar() or 0
        
        # Проверка лимита
        remaining_slots = 10 - current_photos
        if remaining_slots <= 0:
            await message.answer("❌ Максимум 10 фото на точку")
            return
        
        # Ограничиваем количество сохраняемых фото лимитом
        photos_to_save = photos_to_save[:remaining_slots]
        saved_count = 0
        
        # Сохраняем каждое фото
        for photo in photos_to_save:
            try:
                file_path = await save_file(message.bot, photo, "patrol")
                
                new_photo = CheckpointPhoto(
                    checkpoint_id=point_id,
                    photo_path=file_path,
                    uploaded_at=datetime.datetime.utcnow()
                )
                session.add(new_photo)
                saved_count += 1
                
            except Exception as e:
                logger.error(f"Error saving photo: {e}")
                continue
        
        await session.commit()
        
        # Обновляем счётчик
        photos_count = current_photos + saved_count
    
    await state.update_data(photos_count=photos_count)
    
    # НЕ меняем состояние - остаёмся в waiting_photo для добавления следующего фото
    # await state.set_state(PatrolStates.adding_point)  # УБРАЛИ эту строку
    
    # Показываем обновлённое меню точки с возможностью добавить ещё фото
    async with get_session() as session:
        result = await session.execute(
            select(PatrolCheckpoint).where(PatrolCheckpoint.id == point_id)
        )
        point = result.scalar_one_or_none()
        
        if not point:
            return
        
        point_num = point.checkpoint_number
        has_location = point.latitude is not None
        has_note = point.notes is not None
    
    # Иконки статуса
    photo_status = "✅" if photos_count >= 1 else "❌"
    location_status = "✅" if has_location else "❌"
    note_status = "✅" if has_note else "⏹️"
    
    remaining = 10 - photos_count
    menu_text = (
        f"✅ <b>Фото добавлено!</b> ({photos_count}/10)\n\n"
        f"📍 <b>Точка №{point_num}</b>\n\n"
        f"📸 Фото: {photos_count}/10 {photo_status}\n"
        f"📍 Геолокация: {'Добавлена' if has_location else 'Не добавлена'} {location_status}\n"
        f"📝 Заметка: {'Добавлена' if has_note else 'Нет'} {note_status}\n\n"
    )
    
    if remaining > 0:
        menu_text += f"<i>💡 Можете добавить ещё {remaining} фото</i>\n\n"
    
    if photos_count == 0 or not has_location:
        menu_text += "<i>⚠️ Для сохранения: минимум 1 фото и геолокация</i>"
    else:
        menu_text += "<i>✅ Готово к сохранению</i>"
    
    # Простое меню с подсказкой
    remaining = 10 - photos_count
    step_text = (
        f"✅ <b>Фото добавлено!</b> ({photos_count}/10)\n\n"
        f"<b>Шаг 1/3: Фотографии</b>\n"
    )
    
    if remaining > 0:
        step_text += f"� Можете отправить ещё {remaining} фото\n\n"
        step_text += f"<i>💡 Отправьте следующее фото или нажмите \"Далее\"</i>"
    else:
        step_text += f"<i>✅ Максимум фото достигнут</i>"
    
    buttons = [
        [InlineKeyboardButton(text="➡️ Далее: Геолокация", callback_data="point_photos_done")],
        [InlineKeyboardButton(text="❌ Отменить точку", callback_data="point_cancel")]
    ]
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer(step_text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data == "point_photos_done")
async def point_photos_done(callback: types.CallbackQuery, state: FSMContext):
    """Завершить добавление фото и перейти к геолокации"""
    data = await state.get_data()
    point_id = data.get('point_id')
    photos_count = data.get('photos_count', 0)
    
    # ОБЯЗАТЕЛЬНО минимум 1 фото
    if photos_count == 0:
        await callback.answer("❌ Необходимо добавить минимум 1 фото!", show_alert=True)
        return
    
    await state.set_state(PatrolStates.waiting_location)
    
    async with get_session() as session:
        result = await session.execute(
            select(PatrolCheckpoint).where(PatrolCheckpoint.id == point_id)
        )
        point = result.scalar_one_or_none()
        point_num = point.checkpoint_number if point else 0
    
    text = (
        f"📍 <b>Точка #{point_num}</b>\n\n"
        f"<b>Шаг 2/3: Геолокация</b>\n"
        f"📍 Отправьте вашу текущую геолокацию\n\n"
        f"<i>💡 Используйте кнопку \"📎\" → \"Геопозиция\" в Telegram</i>"
    )
    
    # Кнопка с отправкой геолокации
    location_button = KeyboardButton(text="📍 Отправить геолокацию", request_location=True)
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[location_button]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    
    await callback.message.answer(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "point_add_location")
async def point_add_location(callback: types.CallbackQuery, state: FSMContext):
    """Запросить геолокацию"""
    await state.set_state(PatrolStates.waiting_location)
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📍 Отправить геолокацию", request_location=True)],
            [KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True
    )
    
    await callback.message.answer(
        "📍 Отправьте геолокацию точки обхода",
        reply_markup=keyboard
    )
    await callback.answer()


@router.message(PatrolStates.waiting_location, F.location)
async def handle_location(message: types.Message, state: FSMContext):
    """Сохранить геолокацию"""
    data = await state.get_data()
    point_id = data.get('point_id')
    
    if not point_id:
        await message.answer("❌ Ошибка: точка не найдена", reply_markup=ReplyKeyboardRemove())
        return
    
    async with get_session() as session:
        result = await session.execute(
            select(PatrolCheckpoint).where(PatrolCheckpoint.id == point_id)
        )
        point = result.scalar_one_or_none()
        
        if not point:
            await message.answer("❌ Точка не найдена", reply_markup=ReplyKeyboardRemove())
            return
            
        point.latitude = message.location.latitude
        point.longitude = message.location.longitude
        await session.commit()
        
        point_num = point.checkpoint_number
        has_note = point.notes is not None
        
        # Получаем реальное количество фото из БД
        count_result = await session.execute(
            select(func.count(CheckpointPhoto.id))
            .where(CheckpointPhoto.checkpoint_id == point_id)
        )
        photos_count = count_result.scalar() or 0
    
    await state.update_data(has_location=True, photos_count=photos_count)
    
    # Возврат в меню точки
    await state.set_state(PatrolStates.adding_point)
    
    # Пошаговое меню
    text = (
        f"✅ <b>Геолокация добавлена!</b>\n\n"
        f"<b>Шаг 3/3: Заметка (опционально)</b>\n"
        f"📝 Хотите добавить заметку к точке?\n\n"
        f"<i>💡 Заметка помогает запомнить особенности точки</i>"
    )
    
    buttons = [
        [InlineKeyboardButton(text="📝 Добавить заметку", callback_data="point_add_note")],
        [InlineKeyboardButton(text="✅ Завершить точку", callback_data="point_save")],
        [InlineKeyboardButton(text="❌ Отменить точку", callback_data="point_cancel")]
    ]
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    # Убираем ReplyKeyboard
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
    
    # Убираем reply клавиатуру
    await message.answer(".", reply_markup=ReplyKeyboardRemove(), parse_mode=None)
    await message.delete()


@router.callback_query(F.data == "point_add_note")
async def point_add_note(callback: types.CallbackQuery, state: FSMContext):
    """Запросить заметку"""
    await state.set_state(PatrolStates.waiting_notes)
    
    buttons = [
        [InlineKeyboardButton(text="◀️ Назад", callback_data="point_back")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await callback.message.answer(
        "📝 Введите заметку о точке обхода",
        reply_markup=keyboard
    )
    await callback.answer()


@router.message(PatrolStates.waiting_notes, F.text)
async def handle_note(message: types.Message, state: FSMContext):
    """Сохранить заметку"""
    data = await state.get_data()
    point_id = data.get('point_id')
    
    if not point_id:
        await message.answer("❌ Ошибка: точка не найдена")
        return
    
    async with get_session() as session:
        result = await session.execute(
            select(PatrolCheckpoint).where(PatrolCheckpoint.id == point_id)
        )
        point = result.scalar_one_or_none()
        
        if point:
            point.notes = message.text
            await session.commit()
    
    await state.set_state(PatrolStates.adding_point)
    
    # Отправляем новое сообщение вместо редактирования (нельзя редактировать чужое)
    data = await state.get_data()
    point_id = data.get("point_id")
    
    async with get_session() as session:
        # Получаем количество фото
        count_result = await session.execute(
            select(func.count(CheckpointPhoto.id))
            .where(CheckpointPhoto.checkpoint_id == point_id)
        )
        photos_count = count_result.scalar() or 0
    
    await state.update_data(photos_count=photos_count)
    await state.set_state(PatrolStates.adding_point)
    
    # Простое подтверждение
    text = (
        f"✅ <b>Заметка добавлена!</b>\n\n"
        f"<i>Точка готова к сохранению</i>"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Завершить точку", callback_data="point_save")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data="point_cancel")]
    ])
    
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data == "point_save")
async def point_save(callback: types.CallbackQuery, state: FSMContext):
    """Сохранить точку обхода"""
    data = await state.get_data()
    point_id = data.get('point_id')
    photos_count = data.get('photos_count', 0)
    
    # ОБЯЗАТЕЛЬНАЯ проверка фото
    if photos_count == 0:
        await callback.answer("❌ Необходимо минимум 1 фото!", show_alert=True)
        return
    
    # ОБЯЗАТЕЛЬНАЯ проверка геолокации
    async with get_session() as session:
        result = await session.execute(
            select(PatrolCheckpoint).where(PatrolCheckpoint.id == point_id)
        )
        point = result.scalar_one_or_none()
        
        if not point or point.latitude is None:
            await callback.answer("❌ Необходимо добавить геолокацию!", show_alert=True)
            return
    
    await state.clear()
    await callback.answer("✅ Точка сохранена!")
    
    # Возврат в главное меню обходов
    await patrol_main_menu(callback, state)


@router.callback_query(F.data == "point_cancel")
async def point_cancel(callback: types.CallbackQuery, state: FSMContext):
    """Отменить добавление точки"""
    data = await state.get_data()
    point_id = data.get('point_id')
    
    # Удаляем точку
    if point_id:
        async with get_session() as session:
            result = await session.execute(
                select(PatrolCheckpoint).where(PatrolCheckpoint.id == point_id)
            )
            point = result.scalar_one_or_none()
            if point:
                await session.delete(point)
                await session.commit()
    
    await state.clear()
    await callback.answer("❌ Отменено")
    
    # Возврат в главное меню обходов
    await patrol_main_menu(callback, state)


# ============================================================================
# СПИСОК ТОЧЕК ТЕКУЩЕГО ОБХОДА
# ============================================================================

@router.callback_query(F.data == "patrol_show_points")
async def patrol_show_points(callback: types.CallbackQuery, state: FSMContext):
    """Показать список точек текущего обхода"""
    telegram_id = callback.from_user.id
    has_access, user = await check_user_access(telegram_id, [Role.GUARD.value, Role.ADMIN.value])
    if not has_access:
        await callback.answer("❌ Нет прав", show_alert=True)
        return

    async with get_session() as session:
        result = await session.execute(
            select(PatrolEvent)
            .where(
                PatrolEvent.guard_id == user.id,
                PatrolEvent.status == 'in_progress'
            )
            .options(selectinload(PatrolEvent.checkpoints).selectinload(PatrolCheckpoint.photos))
        )
        patrol = result.scalar_one_or_none()
        
        if not patrol:
            await callback.answer("❌ Нет активного обхода", show_alert=True)
            return
        
        points = patrol.checkpoints
    
    if not points:
        text = "📋 <b>Точки обхода</b>\n\nТочек пока нет"
        buttons = [
            [InlineKeyboardButton(text="◀️ Назад", callback_data="menu_patrol_management")]
        ]
    else:
        text = f"📋 <b>Точки обхода</b> ({len(points)})\n\n"
        
        for point in sorted(points, key=lambda p: p.checkpoint_number):
            photos = len(point.photos)
            location = "📍" if point.latitude else "⏹️"
            note = "📝" if point.notes else "⏹️"
            time = point.timestamp.strftime('%H:%M')
            
            text += f"{point.checkpoint_number}. {time} | {photos}📸 {location} {note}\n"
        
        buttons = [
            [InlineKeyboardButton(text="◀️ Назад", callback_data="menu_patrol_management")]
        ]
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await safe_edit_message(callback.message, text, reply_markup=keyboard)
    await callback.answer()


# ============================================================================
# ЗАВЕРШИТЬ ОБХОД
# ============================================================================

@router.callback_query(F.data == "patrol_finish")
async def patrol_finish(callback: types.CallbackQuery, state: FSMContext):
    """Завершить обход"""
    telegram_id = callback.from_user.id
    has_access, user = await check_user_access(telegram_id, [Role.GUARD.value, Role.ADMIN.value])
    if not has_access:
        await callback.answer("❌ Нет прав", show_alert=True)
        return

    async with get_session() as session:
        result = await session.execute(
            select(PatrolEvent)
            .where(
                PatrolEvent.guard_id == user.id,
                PatrolEvent.status == 'in_progress'
            )
            .options(selectinload(PatrolEvent.checkpoints))
        )
        patrol = result.scalar_one_or_none()
        
        if not patrol:
            await callback.answer("❌ Нет активного обхода", show_alert=True)
            return
        
        if len(patrol.checkpoints) == 0:
            await callback.answer("⚠️ Добавьте хотя бы одну точку!", show_alert=True)
            return
        
        patrol.status = 'completed'
        patrol.completed_at = datetime.datetime.utcnow()
        await session.commit()
        
        points_count = len(patrol.checkpoints)
    
    await state.clear()
    
    text = f"✅ <b>Обход завершен!</b>\n\nТочек пройдено: {points_count}"
    
    buttons = [
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ]
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await safe_edit_message(callback.message, text, reply_markup=keyboard)
    await callback.answer("✅ Обход завершен!")


# ============================================================================
# АРХИВ ОБХОДОВ
# ============================================================================

@router.callback_query(F.data.startswith("patrol_archive"))
async def patrol_archive(callback: types.CallbackQuery, state: FSMContext):
    """Архив завершенных обходов с пагинацией"""
    telegram_id = callback.from_user.id
    has_access, user = await check_user_access(telegram_id, [Role.GUARD.value, Role.ADMIN.value])
    if not has_access:
        await callback.answer("❌ Нет прав", show_alert=True)
        return
    
    # Получаем номер страницы
    parts = callback.data.split("_")
    page = int(parts[2]) if len(parts) > 2 else 1
    per_page = 5
    
    async with get_session() as session:
        # Для админа - все обходы, для охранника - только свои
        if user.role == Role.ADMIN.value:
            query = select(PatrolEvent).where(PatrolEvent.status == 'completed')
        else:
            query = select(PatrolEvent).where(
                PatrolEvent.guard_id == user.id,
                PatrolEvent.status == 'completed'
            )
        
        # Считаем всего
        count_result = await session.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar()
        
        if total == 0:
            text = "📂 <b>Архив обходов</b>\n\nОбходов пока нет"
            buttons = [
                [InlineKeyboardButton(text="◀️ Назад", callback_data="menu_patrol_management")]
            ]
            keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
            await safe_edit_message(callback.message, text, reply_markup=keyboard)
            await callback.answer()
            return
        
        # Получаем страницу
        offset = (page - 1) * per_page
        result = await session.execute(
            query
            .order_by(desc(PatrolEvent.completed_at))
            .limit(per_page)
            .offset(offset)
            .options(selectinload(PatrolEvent.checkpoints), selectinload(PatrolEvent.guard))
        )
        patrols = result.scalars().all()
        
        total_pages = (total + per_page - 1) // per_page
    
    text = f"📂 <b>Архив обходов</b> (стр. {page}/{total_pages})\n\n"
    
    for patrol in patrols:
        completed = patrol.completed_at.strftime('%d.%m.%Y %H:%M')
        points = len(patrol.checkpoints)
        guard_name = patrol.guard.name if patrol.guard else "?"
        
        text += f"🔹 {completed}\n   {guard_name} | {points} точек\n"
        text += f"   /patrol_{patrol.id}\n\n"
    
    # Навигация
    buttons = []
    nav_buttons = []
    
    if page > 1:
        nav_buttons.append(
            InlineKeyboardButton(text="◀️", callback_data=f"patrol_archive_{page-1}")
        )
    
    nav_buttons.append(
        InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="noop")
    )
    
    if page < total_pages:
        nav_buttons.append(
            InlineKeyboardButton(text="▶️", callback_data=f"patrol_archive_{page+1}")
        )
    
    if nav_buttons:
        buttons.append(nav_buttons)
    
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="menu_patrol_management")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await safe_edit_message(callback.message, text, reply_markup=keyboard)
    await callback.answer()


# ============================================================================
# ПРОСМОТР КОНКРЕТНОГО ОБХОДА
# ============================================================================

@router.callback_query(F.data.startswith("view_patrol_"))
async def view_patrol_callback(callback: types.CallbackQuery):
    """Просмотр обхода по callback кнопке"""
    try:
        patrol_id = int(callback.data.split('_')[2])
    except (IndexError, ValueError):
        await callback.answer("❌ Неверный формат", show_alert=True)
        return
    
    # Создаём fake message для использования общей логики
    fake_message = types.Message(
        message_id=callback.message.message_id,
        date=callback.message.date,
        chat=callback.message.chat,
        from_user=callback.from_user,
        text=f"/patrol_{patrol_id}"
    )
    
    await callback.answer()
    await view_patrol_command(fake_message)


@router.message(F.text.startswith('/patrol_'))
async def view_patrol_command(message: types.Message):
    """Просмотр обхода по команде /patrol_123"""
    try:
        patrol_id = int(message.text.split('_')[1])
    except (IndexError, ValueError):
        await message.answer("❌ Неверный формат. Используйте /patrol_123")
        return
    
    telegram_id = message.from_user.id
    has_access, user = await check_user_access(telegram_id, [Role.GUARD.value, Role.ADMIN.value])
    if not has_access:
        await message.answer("❌ Нет прав")
        return
    
    async with get_session() as session:
        result = await session.execute(
            select(PatrolEvent)
            .where(PatrolEvent.id == patrol_id)
            .options(
                selectinload(PatrolEvent.checkpoints).selectinload(PatrolCheckpoint.photos),
                selectinload(PatrolEvent.guard),
                selectinload(PatrolEvent.questions).selectinload(PatrolQuestion.answer),
                selectinload(PatrolEvent.questions).selectinload(PatrolQuestion.admin)
            )
        )
        patrol = result.scalar_one_or_none()
        
        if not patrol:
            await message.answer("❌ Обход не найден")
            return
        
        # Проверка доступа (охранник видит только свои)
        if user.role != Role.ADMIN.value and patrol.guard_id != user.id:
            await message.answer("❌ Нет доступа к этому обходу")
            return
        
        guard_name = patrol.guard.name if patrol.guard else "Неизвестно"
        started = patrol.started_at.strftime('%d.%m.%Y %H:%M')
        completed = patrol.completed_at.strftime('%d.%m.%Y %H:%M') if patrol.completed_at else "—"
        status = "✅ Завершен" if patrol.status == 'completed' else "▶️ В процессе"
        
        # Основная информация
        text = (
            f"🛡️ <b>Обход #{patrol.id}</b>\n\n"
            f"👤 Охранник: {guard_name}\n"
            f"🕐 Начат: {started}\n"
            f"🕑 Завершен: {completed}\n"
            f"📊 Статус: {status}\n"
            f"📍 Точек: {len(patrol.checkpoints)}\n"
        )
        
        await message.answer(text, parse_mode="HTML")
        
        # Отправляем каждую точку обхода
        for point in sorted(patrol.checkpoints, key=lambda p: p.checkpoint_number):
            time = point.timestamp.strftime('%H:%M')
            photos_count = len(point.photos)
            
            point_text = (
                f"━━━━━━━━━━━━━━━━━━\n"
                f"📍 <b>Точка {point.checkpoint_number}</b> ({time})\n"
                f"📸 Фото: {photos_count}\n"
            )
            
            # Геолокация
            if point.latitude and point.longitude:
                point_text += f"� Координаты: {point.latitude:.6f}, {point.longitude:.6f}\n"
            
            # Заметка
            if point.notes:
                point_text += f"📝 Заметка: {point.notes}\n"
            
            # Отправляем текст точки
            await message.answer(point_text, parse_mode="HTML")
            
            # Отправляем все фото одним альбомом (media group)
            if point.photos:
                media_group = []
                for idx, photo in enumerate(point.photos):
                    try:
                        # Первое фото с подписью, остальные без
                        caption = f"Точка №{point.checkpoint_number}" if idx == 0 else None
                        media_group.append(
                            types.InputMediaPhoto(
                                media=types.FSInputFile(photo.photo_path),
                                caption=caption
                            )
                        )
                    except Exception as e:
                        logger.error(f"Error preparing photo: {e}")
                
                # Отправляем группу фото
                if media_group:
                    try:
                        await message.answer_media_group(media=media_group)
                    except Exception as e:
                        logger.error(f"Error sending media group: {e}")
                        await message.answer("❌ Ошибка отправки фото")
        
        # Вопросы и ответы (если есть)
        if patrol.questions:
            qa_text = "\n━━━━━━━━━━━━━━━━━━\n💬 <b>Вопросы и ответы:</b>\n\n"
            for q in patrol.questions:
                admin_name = q.admin.name if q.admin else "Админ"
                qa_text += f"❓ <b>{admin_name}:</b> {q.question_text}\n"
                
                if q.is_answered and q.answer:
                    qa_text += f"✅ <b>Ответ:</b> {q.answer.answer_text}\n\n"
                else:
                    qa_text += f"⏳ <i>Ожидает ответа</i>\n\n"
            
            await message.answer(qa_text, parse_mode="HTML")
        
        # Кнопки
        buttons = []
        
        # Админ может задать вопрос
        if user.role == Role.ADMIN.value:
            buttons.append([InlineKeyboardButton(
                text="❓ Задать вопрос",
                callback_data=f"patrol_ask_{patrol.id}"
            )])
        
        buttons.append([InlineKeyboardButton(
            text="📂 Обходы",
            callback_data="menu_patrol_management"
        )])
        buttons.append([InlineKeyboardButton(
            text="🏠 Главное меню",
            callback_data="main_menu"
        )])
        
        if buttons:
            keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
            await message.answer("━━━━━━━━━━━━━━━━━━", reply_markup=keyboard)


# ============================================================================
# СИСТЕМА ВОПРОСОВ-ОТВЕТОВ
# ============================================================================

@router.callback_query(F.data.startswith("patrol_ask_"))
async def patrol_ask_question(callback: types.CallbackQuery, state: FSMContext):
    """Админ задаёт вопрос по обходу"""
    patrol_id = int(callback.data.split("_")[2])
    
    telegram_id = callback.from_user.id
    has_access, user = await check_user_access(telegram_id, [Role.ADMIN.value])
    if not has_access:
        await callback.answer("❌ Нет прав", show_alert=True)
        return
    
    # Сохраняем ID обхода в state
    await state.update_data(question_patrol_id=patrol_id)
    await state.set_state(PatrolStates.asking_question)
    
    buttons = [[InlineKeyboardButton(text="❌ Отмена", callback_data="patrol_ask_cancel")]]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await callback.message.answer(
        f"❓ <b>Задать вопрос по обходу #{patrol_id}</b>\n\n"
        f"Введите ваш вопрос:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(PatrolStates.asking_question, F.text)
async def handle_question_text(message: types.Message, state: FSMContext):
    """Обработка вопроса от админа"""
    data = await state.get_data()
    patrol_id = data.get('question_patrol_id')
    
    if not patrol_id:
        await message.answer("❌ Ошибка: обход не найден")
        await state.clear()
        return
    
    telegram_id = message.from_user.id
    has_access, admin_user = await check_user_access(telegram_id, [Role.ADMIN.value])
    if not has_access:
        await message.answer("❌ Нет прав")
        await state.clear()
        return
    
    # Создаём вопрос
    async with get_session() as session:
        # Получаем обход с охранником
        result = await session.execute(
            select(PatrolEvent)
            .where(PatrolEvent.id == patrol_id)
            .options(selectinload(PatrolEvent.guard))
        )
        patrol = result.scalar_one_or_none()
        
        if not patrol:
            await message.answer("❌ Обход не найден")
            await state.clear()
            return
        
        # Создаём вопрос
        new_question = PatrolQuestion(
            event_id=patrol_id,
            admin_id=admin_user.id,
            question_text=message.text,
            asked_at=datetime.datetime.utcnow(),
            is_answered=False
        )
        session.add(new_question)
        await session.commit()
        
        guard_telegram_id = patrol.guard.telegram_id
        guard_name = patrol.guard.name
    
    await state.clear()
    
    # Отправляем подтверждение с расширенным меню
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👁 Посмотреть обход", callback_data=f"view_patrol_{patrol_id}")],
        [InlineKeyboardButton(text="📂 Обходы", callback_data="menu_patrol_management")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ])
    await message.answer(
        f"✅ Вопрос отправлен охраннику {guard_name}",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    
    # Отправляем уведомление охраннику
    try:
        buttons = [[InlineKeyboardButton(
            text="✍️ Ответить",
            callback_data=f"patrol_answer_{patrol_id}"
        )]]
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        
        await message.bot.send_message(
            chat_id=guard_telegram_id,
            text=(
                f"💬 <b>Новый вопрос по обходу #{patrol_id}</b>\n\n"
                f"Администратор спрашивает:\n"
                f"❓ {message.text}\n\n"
                f"Ответьте на вопрос:"
            ),
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error sending notification to guard: {e}")


@router.callback_query(F.data == "patrol_ask_cancel")
async def patrol_ask_cancel(callback: types.CallbackQuery, state: FSMContext):
    """Отмена задания вопроса"""
    await state.clear()
    await callback.message.answer("❌ Отменено")
    await callback.answer()


@router.callback_query(F.data == "patrol_answer_cancel")
async def patrol_answer_cancel(callback: types.CallbackQuery, state: FSMContext):
    """Отмена ответа на вопрос"""
    await state.clear()
    await callback.message.answer("❌ Отменено")
    await callback.answer()


@router.callback_query(F.data.startswith("patrol_answer_"))
async def patrol_answer_question(callback: types.CallbackQuery, state: FSMContext):
    """Охранник отвечает на вопрос"""
    # Проверяем что это не cancel (уже обработан выше)
    if callback.data == "patrol_answer_cancel":
        return
    
    try:
        patrol_id = int(callback.data.split("_")[2])
    except (IndexError, ValueError):
        await callback.answer("❌ Неверный формат команды", show_alert=True)
        return
    
    telegram_id = callback.from_user.id
    has_access, user = await check_user_access(telegram_id, [Role.GUARD.value, Role.ADMIN.value])
    if not has_access:
        await callback.answer("❌ Нет прав", show_alert=True)
        return
    
    # Получаем неотвеченные вопросы по этому обходу
    async with get_session() as session:
        result = await session.execute(
            select(PatrolQuestion)
            .where(
                PatrolQuestion.event_id == patrol_id,
                PatrolQuestion.is_answered == False
            )
            .options(selectinload(PatrolQuestion.admin))
        )
        unanswered_questions = result.scalars().all()
        
        if not unanswered_questions:
            await callback.answer("✅ Нет вопросов без ответа", show_alert=True)
            return
        
        # Берём первый неотвеченный вопрос
        question = unanswered_questions[0]
        admin_name = question.admin.name if question.admin else "Админ"
    
    # Сохраняем ID вопроса
    await state.update_data(answer_question_id=question.id)
    await state.set_state(PatrolStates.answering_question)
    
    buttons = [[InlineKeyboardButton(text="❌ Отмена", callback_data="patrol_answer_cancel")]]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await callback.message.answer(
        f"💬 <b>Вопрос от {admin_name}:</b>\n"
        f"❓ {question.question_text}\n\n"
        f"Введите ваш ответ:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(PatrolStates.answering_question, F.text)
async def handle_answer_text(message: types.Message, state: FSMContext):
    """Обработка ответа от охранника"""
    data = await state.get_data()
    question_id = data.get('answer_question_id')
    
    if not question_id:
        await message.answer("❌ Ошибка: вопрос не найден")
        await state.clear()
        return
    
    # Создаём ответ
    async with get_session() as session:
        # Получаем вопрос
        result = await session.execute(
            select(PatrolQuestion)
            .where(PatrolQuestion.id == question_id)
            .options(
                selectinload(PatrolQuestion.admin),
                selectinload(PatrolQuestion.event)
            )
        )
        question = result.scalar_one_or_none()
        
        if not question:
            await message.answer("❌ Вопрос не найден")
            await state.clear()
            return
        
        # Создаём ответ
        new_answer = PatrolAnswer(
            question_id=question_id,
            answer_text=message.text,
            answered_at=datetime.datetime.utcnow()
        )
        session.add(new_answer)
        
        # Помечаем вопрос как отвеченный
        question.is_answered = True
        await session.commit()
        
        admin_telegram_id = question.admin.telegram_id
        admin_name = question.admin.name
        patrol_id = question.event_id
    
    await state.clear()
    
    # Отправляем сообщение с расширенным меню
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👁 Посмотреть обход", callback_data=f"view_patrol_{patrol_id}")],
        [InlineKeyboardButton(text="❓ Задать еще вопрос", callback_data=f"patrol_ask_{patrol_id}")],
        [InlineKeyboardButton(text="📂 Обходы", callback_data="menu_patrol_management")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ])
    await message.answer(
        f"✅ Ответ отправлен администратору {admin_name}",
        reply_markup=keyboard
    )
    
    # Отправляем уведомление админу
    try:
        buttons = [[InlineKeyboardButton(
            text="👁 Посмотреть обход",
            callback_data=f"view_patrol_{patrol_id}"
        )]]
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        
        await message.bot.send_message(
            chat_id=admin_telegram_id,
            text=(
                f"✅ <b>Получен ответ на вопрос по обходу #{patrol_id}</b>\n\n"
                f"Ваш вопрос:\n"
                f"❓ {question.question_text}\n\n"
                f"Ответ охранника:\n"
                f"💬 {message.text}\n\n"
                f"Для просмотра обхода используйте: /patrol_{patrol_id}"
            ),
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error sending notification to admin: {e}")


# ============================================================================
# КОМАНДЫ
# ============================================================================

@router.message(Command("patrol"))
async def patrol_command(message: types.Message, state: FSMContext):
    """Быстрый доступ к обходам"""
    telegram_id = message.from_user.id
    has_access, user = await check_user_access(telegram_id, [Role.GUARD.value, Role.ADMIN.value])
    if not has_access:
        await message.answer("❌ Нет прав")
        return
    
    # Создаём фейковый callback для вызова главного меню
    fake_callback = types.CallbackQuery(
        id="fake",
        from_user=message.from_user,
        chat_instance="fake",
        message=message,
        data="menu_patrol_management"
    )
    
    await patrol_main_menu(fake_callback, state)


@router.callback_query(F.data == "noop")
async def noop_handler(callback: types.CallbackQuery):
    """Пустой обработчик для неактивных кнопок"""
    await callback.answer()


# Алиасы для совместимости
@router.callback_query(F.data == "menu_start_patrol")
async def menu_start_patrol_alias(callback: types.CallbackQuery, state: FSMContext):
    """Алиас для старого названия"""
    await patrol_start(callback, state)


@router.callback_query(F.data == "patrol_continue")
async def patrol_continue_alias(callback: types.CallbackQuery, state: FSMContext):
    """Алиас - продолжить = главное меню"""
    await patrol_main_menu(callback, state)
