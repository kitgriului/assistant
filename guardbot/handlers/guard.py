"""Handlers for Guard role: patrol check-in, confirm by QR, photo capture."""
from aiogram import Router, F, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from sqlalchemy import select, func
import tempfile
import os
import datetime

from states.guard import GuardStates
from utils.media import save_file
from utils.qr import generate_qr_bytes
from database.session import get_session
from database.models import User, Request as DBRequest
from utils.constants import Role, RequestStatus
import logging

logger = logging.getLogger(__name__)

router = Router()


def register_guard_handlers(dp: Dispatcher):
    dp.include_router(router)


@router.message(Command("pending_deprecated"))
async def cmd_pending(message: types.Message):
    """Список заявок на утверждение (для охранников и админов)"""
    telegram_id = message.from_user.id
    
    async with get_session() as session:
        # Проверяем роль пользователя
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        
        if not user or user.role not in [Role.GUARD.value, Role.ADMIN.value]:
            await message.answer("❌ Эта команда доступна только охранникам и администраторам.")
            return
        
        # Получаем все pending заявки
        result = await session.execute(
            select(DBRequest)
            .where(DBRequest.status == RequestStatus.PENDING.value)
            .order_by(DBRequest.created_at.desc())
        )
        requests = result.scalars().all()
    
    if not requests:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
        ])
        await message.answer("📋 Нет заявок, ожидающих утверждения.", reply_markup=keyboard)
        return
    
    text = f"📋 <b>Заявки на утверждение ({len(requests)}):</b>\n\n"
    
    for req in requests:
        # Определяем эмодзи и текст типа пропуска
        pass_type_emoji = "🚶" if req.pass_type == "pedestrian" else "🚗"
        pass_type_text = "Пешеход" if req.pass_type == "pedestrian" else "Автомобиль"
        
        text += (
            f"🆔 <b>Заявка #{req.id}</b>\n"
            f"👤 {req.name}\n"
            f"{pass_type_emoji} Тип: {pass_type_text}\n"
            f"📝 Цель: {req.purpose}\n"
        )
        
        # Показываем номер авто для машин
        if req.car_number:
            text += f"🚗 Номер: {req.car_number}\n"
        
        text += (
            f"📅 Визит: {req.datetime}\n"
            f"🕐 Создана: {req.created_at.strftime('%d.%m.%Y %H:%M')}\n"
        )
        
        # Кнопки для каждой заявки
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Утвердить", callback_data=f"approve_{req.id}"),
                InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_{req.id}")
            ],
            [
                InlineKeyboardButton(text="📷 Посмотреть фото", callback_data=f"viewphoto_{req.id}")
            ],
            [
                InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
            ]
        ])
        
        await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
        text = ""


async def show_pending_requests(callback: types.CallbackQuery):
    """Показать список заявок (вызывается из меню)"""
    from utils.user_helpers import check_user_access
    
    telegram_id = callback.from_user.id
    
    # Проверяем доступ (1 запрос вместо 2)
    has_access, user = await check_user_access(telegram_id, [Role.GUARD.value, Role.ADMIN.value])
    
    if not has_access:
        await callback.answer("❌ Недостаточно прав", show_alert=True)
        return
    
    # Получаем все pending заявки
    async with get_session() as session:
        result = await session.execute(
            select(DBRequest)
            .where(DBRequest.status == RequestStatus.PENDING.value)
            .order_by(DBRequest.created_at.desc())
        )
        requests = result.scalars().all()
    
    if not requests:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="menu_requests_management")]
        ])
        await callback.message.edit_text("📋 Нет заявок, ожидающих утверждения.", reply_markup=keyboard)
        await callback.answer()
        return
    
    # Показываем первую заявку
    req = requests[0]
    
    # Определяем эмодзи и текст типа пропуска
    pass_type_emoji = "🚶" if req.pass_type == "pedestrian" else "🚗"
    pass_type_text = "Пешеход" if req.pass_type == "pedestrian" else "Автомобиль"
    
    text = (
        f"📋 <b>Заявка #{req.id}</b> (1 из {len(requests)})\n\n"
        f"👤 {req.name}\n"
        f"{pass_type_emoji} Тип: {pass_type_text}\n"
        f"📝 Цель: {req.purpose}\n"
    )
    
    # Показываем номер авто для машин
    if req.car_number:
        text += f"🚗 Номер: {req.car_number}\n"
    
    text += (
        f"📅 Визит: {req.datetime}\n"
        f"🕐 Создана: {req.created_at.strftime('%d.%m.%Y %H:%M')}\n"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Утвердить", callback_data=f"approve_{req.id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_{req.id}")
        ],
        [
            InlineKeyboardButton(text="📷 Посмотреть фото", callback_data=f"viewphoto_{req.id}")
        ],
        [
            InlineKeyboardButton(text="◀️ Назад", callback_data="menu_requests_management")
        ]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("approve_"))
async def callback_approve(callback: types.CallbackQuery):
    """Утверждение заявки"""
    req_id = int(callback.data.split("_")[1])
    telegram_id = callback.from_user.id
    
    async with get_session() as session:
        # Проверяем права
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        
        if not user or user.role not in [Role.GUARD.value, Role.ADMIN.value]:
            await callback.answer("❌ Недостаточно прав", show_alert=True)
            return
        
        # Получаем заявку
        req = await session.get(DBRequest, req_id)
        if not req:
            await callback.answer("❌ Заявка не найдена", show_alert=True)
            return
        
        if req.status == "approved":
            await callback.answer("✅ Заявка уже утверждена", show_alert=True)
            return
        
        # Утверждаем заявку и устанавливаем срок действия (2 часа)
        req.status = "approved"
        req.processed_by_id = user.id
        req.processed_at = datetime.datetime.utcnow()
        req.valid_until = datetime.datetime.utcnow() + datetime.timedelta(hours=2)
        await session.commit()
        
        # Сохраняем valid_until для использования вне сессии
        valid_until = req.valid_until
    
    await callback.answer("✅ Заявка утверждена!")
    
    # Обновляем сообщение администратору/охраннику (БЕЗ QR-кода)
    pass_type_emoji = "🚶" if req.pass_type == "pedestrian" else "🚗"
    pass_type_text = "Пешеход" if req.pass_type == "pedestrian" else "Автомобиль"
    
    text = (
        f"✅ <b>Заявка #{req.id} УТВЕРЖДЕНА</b>\n\n"
        f"👤 {req.name}\n"
        f"{pass_type_emoji} Тип: {pass_type_text}\n"
        f"📝 Цель: {req.purpose}\n"
    )
    
    if req.car_number:
        text += f"🚗 Номер: {req.car_number}\n"
    
    text += (
        f"📅 Визит: {req.datetime}\n"
        f"⏰ Срок действия: {valid_until.strftime('%d.%m.%Y %H:%M')} (2 часа)\n"
        f"👮 Утвердил: {user.name}\n\n"
        f"📨 Уведомление и QR-код отправлены заявителю."
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 К заявкам", callback_data="menu_pending")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ])
    
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    
    # 🔔 УВЕДОМЛЕНИЕ ЗАЯВИТЕЛЮ (с QR-кодом)
    async with get_session() as session:
        try:
            # Получаем заявителя
            applicant = await session.get(User, req.applicant_id)
            
            if applicant and applicant.telegram_id:
                # Формируем сообщение для заявителя
                applicant_text = (
                    f"✅ <b>Ваша заявка #{req.id} УТВЕРЖДЕНА!</b>\n\n"
                    f"📋 <b>Детали пропуска:</b>\n"
                    f"{pass_type_emoji} Тип: {pass_type_text}\n"
                    f"📝 Цель: {req.purpose}\n"
                )
                
                if req.car_number:
                    applicant_text += f"🚗 Номер авто: {req.car_number}\n"
                
                applicant_text += (
                    f"📅 Дата и время визита: {req.datetime}\n"
                    f"⏰ <b>Срок действия до:</b> {valid_until.strftime('%d.%m.%Y %H:%M')} (2 часа)\n\n"
                    f"👮 Утвердил: {user.name}\n\n"
                    f"💡 <b>Важно:</b> Сохраните QR-код ниже для предъявления на КПП.\n"
                    f"⚠️ За 30 минут до истечения вы получите уведомление."
                )
                
                # Отправляем уведомление заявителю
                await callback.bot.send_message(
                    chat_id=applicant.telegram_id,
                    text=applicant_text,
                    parse_mode="HTML"
                )
                
                # Генерируем и отправляем QR-код заявителю
                # Формат: Telegram deep link для открытия бота с информацией о пропуске
                qr_data = f"https://t.me/SK_GuardBot?start=pass_{req.id}_{req.qr_code}"
                logger.info(f"Generating QR code with data: {qr_data}")
                logger.info(f"QR UUID length: {len(req.qr_code) if req.qr_code else 0}")
                
                qr = generate_qr_bytes(qr_data)
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                    tmp.write(qr.read())
                    tmp_path = tmp.name
                
                await callback.bot.send_photo(
                    chat_id=applicant.telegram_id,
                    photo=FSInputFile(tmp_path),
                    caption=(
                        f"🎫 <b>Пропуск #{req.id}</b>\n\n"
                        f"Действителен до: {valid_until.strftime('%d.%m.%Y %H:%M')}\n"
                        f"Предъявите этот QR-код на КПП"
                    ),
                    parse_mode="HTML"
                )
                
                os.remove(tmp_path)
                
                logger.info(f"Notification and QR sent to applicant {applicant.telegram_id} for request #{req.id}")
        
        except Exception as e:
            logger.error(f"Failed to send notification to applicant: {e}")
            # Не прерываем процесс, даже если уведомление не отправилось


@router.callback_query(F.data.startswith("reject_"))
async def callback_reject(callback: types.CallbackQuery):
    """Отклонение заявки"""
    req_id = int(callback.data.split("_")[1])
    telegram_id = callback.from_user.id
    
    async with get_session() as session:
        # Проверяем права
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        
        if not user or user.role not in [Role.GUARD.value, Role.ADMIN.value]:
            await callback.answer("❌ Недостаточно прав", show_alert=True)
            return
        
        # Получаем заявку
        req = await session.get(DBRequest, req_id)
        if not req:
            await callback.answer("❌ Заявка не найдена", show_alert=True)
            return
        
        # Отклоняем заявку
        req.status = "rejected"
        req.processed_by_id = user.id
        req.processed_at = datetime.datetime.utcnow()
        req.rejection_reason = "Отклонено охранником"  # TODO: можно добавить ввод причины
        await session.commit()
        
        # Получаем заявителя для уведомления
        applicant = await session.get(User, req.applicant_id)
    
    await callback.answer("❌ Заявка отклонена")
    
    # Обновляем сообщение охраннику
    pass_type_emoji = "🚶" if req.pass_type == "pedestrian" else "🚗"
    pass_type_text = "Пешеход" if req.pass_type == "pedestrian" else "Автомобиль"
    
    text = (
        f"❌ <b>Заявка #{req.id} ОТКЛОНЕНА</b>\n\n"
        f"👤 {req.name}\n"
        f"{pass_type_emoji} Тип: {pass_type_text}\n"
        f"📝 Цель: {req.purpose}\n"
    )
    
    if req.car_number:
        text += f"🚗 Номер: {req.car_number}\n"
    
    text += (
        f"📅 Визит: {req.datetime}\n"
        f"👮 Отклонил: {user.name}\n"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 К заявкам", callback_data="menu_pending")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ])
    
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    
    # 🔔 УВЕДОМЛЕНИЕ ЗАЯВИТЕЛЮ ОБ ОТКЛОНЕНИИ
    try:
        if applicant and applicant.telegram_id:
            # Формируем сообщение для заявителя
            rejection_text = (
                f"❌ <b>Ваша заявка #{req.id} отклонена</b>\n\n"
                f"📋 <b>Детали заявки:</b>\n"
                f"{pass_type_emoji} Тип: {pass_type_text}\n"
                f"📝 Цель: {req.purpose}\n"
            )
            
            if req.car_number:
                rejection_text += f"🚗 Номер авто: {req.car_number}\n"
            
            rejection_text += (
                f"📅 Дата и время: {req.datetime}\n\n"
                f"📝 <b>Причина отклонения:</b>\n{req.rejection_reason}\n\n"
                f"👮 Обработал: {user.name}\n\n"
                f"💡 Вы можете подать новую заявку через /start"
            )
            
            # Отправляем уведомление
            await callback.bot.send_message(
                chat_id=applicant.telegram_id,
                text=rejection_text,
                parse_mode="HTML"
            )
            
            logger.info(f"Rejection notification sent to applicant {applicant.telegram_id} for request #{req.id}")
    
    except Exception as e:
        logger.error(f"Failed to send rejection notification: {e}")
        # Не прерываем процесс


@router.callback_query(F.data.startswith("viewphoto_"))
async def callback_view_photo(callback: types.CallbackQuery):
    """Просмотр фото документа из заявки"""
    req_id = int(callback.data.split("_")[1])
    
    async with get_session() as session:
        req = await session.get(DBRequest, req_id)
        if not req or not req.photo:
            await callback.answer("❌ Фото не найдено", show_alert=True)
            return
    
    # Отправляем фото
    if os.path.exists(req.photo):
        await callback.message.answer_photo(
            photo=FSInputFile(req.photo),
            caption=f"📷 Фото документа для заявки #{req.id}\n👤 {req.name}"
        )
        await callback.answer("✅")
    else:
        await callback.answer("❌ Файл фото не найден на сервере", show_alert=True)


async def show_active_passes(callback: types.CallbackQuery):
    """Показать список активных пропусков"""
    from utils.user_helpers import check_user_access
    
    telegram_id = callback.from_user.id
    
    # Проверяем доступ
    has_access, user = await check_user_access(telegram_id, [Role.GUARD.value, Role.ADMIN.value])
    
    if not has_access:
        await callback.answer("❌ Недостаточно прав", show_alert=True)
        return
    
    # Получаем активные заявки (approved и valid_until > now)
    now = datetime.datetime.utcnow()
    async with get_session() as session:
        result = await session.execute(
            select(DBRequest)
            .where(
        DBRequest.status == RequestStatus.APPROVED.value,
                DBRequest.valid_until > now
            )
            .order_by(DBRequest.valid_until.asc())
        )
        requests = result.scalars().all()
    
    if not requests:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="menu_requests_management")]
        ])
        await callback.message.edit_text(
            "✅ <b>Активные пропуска</b>\n\n"
            "Нет активных пропусков.",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await callback.answer()
        return
    
    text = f"✅ <b>Активные пропуска ({len(requests)}):</b>\n\n"
    
    for req in requests:
        pass_type_emoji = "🚶" if req.pass_type == "pedestrian" else "🚗"
        pass_type_text = "Пешеход" if req.pass_type == "pedestrian" else "Автомобиль"
        
        # Вычисляем оставшееся время
        time_left = req.valid_until - now
        hours_left = int(time_left.total_seconds() / 3600)
        minutes_left = int((time_left.total_seconds() % 3600) / 60)
        
        text += (
            f"🆔 <b>Пропуск #{req.id}</b>\n"
            f"👤 {req.name}\n"
            f"{pass_type_emoji} {pass_type_text}\n"
        )
        
        if req.car_number:
            text += f"🚗 Номер: {req.car_number}\n"
        
        text += (
            f"📝 Цель: {req.purpose}\n"
            f"⏰ Действителен до: {req.valid_until.strftime('%d.%m.%Y %H:%M')}\n"
            f"⏳ Осталось: {hours_left}ч {minutes_left}м\n"
            f"📅 Визит: {req.datetime}\n\n"
        )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="menu_active")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="menu_requests_management")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


async def show_archive(callback: types.CallbackQuery, page: int = 0):
    """Показать архив заявок (отклонённые, истёкшие, использованные) с пагинацией по 10"""
    from utils.user_helpers import check_user_access
    
    telegram_id = callback.from_user.id
    
    # Проверяем доступ
    has_access, user = await check_user_access(telegram_id, [Role.GUARD.value, Role.ADMIN.value])
    
    if not has_access:
        await callback.answer("❌ Недостаточно прав", show_alert=True)
        return
    
    # Пагинация
    ITEMS_PER_PAGE = 10
    offset = page * ITEMS_PER_PAGE
    
    # Получаем архивные заявки
    async with get_session() as session:
        # Общее количество записей
        count_result = await session.execute(
            select(func.count(DBRequest.id))
            .where(
                DBRequest.status.in_([
                    RequestStatus.REJECTED.value, 
                    RequestStatus.EXPIRED.value, 
                    RequestStatus.USED.value
                ])
            )
        )
        total_count = count_result.scalar()
        
        # Получаем записи для текущей страницы
        result = await session.execute(
            select(DBRequest)
            .where(
                DBRequest.status.in_([
                    RequestStatus.REJECTED.value, 
                    RequestStatus.EXPIRED.value, 
                    RequestStatus.USED.value
                ])
            )
            .order_by(DBRequest.processed_at.desc())
            .limit(ITEMS_PER_PAGE)
            .offset(offset)
        )
        requests = result.scalars().all()
    
    if total_count == 0:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="menu_requests_management")]
        ])
        await callback.message.edit_text(
            "📦 <b>Архив заявок</b>\n\n"
            "Архив пуст.",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await callback.answer()
        return
    
    # Расчёт страниц
    total_pages = (total_count + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    current_page = page + 1
    
    text = (
        f"📦 <b>Архив заявок</b>\n"
        f"Страница {current_page} из {total_pages} (всего записей: {total_count})\n\n"
    )
    
    for req in requests:
        status_emoji = {
            "rejected": "❌",
            "expired": "⌛",
            "used": "✔️"
        }
        
        status_text = {
            "rejected": "Отклонён",
            "expired": "Истёк",
            "used": "Использован"
        }
        
        pass_type_emoji = "🚶" if req.pass_type == "pedestrian" else "🚗"
        
        text += (
            f"{status_emoji.get(req.status, '❓')} <b>#{req.id}</b> - {status_text.get(req.status, 'Неизвестно')}\n"
            f"👤 {req.name} | {pass_type_emoji}\n"
        )
        
        if req.processed_at:
            text += f"📅 {req.processed_at.strftime('%d.%m %H:%M')}\n"
        
        if req.status == "rejected" and req.rejection_reason:
            text += f"💬 {req.rejection_reason[:50]}...\n"
        
        text += "\n"
    
    # Кнопки навигации
    navigation_buttons = []
    
    if page > 0:
        navigation_buttons.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data=f"archive_page_{page - 1}")
        )
    
    if current_page < total_pages:
        navigation_buttons.append(
            InlineKeyboardButton(text="Вперёд ➡️", callback_data=f"archive_page_{page + 1}")
        )
    
    keyboard_rows = []
    
    if navigation_buttons:
        keyboard_rows.append(navigation_buttons)
    
    keyboard_rows.extend([
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="menu_archive")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="menu_requests_management")]
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_rows)
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("archive_page_"))
async def archive_pagination(callback: types.CallbackQuery):
    """Обработка пагинации архива"""
    page = int(callback.data.split("_")[-1])
    await show_archive(callback, page=page)
