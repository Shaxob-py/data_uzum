import asyncio

from aiogram import Bot

from core.core import settings
from database.base import db
from handler.user import dp
from handler.data import dp
from admin.admin import dp

TOKEN = settings.BOT_TOKEN


async def main() -> None:
    bot = Bot(token=TOKEN)
    await db.create_all()
    await asyncio.sleep(0.5)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
