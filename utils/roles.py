"""Role-based access control utilities and decorators.

These helpers centralize common role checks. Messages are intentionally
minimal and in English to avoid coupling behavior to text.
"""
from __future__ import annotations

from functools import wraps
from typing import List, Callable, Awaitable, Any

from aiogram import types
from sqlalchemy import select

from database.session import get_session
from database.models import User as DBUser
from utils.constants import Role


async def get_user_by_telegram_id(telegram_id: int) -> DBUser | None:
    """Fetch user by Telegram ID or return None if not found."""
    async with get_session() as session:
        result = await session.execute(
            select(DBUser).where(DBUser.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()


async def is_authenticated(telegram_id: int) -> bool:
    """Return True if user exists and is considered authenticated."""
    user = await get_user_by_telegram_id(telegram_id)
    if not user:
        return False
    # Guests are considered allowed to proceed without extra checks
    if user.role == Role.GUEST.value:
        return True
    # For guards/admins rely on DB flag used by the project
    return getattr(user, "is_authenticated", False)


async def has_role(telegram_id: int, required_role: str) -> bool:
    """Return True if user has the exact required role."""
    user = await get_user_by_telegram_id(telegram_id)
    if not user:
        return False
    return user.role == required_role


async def has_any_role(telegram_id: int, roles: List[str]) -> bool:
    """Return True if user has any role from the provided list."""
    user = await get_user_by_telegram_id(telegram_id)
    if not user:
        return False
    return user.role in roles


def require_role(role: str):
    """Decorator that restricts access to a single role."""

    def decorator(handler: Callable[..., Awaitable[Any]]):
        @wraps(handler)
        async def wrapper(message: types.Message, *args, **kwargs):
            if not await has_role(message.from_user.id, role):
                await message.reply(f"Access denied. Required role: {role}")
                return
            return await handler(message, *args, **kwargs)

        return wrapper

    return decorator


def require_any_role(roles: List[str]):
    """Decorator that allows any of the listed roles."""

    def decorator(handler: Callable[..., Awaitable[Any]]):
        @wraps(handler)
        async def wrapper(message: types.Message, *args, **kwargs):
            if not await has_any_role(message.from_user.id, roles):
                roles_str = ", ".join(roles)
                await message.reply(f"Access denied. Required roles: {roles_str}")
                return
            return await handler(message, *args, **kwargs)

        return wrapper

    return decorator


def require_auth(handler: Callable[..., Awaitable[Any]]):
    """Decorator that requires the user to be authenticated."""

    @wraps(handler)
    async def wrapper(message: types.Message, *args, **kwargs):
        if not await is_authenticated(message.from_user.id):
            await message.reply("Please authenticate first. Send /start")
            return
        return await handler(message, *args, **kwargs)

    return wrapper

