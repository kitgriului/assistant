"""
Авторизация через номер телефона
"""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select
from database.session import get_session
from database.models import User, Request as DBRequest
from utils.constants import RequestStatus
import datetime
import logging

logger = logging.getLogger(__name__)

router = Router()


class RegistrationStates(StatesGroup):
    waiting_for_name = State()


async def show_pass_info(message: Message, deep_link_param: str):
    """
    Показывает информацию о пропуске по deep link параметру.
    Формат: pass_{request_id}_{uuid}
    """
    try:
        # Парсим параметр: pass_123_uuid-string
        parts = deep_link_param.split("_", 2)  # ["pass", "123", "uuid-string"]
        
        if len(parts) < 3:
            await message.answer("❌ Неверный формат QR-кода.")
            return
        
        request_id = int(parts[1])
        uuid = parts[2]
        
        # Получаем заявку из базы
        async with get_session() as session:
            req = await session.get(DBRequest, request_id)
            
            if not req:
                await message.answer("❌ Пропуск не найден.")
                return
            
            # Проверяем UUID для безопасности
            if req.qr_code != uuid:
                await message.answer("❌ Недействительный QR-код.")
                logger.warning(f"Invalid UUID for request {request_id}: expected {req.qr_code}, got {uuid}")
                return
            
            # Получаем информацию о заявителе и обработавшем
            applicant = await session.get(User, req.applicant_id) if req.applicant_id else None
            processed_by = await session.get(User, req.processed_by_id) if req.processed_by_id else None
            
            # Определяем статус
            status_emoji = {
                "pending": "⏳",
                "approved": "✅",
                "rejected": "❌",
                "used": "✔️",
                "expired": "⌛"
            }
            
            status_text = {
                "pending": "Ожидает утверждения",
                "approved": "Утверждён",
                "rejected": "Отклонён",
                "used": "Использован",
                "expired": "Истёк"
            }
            
            # Проверяем актуальность
            is_expired = False
            if req.valid_until and req.status == RequestStatus.APPROVED.value:
                is_expired = datetime.datetime.utcnow() > req.valid_until
                if is_expired and req.status != RequestStatus.EXPIRED.value:
                    req.status = RequestStatus.EXPIRED.value
                    await session.commit()
            
            # Формируем сообщение
            pass_type_emoji = "🚶" if req.pass_type == "pedestrian" else "🚗"
            pass_type_text = "Пешеход" if req.pass_type == "pedestrian" else "Автомобиль"
            
            text = (
                f"🎫 <b>Пропуск #{req.id}</b>\n\n"
                f"{status_emoji.get(req.status, '❓')} <b>Статус:</b> {status_text.get(req.status, 'Неизвестно')}\n\n"
                f"👤 <b>Заявитель:</b> {req.name}\n"
                f"{pass_type_emoji} <b>Тип:</b> {pass_type_text}\n"
                f"📝 <b>Цель визита:</b> {req.purpose}\n"
            )
            
            if req.car_number:
                text += f"🚗 <b>Номер авто:</b> {req.car_number}\n"
            
            text += f"📅 <b>Запланированный визит:</b> {req.datetime}\n"
            
            # История обработки
            text += f"\n📋 <b>История:</b>\n"
            text += f"🕐 Создана: {req.created_at.strftime('%d.%m.%Y %H:%M')}\n"
            
            if req.processed_at:
                text += f"✅ Обработана: {req.processed_at.strftime('%d.%m.%Y %H:%M')}\n"
                if processed_by:
                    text += f"👮 Обработал: {processed_by.name}\n"
            
            if req.valid_until and req.status == "approved":
                if is_expired:
                    text += f"\n⌛ <b>Срок действия истёк:</b> {req.valid_until.strftime('%d.%m.%Y %H:%M')}\n"
                else:
                    time_left = req.valid_until - datetime.datetime.utcnow()
                    hours_left = int(time_left.total_seconds() / 3600)
                    minutes_left = int((time_left.total_seconds() % 3600) / 60)
                    
                    text += f"\n⏰ <b>Действителен до:</b> {req.valid_until.strftime('%d.%m.%Y %H:%M')}\n"
                    text += f"⏳ Осталось: {hours_left}ч {minutes_left}м\n"
            
            if req.rejection_reason:
                text += f"\n❌ <b>Причина отклонения:</b> {req.rejection_reason}\n"
            
            # Кнопки действий
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
            ])
            
            await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
            
    except ValueError:
        await message.answer("❌ Неверный формат QR-кода.")
    except Exception as e:
        logger.error(f"Error showing pass info: {e}")
        await message.answer("❌ Произошла ошибка при получении информации о пропуске.")



@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Начало работы - запрос номера телефона или показ информации о пропуске"""
    await state.clear()
    
    telegram_id = message.from_user.id
    
    # Проверяем наличие параметра deep link (например: /start pass_123_uuid)
    args = message.text.split(maxsplit=1)
    deep_link_param = args[1] if len(args) > 1 else None
    
    # Если есть параметр pass_X_UUID - показываем информацию о пропуске
    if deep_link_param and deep_link_param.startswith("pass_"):
        await show_pass_info(message, deep_link_param)
        return
    
    # Проверяем, есть ли пользователь в БД
    async with get_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        
        if user:
            # Проверяем блокировку
            if user.is_blocked:
                await message.answer(
                    "❌ Ваш доступ заблокирован.\n"
                    "Обратитесь к администратору."
                )
                return
            
            # Пользователь уже зарегистрирован - показываем главное меню
            from handlers.menu import show_main_menu
            await show_main_menu(message, user.role, user.name)
            return
    
    # Новый пользователь - запрашиваем номер телефона
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Отправить номер телефона", request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    
    await message.answer(
        "👋 Добро пожаловать в систему контроля доступа!\n\n"
        "Для авторизации или регистрации, пожалуйста, отправьте свой номер телефона.",
        reply_markup=keyboard
    )


@router.message(F.contact)
async def process_contact(message: Message, state: FSMContext):
    """Обработка полученного контакта"""
    contact = message.contact
    
    # Проверяем, что пользователь отправил свой номер
    if contact.user_id != message.from_user.id:
        await message.answer(
            "❌ Пожалуйста, отправьте свой собственный номер телефона.",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="📱 Отправить номер телефона", request_contact=True)]
                ],
                resize_keyboard=True
            )
        )
        return
    
    phone_number = contact.phone_number
    telegram_id = message.from_user.id
    
    # Проверяем, есть ли пользователь с таким номером
    async with get_session() as session:
        result = await session.execute(
            select(User).where(User.phone_number == phone_number)
        )
        user = result.scalar_one_or_none()
        
        if user:
            # Пользователь уже зарегистрирован по этому номеру
            if user.is_blocked:
                await message.answer(
                    "❌ Ваш доступ заблокирован.\n"
                    "Обратитесь к администратору.",
                    reply_markup=ReplyKeyboardRemove()
                )
                return
            
            # Обновляем telegram_id если изменился
            if user.telegram_id != telegram_id:
                user.telegram_id = telegram_id
                await session.commit()
            
            # Показываем главное меню
            from handlers.menu import show_main_menu
            await show_main_menu(message, user.role, user.name)
            return
            return
        
        # Новый пользователь - регистрация
        await state.set_state(RegistrationStates.waiting_for_name)
        await state.update_data(phone_number=phone_number, telegram_id=telegram_id)
        
        await message.answer(
            "📝 Регистрация нового пользователя\n\n"
            "Пожалуйста, введите ваши ФИО (полностью):",
            reply_markup=ReplyKeyboardRemove()
        )


@router.message(RegistrationStates.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    """Обработка ФИО и завершение регистрации"""
    name = message.text.strip()
    
    if len(name) < 5:
        await message.answer(
            "❌ Пожалуйста, введите ФИО полностью (минимум 5 символов).\n\n"
            "Например: Иванов Иван Иванович"
        )
        return
    
    data = await state.get_data()
    phone_number = data['phone_number']
    telegram_id = data['telegram_id']
    
    # Создаём нового пользователя
    async with get_session() as session:
        new_user = User(
            telegram_id=telegram_id,
            phone_number=phone_number,
            name=name,
            role="guest"  # По умолчанию все гости
        )
        session.add(new_user)
        await session.commit()
    
    await state.clear()
    
    # Показываем главное меню
    from handlers.menu import show_main_menu
    await show_main_menu(message, "guest", name)
