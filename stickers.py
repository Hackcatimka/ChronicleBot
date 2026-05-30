import logging
import random

from aiogram import Bot

logger = logging.getLogger(__name__)
_cache: list[str] = []


async def send_random_sticker(bot: Bot, chat_id: int, set_name: str) -> None:
    global _cache
    if not set_name:
        return
    if not _cache:
        try:
            sticker_set = await bot.get_sticker_set(set_name)
            _cache = [s.file_id for s in sticker_set.stickers]
        except Exception:
            logger.warning("Failed to load sticker set %r", set_name)
            return
    if _cache:
        try:
            await bot.send_sticker(chat_id, random.choice(_cache))
        except Exception:
            pass
