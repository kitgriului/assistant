from aiogram.fsm.state import StatesGroup, State


class ClientStates(StatesGroup):
    idle = State()
