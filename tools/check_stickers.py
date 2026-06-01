"""
Run from the project root:
    python tools/check_stickers.py

Prints all stickers in the configured pack with their emoji,
and shows how many stickers fall into each mood category.
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from config import settings
from stickers import MOOD_EMOJIS

EMOJI_TO_MOOD = {emoji: mood for mood, emojis in MOOD_EMOJIS.items() for emoji in emojis}


async def main() -> None:
    bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties())
    pack_name = settings.STICKER_SET_NAME
    print(f"Sticker pack: {pack_name}\n")

    sticker_set = await bot.get_sticker_set(pack_name)
    stickers = sticker_set.stickers

    mood_counts: dict[str, int] = {mood: 0 for mood in MOOD_EMOJIS}
    reserve = 0

    for i, sticker in enumerate(stickers, start=1):
        emoji = sticker.emoji or "?"
        mood = EMOJI_TO_MOOD.get(emoji)
        if mood:
            mood_counts[mood] += 1
            tag = f"[{mood}]"
        else:
            reserve += 1
            tag = "[reserve]"
        print(f"  {i:>3}. {emoji}  {tag:<12}  file_id: {sticker.file_id[:24]}…")

    print(f"\n{'─' * 40}")
    print(f"Total stickers: {len(stickers)}\n")
    for mood, count in mood_counts.items():
        bar = "█" * count
        print(f"  {mood:<10} {count:>3}  {bar}")
    print(f"  {'reserve':<10} {reserve:>3}")

    await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
