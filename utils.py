from datetime import datetime

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import InlineKeyboardMarkup, Message

def split_tags(tag: str | None) -> list[str]:
    if not tag:
        return ["other"]
    parts = [t.strip() for t in tag.split(",") if t.strip()]
    return parts if parts else ["other"]


_RU_MONTHS_SHORT = ["", "янв", "фев", "мар", "апр", "май", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"]
_RU_WEEKDAYS_SHORT = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]


def format_date(dt: datetime, lang: str = "en", weekday: bool = False, year: bool = True) -> str:
    if lang == "ru":
        month = _RU_MONTHS_SHORT[dt.month]
        if weekday:
            wd = _RU_WEEKDAYS_SHORT[dt.weekday()]
            return f"{wd}, {dt.day:02d} {month}"
        return f"{dt.day:02d} {month} {dt.year}" if year else f"{dt.day:02d} {month}"
    if weekday:
        return dt.strftime("%a, %d %b")
    return dt.strftime("%d %b %Y") if year else dt.strftime("%d %b")


async def try_delete(message: Message) -> None:
    try:
        await message.delete()
    except TelegramBadRequest:
        pass


async def edit_or_answer(message: Message, text: str, reply_markup: InlineKeyboardMarkup | None = None) -> Message:
    try:
        result = await message.edit_text(text, reply_markup=reply_markup)
        return result if isinstance(result, Message) else message
    except TelegramBadRequest:
        return await message.answer(text, reply_markup=reply_markup)


async def edit_stored(
    bot: Bot,
    chat_id: int,
    msg_id: int | None,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
) -> Message:
    if msg_id:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=msg_id)
        except TelegramBadRequest:
            pass
    return await bot.send_message(chat_id, text, reply_markup=reply_markup)
