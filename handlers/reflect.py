import logging
from datetime import datetime, timedelta, timezone

from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery
from aiogram.utils.chat_action import ChatActionSender
from sqlalchemy import select

from ai import ask_reflect_analysis
from config import settings
from db.models import User, Win
from keyboards import get_main_menu_keyboard
from locales import t
from ratelimit import check as rate_check
from stickers import send_mood_sticker
from utils import edit_or_answer, try_delete

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(F.data == "menu:reflect")
async def show_reflect(query: CallbackQuery, session, bot: Bot) -> None:
    if not rate_check(query.from_user.id):
        await query.answer(t("en", "rate_limited"), show_alert=True)
        return
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    if user is None:
        await query.answer(t(lang, "user_not_found"), show_alert=True)
        return

    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    wins = (await session.scalars(
        select(Win).filter(Win.user_id == user.id, Win.created_at >= cutoff).order_by(Win.created_at)
    )).all()

    if not wins:
        await query.answer()
        await edit_or_answer(query.message, t(lang, "reflect_no_wins"), get_main_menu_keyboard(lang))
        return

    await query.answer()
    msg = await edit_or_answer(query.message, t(lang, "reflect_analysing"))

    try:
        wins_with_tags = [(win.raw_text, win.tag or "other") for win in wins]
        async with ChatActionSender.typing(bot=bot, chat_id=query.message.chat.id):
            analysis = await ask_reflect_analysis(user.tone, wins_with_tags, lang)
    except Exception:
        logger.warning("AI reflect analysis failed for user %s", user.id, exc_info=True)
        analysis = t(lang, "reflect_error")

    stickers_enabled = getattr(user, "stickers_enabled", False)
    chat_id = query.message.chat.id
    if stickers_enabled:
        await try_delete(msg)
        await send_mood_sticker(bot, chat_id, "calm", settings.STICKER_SET_NAME, True)
        await bot.send_message(chat_id, analysis)
    else:
        await edit_or_answer(msg, analysis)
    await bot.send_message(chat_id, t(lang, "main_menu"), reply_markup=get_main_menu_keyboard(lang))
