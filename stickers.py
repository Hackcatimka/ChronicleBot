import logging
import random

from aiogram import Bot

logger = logging.getLogger(__name__)

# Canonical emoji per mood — single source of truth for this project and check_stickers.py
MOOD_EMOJIS: dict[str, list[str]] = {
    "happy":    ["😁"],
    "proud":    ["🥰"],
    "grateful": ["🙏"],
    "excited":  ["🥳"],
    "calm":     ["😌"],
    "sad":      ["😢"],
}

TAG_TO_MOOD: dict[str, str] = {
    "work":          "proud",
    "health":        "calm",
    "learning":      "excited",
    "creativity":    "excited",
    "relationships": "grateful",
    "mindfulness":   "calm",
    "finance":       "proud",
    "other":         "happy",
}

_EMOJI_TO_MOOD = {emoji: mood for mood, emojis in MOOD_EMOJIS.items() for emoji in emojis}
_cache: dict[str, list[str]] = {}   # mood -> file_ids; "_all" -> every file_id


async def _load_cache(bot: Bot, set_name: str) -> None:
    global _cache
    try:
        sticker_set = await bot.get_sticker_set(set_name)
    except Exception:
        logger.warning("Failed to load sticker set %r", set_name)
        return
    by_mood: dict[str, list[str]] = {mood: [] for mood in MOOD_EMOJIS}
    all_ids: list[str] = []
    for s in sticker_set.stickers:
        fid = s.file_id
        all_ids.append(fid)
        mood = _EMOJI_TO_MOOD.get(s.emoji or "")
        if mood:
            by_mood[mood].append(fid)
    _cache = {**by_mood, "_all": all_ids}


async def send_mood_sticker(
    bot: Bot, chat_id: int, mood: str | None, set_name: str, enabled: bool = True
) -> None:
    if not enabled or not set_name:
        return
    if not _cache:
        await _load_cache(bot, set_name)
    if not _cache:
        return
    pool = (_cache.get(mood) or []) if mood else []
    if not pool:
        pool = _cache.get("_all") or []
    if pool:
        try:
            await bot.send_sticker(chat_id, random.choice(pool))
        except Exception:
            pass


async def send_random_sticker(bot: Bot, chat_id: int, set_name: str, enabled: bool = True) -> None:
    await send_mood_sticker(bot, chat_id, None, set_name, enabled)
