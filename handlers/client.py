"""Client handlers: view and filter requests, download media, export data."""
from aiogram import Dispatcher, types
from aiogram.filters import Command
from database.session import get_session
from database.models import Request
from utils.export import export_requests_placeholder
import logging

logger = logging.getLogger(__name__)


def register_client_handlers(dp: Dispatcher):
    dp.message.register(cmd_list, Command(commands=["list_requests"]))
    dp.message.register(cmd_export, Command(commands=["export_requests"]))


async def cmd_list(message: types.Message):
    async with get_session() as session:
        q = await session.execute(Request.__table__.select().limit(20))
        rows = q.fetchall()
    if not rows:
        await message.reply("No requests found.")
        return
    text = "Requests:\n"
    for r in rows:
        text += f"{r.id}: {r.name} - {r.status}\n"
    await message.reply(text)


async def cmd_export(message: types.Message):
    path = await export_requests_placeholder()
    await message.reply_document(types.FSInputFile(path))
