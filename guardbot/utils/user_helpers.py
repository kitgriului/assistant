"""User management utilities.

Provides helper functions for common user operations like fetching user data,
checking access permissions, and managing user state in the bot.

This module centralizes user-related logic to avoid duplication across handlers.
"""
from typing import Optional, Tuple, Union, List
import logging

from sqlalchemy import select
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database.session import get_session
from database.models import User
from utils.constants import Role


logger = logging.getLogger(__name__)


async def get_user_by_telegram_id(telegram_id: int) -> Optional[User]:
    """Fetch user by Telegram ID.
    
    Args:
        telegram_id: Telegram user identifier
        
    Returns:
        User object if found, None otherwise
        
    Example:
        user = await get_user_by_telegram_id(message.from_user.id)
        if user and user.is_admin:
            # Admin-only logic
    """
    async with get_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()


async def get_or_create_user(
    telegram_id: int, 
    name: Optional[str] = None,
    phone_number: Optional[str] = None,
) -> User:
    """Get existing user or create new guest user.
    
    Args:
        telegram_id: Telegram user identifier
        name: User's full name (optional)
        phone_number: User's phone number (optional)
        
    Returns:
        User object (existing or newly created)
        
    Example:
        user = await get_or_create_user(
            message.from_user.id,
            message.from_user.full_name,
        )
    """
    async with get_session() as session:
        # Try to find existing user
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        
        if user:
            return user
        
        # Create new guest user
        user = User(
            telegram_id=telegram_id,
            name=name or f"User_{telegram_id}",
            phone_number=phone_number,
            role=Role.GUEST.value,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        
        logger.info(f"Created new user: telegram_id={telegram_id}, name={user.name}")
        return user


async def get_user_info(telegram_id: int) -> Tuple[str, str]:
    """Get user role and name.
    
    Args:
        telegram_id: Telegram user identifier
        
    Returns:
        Tuple of (role, name). Returns ("guest", "Гость") for unknown users.
        
    Example:
        role, name = await get_user_info(message.from_user.id)
        if role == Role.ADMIN.value:
            # Show admin menu
    """
    user = await get_user_by_telegram_id(telegram_id)
    
    if user:
        return user.role, user.name or "Unknown"
    else:
        return Role.GUEST.value, "Гость"


async def check_user_access(
    telegram_id: int, 
    required_roles: List[str]
) -> Tuple[bool, Optional[User]]:
    """Check if user has required role access.
    
    Validates user exists, is not blocked, and has one of the required roles.
    
    Args:
        telegram_id: Telegram user identifier
        required_roles: List of acceptable role values (e.g., ["admin", "guard"])
        
    Returns:
        Tuple of (has_access, user_object)
        - has_access: True if user can proceed
        - user_object: User instance or None if not found
        
    Example:
        has_access, user = await check_user_access(
            message.from_user.id,
            [Role.ADMIN.value, Role.GUARD.value]
        )
        if not has_access:
            await message.answer("Access denied")
            return
    """
    user = await get_user_by_telegram_id(telegram_id)
    
    if not user:
        logger.debug(f"Access denied: user not found (telegram_id={telegram_id})")
        return False, None
    
    if user.is_blocked:
        logger.debug(f"Access denied: user is blocked (user_id={user.id})")
        return False, user
    
    has_access = user.role in required_roles
    
    if not has_access:
        logger.debug(
            f"Access denied: insufficient role (user_id={user.id}, "
            f"role={user.role}, required={required_roles})"
        )
    
    return has_access, user


async def update_user_activity(telegram_id: int) -> None:
    """Update user's last activity timestamp.
    
    Args:
        telegram_id: Telegram user identifier
        
    Example:
        await update_user_activity(message.from_user.id)
    """
    import datetime
    
    async with get_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        
        if user:
            user.last_activity = datetime.datetime.utcnow()
            await session.commit()
            logger.debug(f"Updated activity for user {user.id}")


async def return_to_menu(
    message_or_callback: Union[Message, CallbackQuery], 
    state: FSMContext
) -> None:
    """Clear FSM state and return to main menu.
    
    Handles both Message and CallbackQuery objects, clears state,
    and displays the main menu for the user.
    
    Args:
        message_or_callback: Message or CallbackQuery object
        state: FSM Context to clear
        
    Example:
        await return_to_menu(callback, state)
    """
    # Import here to avoid circular dependency
    from handlers.menu import show_main_menu
    
    # Clear FSM state
    await state.clear()
    
    # Extract telegram_id and display object based on type
    if isinstance(message_or_callback, CallbackQuery):
        telegram_id = message_or_callback.from_user.id
        display_object = message_or_callback.message
    else:  # Message
        telegram_id = message_or_callback.from_user.id
        display_object = message_or_callback
    
    # Get user information
    role, name = await get_user_info(telegram_id)
    
    # Show main menu
    await show_main_menu(display_object, role, name)
    
    logger.debug(f"User {telegram_id} returned to main menu")


async def is_user_blocked(telegram_id: int) -> bool:
    """Check if user is blocked.
    
    Args:
        telegram_id: Telegram user identifier
        
    Returns:
        True if user is blocked, False otherwise (including non-existent users)
        
    Example:
        if await is_user_blocked(message.from_user.id):
            await message.answer("You are blocked")
            return
    """
    user = await get_user_by_telegram_id(telegram_id)
    return user.is_blocked if user else False


async def set_user_role(telegram_id: int, new_role: str) -> bool:
    """Update user role.
    
    Args:
        telegram_id: Telegram user identifier
        new_role: New role value (guest/guard/admin)
        
    Returns:
        True if role was updated, False if user not found
        
    Example:
        success = await set_user_role(user_telegram_id, Role.GUARD.value)
        if success:
            await message.answer("Role updated successfully")
    """
    async with get_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            logger.warning(f"Cannot set role: user not found (telegram_id={telegram_id})")
            return False
        
        old_role = user.role
        user.role = new_role
        await session.commit()
        
        logger.info(
            f"User role changed: user_id={user.id}, "
            f"{old_role} -> {new_role}"
        )
        return True
    return has_access, user


async def is_user_blocked(telegram_id: int) -> bool:
    """
    Проверить, заблокирован ли пользователь
    
    Args:
        telegram_id: Telegram ID пользователя
        
    Returns:
        True если пользователь заблокирован или не найден
    """
    user = await get_user_by_telegram_id(telegram_id)
    
    if not user:
        return True  # Незарегистрированные считаем заблокированными
    
    return user.is_blocked


async def get_user_role(telegram_id: int) -> str:
    """
    Получить роль пользователя
    
    Args:
        telegram_id: Telegram ID пользователя
        
    Returns:
        Роль пользователя или "guest" если не найден
    """
    user = await get_user_by_telegram_id(telegram_id)
    return user.role if user else Role.GUEST.value
