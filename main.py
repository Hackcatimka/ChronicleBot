import asyncio
import logging

from aiogram import BaseMiddleware, Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from config import settings
from db.engine import async_session, init_db
from handlers.start import router as start_router
from handlers.stats import router as stats_router
from handlers.then import router as then_router
from handlers.reminders import router as reminders_router
from handlers.goals import router as goals_router
from handlers.wins import router as wins_router
from scheduler import init_scheduler

logging.basicConfig(level=logging.INFO)


class DBSessionMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        async with async_session() as session:
            data["session"] = session
            return await handler(event, data)


async def main() -> None:
    bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher()
    dp.message.middleware(DBSessionMiddleware())
    dp.callback_query.middleware(DBSessionMiddleware())

    dp.include_router(start_router)
    dp.include_router(stats_router)
    dp.include_router(then_router)
    dp.include_router(reminders_router)
    dp.include_router(goals_router)
    dp.include_router(wins_router)

    await init_db()
    await init_scheduler(bot)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
