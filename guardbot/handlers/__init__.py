from aiogram import Dispatcher

from .auth_phone import router as auth_router
from .admin import router as admin_router
from .menu import router as menu_router
from .applicant import register_applicant_handlers
from .guard import register_guard_handlers
from .client import register_client_handlers
from .patrol import router as patrol_router
from .requests import router as requests_router


def register_handlers(dp: Dispatcher):
    # ВАЖНО: Сначала регистрируем auth handlers (они обрабатывают /start и контакты)
    dp.include_router(auth_router)
    
    # Меню и навигация
    dp.include_router(menu_router)
    dp.include_router(requests_router)
    
    # Патрулирование
    dp.include_router(patrol_router)
    
    # Админские команды
    dp.include_router(admin_router)
    
    # Затем регистрируем обработчики для всех ролей
    register_applicant_handlers(dp)
    register_guard_handlers(dp)
    register_client_handlers(dp)
