from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import InlineKeyboardMarkup, Message


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
