from aiogram.types import FSInputFile
from utils.constants import PassType
"""Handlers for the Applicant (guest) role: submit request and receive QR code."""
from aiogram import Dispatcher, types, F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery
import io
from aiogram.fsm.context import FSMContext
import os
import uuid
import datetime
from sqlalchemy import select

from states.applicant import ApplicantStates
from utils.qr import generate_qr_bytes
from utils.media import save_file
from utils.calendar_kb import generate_calendar, generate_time_keyboard, format_datetime
from database.models import Request as DBRequest, User
from database.session import get_session
import logging

logger = logging.getLogger(__name__)

router = Router()


def register_applicant_handlers(dp: Dispatcher):
    dp.include_router(router)


@router.message(Command("help"))
async def cmd_help(message: types.Message):
    """Справка для гостей."""
    await message.reply(
        "📖 <b>Справка GuardBot</b>\n\n"
        "<b>Доступные команды:</b>\n"
        "/request - подать заявку на пропуск\n"
        "/help - показать эту справку\n\n"
        "<b>Процесс подачи заявки:</b>\n"
        "1. Введите /request\n"
        "2. Укажите цель визита\n"
        "3. Выберите дату в календаре\n"
        "4. Выберите время\n"
        "5. Отправьте фото документа\n"
        "6. Получите QR-код заявки",
        parse_mode="HTML"
    )


@router.message(Command("request"))
async def start_request(message: types.Message, state: FSMContext):
    """Начало процесса создания заявки - выбор типа пропуска"""
    telegram_id = message.from_user.id

    # Проверка регистрации
    async with get_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            await message.reply("❌ Вы не зарегистрированы. Используйте /start для регистрации.")
            return
        
        if user.is_blocked:
            await message.reply("🚫 Ваш доступ заблокирован. Обратитесь к администратору.")
            return

    # Показываем выбор типа пропуска
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🚶 Пешеход", callback_data="passtype_pedestrian"),
            InlineKeyboardButton(text="🚗 Автомобиль", callback_data="passtype_vehicle")
        ],
        [
            InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_request")
        ]
    ])
    
    await state.set_state(ApplicantStates.pass_type)
    await message.answer(
        "📝 <b>Создание заявки на пропуск</b>\n\n"
        "Выберите тип пропуска:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.message(ApplicantStates.purpose)
async def request_purpose(message: types.Message, state: FSMContext):
    """Обработка ввода пользовательской цели визита (если выбрано 'Другое')"""
    # Проверяем на отмену
    if message.text and message.text.lower() in ['/cancel', 'отмена']:
        from utils.user_helpers import return_to_menu
        await return_to_menu(message, state)
        return
    
    # Проверяем, что это текстовое сообщение
    if not message.text:
        await message.reply("❌ Пожалуйста, введите текстовое описание цели визита или используйте /cancel для отмены.")
        return
    
    purpose = message.text.strip()
    if not purpose or len(purpose) < 5:
        await message.reply("❌ Пожалуйста, введите более подробную цель визита (минимум 5 символов).")
        return
    
    await state.update_data(purpose=purpose)
    
    # Показываем календарь для выбора даты
    today = datetime.date.today()
    calendar_kb = generate_calendar(today.year, today.month)
    
    await message.answer(
        f"✅ Цель визита: {purpose}\n\n"
        f"📅 Выберите дату визита:",
        reply_markup=calendar_kb
    )


@router.callback_query(F.data.startswith("passtype_"))
async def process_pass_type(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора типа пропуска"""
    pass_type = callback.data.split("_")[1]  # pedestrian или vehicle
    await state.update_data(pass_type=pass_type)
    
    # Показываем цели в зависимости от типа
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    if pass_type == "pedestrian":
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="� Деловая встреча", callback_data="purpose_meeting")],
            [InlineKeyboardButton(text="📦 Получение груза", callback_data="purpose_pickup")],
            [InlineKeyboardButton(text="🚚 Доставка", callback_data="purpose_delivery")],
            [InlineKeyboardButton(text="✏️ Другое (указать)", callback_data="purpose_custom")],
            [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_request")]
        ])
        emoji = "🚶"
        type_text = "Пешеход"
    else:  # vehicle
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🚛 Погрузка/разгрузка", callback_data="purpose_loading")],
            [InlineKeyboardButton(text="🚚 Доставка", callback_data="purpose_delivery")],
            [InlineKeyboardButton(text="🚗 Служебная поездка", callback_data="purpose_business")],
            [InlineKeyboardButton(text="✏️ Другое (указать)", callback_data="purpose_custom")],
            [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_request")]
        ])
        emoji = "🚗"
        type_text = "Автомобиль"
    
    await state.set_state(ApplicantStates.purpose)
    await callback.message.edit_text(
        f"✅ Тип пропуска: {emoji} {type_text}\n\n"
        f"📋 Выберите цель визита:",
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data.startswith("purpose_"))
async def process_purpose(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора цели визита"""
    purpose_code = callback.data.split("_")[1]
    
    # Маппинг кодов на текст
    purpose_map = {
        "meeting": "Деловая встреча",
        "pickup": "Получение груза",
        "delivery": "Доставка",
        "loading": "Погрузка/разгрузка",
        "business": "Служебная поездка"
    }
    
    if purpose_code == "custom":
        # Просим ввести свою цель
        await state.set_state(ApplicantStates.custom_purpose)
        await callback.message.edit_text(
            "✏️ Введите цель визита:"
        )
        await callback.answer()
        return
    
    purpose = purpose_map.get(purpose_code, "Другое")
    await state.update_data(purpose=purpose)
    
    # Показываем календарь для выбора даты
    today = datetime.date.today()
    calendar_kb = generate_calendar(today.year, today.month)
    
    await callback.message.edit_text(
        f"✅ Цель визита: {purpose}\n\n"
        f"📅 Выберите дату визита:",
        reply_markup=calendar_kb
    )
    await callback.answer()


@router.message(ApplicantStates.custom_purpose)
async def process_custom_purpose(message: types.Message, state: FSMContext):
    """Обработка ввода пользовательской цели"""
    # Проверяем на отмену
    if message.text and message.text.lower() in ['/cancel', 'отмена']:
        from utils.user_helpers import return_to_menu
        await return_to_menu(message, state)
        return
    
    purpose = message.text.strip()
    if not purpose or len(purpose) < 5:
        await message.reply("❌ Пожалуйста, введите более подробную цель визита (минимум 5 символов).")
        return
    
    await state.update_data(purpose=purpose)
    
    # Показываем календарь для выбора даты
    today = datetime.date.today()
    calendar_kb = generate_calendar(today.year, today.month)
    
    await message.answer(
        f"✅ Цель визита: {purpose}\n\n"
        f"📅 Выберите дату визита:",
        reply_markup=calendar_kb
    )


@router.callback_query(F.data.startswith("cal_"))
async def process_calendar(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора даты в календаре"""
    data = callback.data.split("_")
    
    if data[1] == "ignore":
        await callback.answer()
        return
    
    if data[1] == "prev":
        # Предыдущий месяц
        year, month = int(data[2]), int(data[3])
        month -= 1
        if month < 1:
            month = 12
            year -= 1
        
        calendar_kb = generate_calendar(year, month)
        await callback.message.edit_reply_markup(reply_markup=calendar_kb)
        await callback.answer()
        return
    
    if data[1] == "next":
        # Следующий месяц
        year, month = int(data[2]), int(data[3])
        month += 1
        if month > 12:
            month = 1
            year += 1
        
        calendar_kb = generate_calendar(year, month)
        await callback.message.edit_reply_markup(reply_markup=calendar_kb)
        await callback.answer()
        return
    
    if data[1] == "day":
        # Выбрана дата
        year, month, day = int(data[2]), int(data[3]), int(data[4])
        await state.update_data(year=year, month=month, day=day)
        
        # Показываем выбор времени
        time_kb = generate_time_keyboard()
        await callback.message.edit_text(
            f"📅 Выбрана дата: {day:02d}.{month:02d}.{year}\n\n"
            f"🕐 Выберите время визита:",
            reply_markup=time_kb
        )
        await callback.answer()


@router.callback_query(F.data == "cancel_request")
async def cancel_request(callback: CallbackQuery, state: FSMContext):
    """Отмена создания заявки"""
    from utils.user_helpers import return_to_menu
    
    await callback.message.edit_text("❌ Создание заявки отменено.")
    await return_to_menu(callback, state)
    await callback.answer()


@router.callback_query(F.data.startswith("time_"))
async def process_time(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора времени"""
    data = callback.data.split("_")
    hour, minute = int(data[1]), int(data[2])
    
    # Получаем сохранённую дату
    state_data = await state.get_data()
    year = state_data.get('year')
    month = state_data.get('month')
    day = state_data.get('day')
    
    # Форматируем дату и время
    dt_string = format_datetime(year, month, day, hour, minute)
    await state.update_data(datetime=dt_string)
    
    # Переходим к следующему шагу - фото или номер машины
    state_data = await state.get_data()
    pass_type = state_data.get('pass_type', PassType.PEDESTRIAN.value)
    
    if pass_type == "vehicle":
        # Для автомобиля сначала спрашиваем номер
        await state.set_state(ApplicantStates.car_number)
        await callback.message.edit_text(
            f"✅ Дата и время: {day:02d}.{month:02d}.{year} {hour:02d}:{minute:02d}\n\n"
            f"🚗 Введите номер автомобиля (например: А123БВ777):"
        )
    else:
        # Для пешехода - сразу фото документа
        await state.set_state(ApplicantStates.photo)
        await callback.message.edit_text(
            f"✅ Дата и время: {day:02d}.{month:02d}.{year} {hour:02d}:{minute:02d}\n\n"
            f"📷 Теперь отправьте фото вашего документа (паспорт, ID):"
        )
    await callback.answer()


@router.message(ApplicantStates.car_number)
async def process_car_number(message: types.Message, state: FSMContext):
    """Обработка ввода номера машины"""
    # Проверяем на отмену
    if message.text and message.text.lower() in ['/cancel', 'отмена']:
        from utils.user_helpers import return_to_menu
        await return_to_menu(message, state)
        return
    
    car_number = message.text.strip().upper()
    if not car_number or len(car_number) < 5:
        await message.reply("❌ Пожалуйста, введите корректный номер автомобиля.")
        return
    
    await state.update_data(car_number=car_number)
    await state.set_state(ApplicantStates.photo)
    await message.answer(
        f"✅ Номер автомобиля: {car_number}\n\n"
        f"📷 Теперь отправьте фото тех. паспорта транспортного средства:"
    )


@router.message(ApplicantStates.photo)
async def request_photo(message: types.Message, state: FSMContext):
    # Проверяем на отмену
    if message.text and message.text.lower() in ['/cancel', 'отмена']:
        from utils.user_helpers import return_to_menu
        await return_to_menu(message, state)
        return
    
    if not message.photo:
        await message.reply("❌ Пожалуйста, отправьте фото документа или используйте /cancel для отмены.")
        return
    
    photo = message.photo[-1]
    file_path = await save_file(message.bot, photo, prefix="applicant_")

    data = await state.get_data()
    purpose = data.get("purpose")
    dt = data.get("datetime")
    pass_type = data.get("pass_type", "pedestrian")
    car_number = data.get("car_number")
    
    if not all([purpose, dt]):
        await message.reply("❌ Ошибка: отсутствуют обязательные данные. Начните заново: /request")
        await state.clear()
        return
    
    telegram_id = message.from_user.id
    
    # Получаем пользователя
    async with get_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            await message.reply("❌ Пользователь не найден. Используйте /start")
            await state.clear()
            return
        
        # Генерируем уникальный код для QR
        qr_code = str(uuid.uuid4())
        
        req = DBRequest(
            applicant_id=user.id,
            name=user.name,  # Берём ФИО из профиля пользователя
            pass_type=pass_type,
            purpose=purpose,
            datetime=dt,
            photo=file_path,
            car_number=car_number,  # Может быть None для пешеходов
            status="pending",
            qr_code=qr_code,
            created_at=datetime.datetime.utcnow()
        )
        session.add(req)
        await session.commit()
        await session.refresh(req)
        request_id = req.id

    # Генерация QR-кода
    import tempfile
    qr = generate_qr_bytes(f"request:{request_id}:{qr_code}")
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp.write(qr.read())
        tmp_path = tmp.name
    
    # Формируем текст в зависимости от типа пропуска
    pass_type_emoji = "🚶" if pass_type == "pedestrian" else "🚗"
    pass_type_text = "Пешеход" if pass_type == "pedestrian" else "Автомобиль"
    
    caption_text = (
        f"✅ <b>Заявка создана!</b>\n\n"
        f"ID заявки: <code>{request_id}</code>\n"
        f"Тип пропуска: {pass_type_emoji} {pass_type_text}\n"
        f"Цель: {purpose}\n"
    )
    
    if car_number:
        caption_text += f"Номер авто: {car_number}\n"
    
    caption_text += f"\nСтатус: ⏳ Ожидает утверждения\n\nСохраните этот QR-код для предъявления."
    
    await message.answer_photo(
        photo=FSInputFile(tmp_path),
        caption=caption_text,
        parse_mode="HTML"
    )
    os.remove(tmp_path)
    await state.clear()
