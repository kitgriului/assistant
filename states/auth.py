"""FSM states for authentication: login for guard/admin, registration for guest."""
from aiogram.fsm.state import StatesGroup, State


class AuthStates(StatesGroup):
    """Состояния для аутентификации охранников и администраторов."""
    waiting_login = State()
    waiting_password = State()


class GuestRegistrationStates(StatesGroup):
    """Состояния для регистрации гостей."""
    waiting_name = State()
