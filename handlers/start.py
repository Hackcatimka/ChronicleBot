from datetime import datetime

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from db.models import User
from keyboards import get_language_keyboard, get_main_menu_keyboard, get_tone_keyboard
from locales import t

router = Router()


@router.message(Command("start"))
async def start_handler(message: Message, session) -> None:
    user = await session.scalar(select(User).filter_by(tg_id=message.from_user.id))
    if user is None:
        await message.answer(t("en", "choose_language"), reply_markup=get_language_keyboard())
        return

    lang = getattr(user, "language", "en")
    user.last_active_at = datetime.utcnow()
    session.add(user)
    await session.commit()
    await message.answer(t(lang, "welcome_back", name=user.name))
    await message.answer(t(lang, "main_menu"), reply_markup=get_main_menu_keyboard(lang))


@router.callback_query(F.data.startswith("lang:"))
async def language_callback(query: CallbackQuery, session) -> None:
    lang = query.data.split(":", 1)[1]
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))

    if user is None:
        user = User(
            tg_id=query.from_user.id,
            name=query.from_user.full_name or "Telegram User",
            tone="friend",
            language=lang,
        )
        session.add(user)
    else:
        user.language = lang
        user.last_active_at = datetime.utcnow()
        session.add(user)

    await session.commit()
    await query.answer()
    await query.message.answer(t(lang, "choose_tone"), reply_markup=get_tone_keyboard(lang))


@router.callback_query(F.data.startswith("tone:"))
async def tone_callback(query: CallbackQuery, session) -> None:
    tone = query.data.split(":", 1)[1]
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))

    if user is None:
        lang = "en"
        user = User(
            tg_id=query.from_user.id,
            name=query.from_user.full_name or "Telegram User",
            tone=tone,
            language=lang,
        )
        session.add(user)
    else:
        lang = getattr(user, "language", "en")
        user.tone = tone
        user.last_active_at = datetime.utcnow()
        session.add(user)

    await session.commit()
    await query.answer()
    await query.message.answer(
        t(lang, "tone_selected", tone=t(lang, f"tone_{tone}")),
        reply_markup=get_main_menu_keyboard(lang),
    )
