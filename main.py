import asyncio
import logging
import os

import sentry_sdk
from aiogram import BaseMiddleware, Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.types import ErrorEvent

from config import settings
from db.engine import async_session, init_db
from handlers.admin import router as admin_router
from handlers.search import router as search_router
from handlers.start import router as start_router
from handlers.stats import router as stats_router
from handlers.then import router as then_router
from handlers.reflect import router as reflect_router
from handlers.reminders import router as reminders_router
from handlers.goals import router as goals_router
from handlers.wins import router as wins_router
from scheduler import init_scheduler

if settings.SENTRY_DSN:
    sentry_sdk.init(dsn=settings.SENTRY_DSN, environment=settings.ENV)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DBSessionMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        async with async_session() as session:
            data["session"] = session
            return await handler(event, data)


async def _global_error_handler(event: ErrorEvent, bot: Bot) -> None:
    logger.exception(
        "Unhandled exception in update %s", event.update.update_id,
        exc_info=event.exception,
    )
    update = event.update
    chat_id = None

    if update.message:
        chat_id = update.message.chat.id
    elif update.callback_query:
        chat_id = update.callback_query.message.chat.id
        try:
            await update.callback_query.answer()
        except Exception:
            pass

    if chat_id:
        try:
            await bot.send_message(
                chat_id,
                "Something went wrong. Please try again.\n"
                "Что-то пошло не так. Попробуй ещё раз.",
            )
        except Exception:
            pass


async def _health_server(port: int) -> None:
    response = (
        b"HTTP/1.1 200 OK\r\n"
        b"Content-Type: text/plain\r\n"
        b"Content-Length: 2\r\n\r\nok"
    )

    async def handle(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        try:
            await reader.read(1024)
        except Exception:
            pass
        writer.write(response)
        await writer.drain()
        writer.close()

    server = await asyncio.start_server(handle, "0.0.0.0", port)
    async with server:
        await server.serve_forever()


async def main() -> None:
    bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher()
    dp.message.middleware(DBSessionMiddleware())
    dp.callback_query.middleware(DBSessionMiddleware())
    dp.error.register(_global_error_handler)

    dp.include_router(admin_router)
    dp.include_router(search_router)
    dp.include_router(start_router)
    dp.include_router(stats_router)
    dp.include_router(then_router)
    dp.include_router(reflect_router)
    dp.include_router(reminders_router)
    dp.include_router(goals_router)
    dp.include_router(wins_router)

    await init_db()
    await init_scheduler(bot)

    port = int(os.getenv("PORT", "8080"))
    asyncio.create_task(_health_server(port))

    await dp.start_polling(bot)


def _run_migrations() -> None:
    from alembic.config import Config
    from alembic import command
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")


if __name__ == "__main__":
    _run_migrations()
    asyncio.run(main())
