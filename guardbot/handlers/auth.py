"""Authentication handlers: login for guard/admin, registration for guest."""
from aiogram import Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
import datetime
import logging

from states.auth import AuthStates, GuestRegistrationStates
from database.session import get_session
from database.models import User as DBUser
from utils.auth import verify_password
from utils.roles import get_user_by_telegram_id
from utils.constants import Role

logger = logging.getLogger(__name__)


def register_auth_handlers(dp: Dispatcher):
    """Регистрация обработчиков аутентификации."""
    dp.message.register(cmd_start, Command(commands=["start"]))
    dp.message.register(process_login, AuthStates.waiting_login)
    dp.message.register(process_password, AuthStates.waiting_password)
    dp.message.register(process_guest_name, GuestRegistrationStates.waiting_name)


async def cmd_start(message: types.Message, state: FSMContext):
    """
    Главная команда /start - определяет роль пользователя и запускает процесс аутентификации.
    """
    telegram_id = message.from_user.id
    
    # Проверяем, есть ли пользователь в системе
    user = await get_user_by_telegram_id(telegram_id)
    
    if user:
        # Пользователь существует
        if user.role == Role.GUEST.value:
            # Гость - уже зарегистрирован
            if user.is_authenticated or user.name:
                await message.reply(
                    f"👋 Добро пожаловать, {user.name}!\n\n"
                    "Доступные команды:\n"
                    "/request - подать заявку на пропуск\n"
                    "/help - справка"
                )
            else:
                # Гость существует, но не завершил регистрацию
                await state.set_state(GuestRegistrationStates.waiting_name)
                await message.reply("👋 Добро пожаловать! Пожалуйста, введите ваше ФИО:")
        
        elif user.role in [Role.GUARD.value, Role.ADMIN.value]:
            # Охранник или администратор
            if user.is_authenticated:
                from handlers.menu import show_main_menu  # local import to avoid cycle
                await show_main_menu(message, user.role, user.name)
                return
                # Уже авторизован
                role_name = "Охранник" if user.role == "guard" else "Администратор"
                commands = get_commands_for_role(user.role)
                await message.reply(
                    f"👮 {role_name} {user.name}, вы авторизованы!\n\n"
                    f"Доступные команды:\n{commands}"
                )
            else:
                # Нужно пройти авторизацию
                await state.set_state(AuthStates.waiting_login)
                await message.reply(
                    "🔐 Для доступа необходимо авторизоваться.\n\n"
                    "Введите ваш логин:"
                )
    else:
        # Новый пользователь - создаём как гостя
        async with get_session() as session:
            new_user = DBUser(
                telegram_id=telegram_id,
                role=Role.GUEST.value,
                is_authenticated=False
            )
            session.add(new_user)
            await session.commit()
        
        await state.set_state(GuestRegistrationStates.waiting_name)
        await message.reply(
            "👋 Добро пожаловать в GuardBot!\n\n"
            "Пожалуйста, введите ваше ФИО:"
        )


async def process_login(message: types.Message, state: FSMContext):
    """Обработка ввода логина."""
    login = message.text.strip()
    
    # Проверяем, существует ли пользователь с таким логином
    async with get_session() as session:
        result = await session.execute(
            select(DBUser).where(DBUser.login == login)
        )
        user = result.scalar_one_or_none()
    
    if not user:
        await message.reply("❌ Пользователь с таким логином не найден. Попробуйте снова:")
        return
    
    # Проверяем, что telegram_id совпадает или не установлен
    if user.telegram_id != message.from_user.id:
        # Это может быть первый вход для предзаполненного пользователя
        if user.telegram_id == 0 or user.telegram_id is None:
            # Обновляем telegram_id
            async with get_session() as session:
                result = await session.execute(
                    select(DBUser).where(DBUser.login == login)
                )
                user = result.scalar_one()
                user.telegram_id = message.from_user.id
                await session.commit()
        else:
            await message.reply("❌ Этот логин уже привязан к другому аккаунту.")
            return
    
    # Сохраняем логин в state и запрашиваем пароль
    await state.update_data(login=login)
    await state.set_state(AuthStates.waiting_password)
    await message.reply("🔑 Введите пароль:")


async def process_password(message: types.Message, state: FSMContext):
    """Обработка ввода пароля."""
    password = message.text
    data = await state.get_data()
    login = data.get("login")
    
    # Удаляем сообщение с паролем для безопасности
    try:
        await message.delete()
    except Exception:
        pass
    
    # Проверяем пароль
    async with get_session() as session:
        result = await session.execute(
            select(DBUser).where(DBUser.login == login)
        )
        user = result.scalar_one_or_none()
    
    if not user or not verify_password(password, user.password_hash):
        await message.reply("❌ Неверный пароль. Попробуйте снова или /start для перезапуска.")
        return
    
    # Успешная авторизация
    async with get_session() as session:
        result = await session.execute(
            select(DBUser).where(DBUser.login == login)
        )
        user = result.scalar_one()
        user.is_authenticated = True
        user.last_login = datetime.datetime.utcnow()
        await session.commit()
    
    await state.clear()
    
    role_name = "Охранник" if user.role == "guard" else "Администратор"
    commands = get_commands_for_role(user.role)
    
    await message.answer(
        f"✅ Авторизация успешна!\n\n"
        f"👮 {role_name}: {user.name}\n\n"
        f"Доступные команды:\n{commands}"
    )


async def process_guest_name(message: types.Message, state: FSMContext):
    """Обработка ввода ФИО гостя."""
    name = message.text.strip()
    
    if len(name) < 3:
        await message.reply("❌ Пожалуйста, введите корректное ФИО (минимум 3 символа):")
        return
    
    # Обновляем данные пользователя
    telegram_id = message.from_user.id
    async with get_session() as session:
        result = await session.execute(
            select(DBUser).where(DBUser.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        
        if user:
            user.name = name
            user.is_authenticated = True
            await session.commit()
    
    await state.clear()
    
    await message.reply(
        f"✅ Регистрация завершена!\n\n"
        f"👤 {name}, добро пожаловать!\n\n"
        "Доступные команды:\n"
        "/request - подать заявку на пропуск\n"
        "/help - справка"
    )


def get_commands_for_role(role: str) -> str:
    """Возвращает список команд для роли."""
    if role == "guard":
        return (
            "/pending - список заявок на утверждение\n"
            "/approve <ID> - утвердить заявку\n"
            "/reject <ID> - отклонить заявку\n"
            "/start_patrol - начать обход\n"
            "/my_patrols - мои обходы\n"
            "/questions - вопросы от администратора"
        )
    elif role == "admin":
        return (
            "/users - список пользователей\n"
            "/requests [status] - список заявок\n"
            "/events - список событий обхода\n"
            "/event <ID> - детали события\n"
            "/ask <event_id> <вопрос> - задать вопрос охраннику\n"
            "/stats - статистика"
        )
    else:
        return (
            "/request - подать заявку на пропуск\n"
            "/help - справка"
        )
