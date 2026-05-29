from datetime import datetime, timezone

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from db.models import User
from keyboards import get_language_keyboard, get_main_menu_keyboard, get_tone_keyboard
from locales import t

router = Router()

_WELCOME_NEW = (
    "👋 Hi! / Привет!\n\n"
    "I'm <b>Chronicle</b> — your personal wins journal.\n"
    "Я <b>Chronicle</b> — твой личный дневник побед.\n\n"
    "Every day you do things worth remembering — at work, at home, for yourself. "
    "Most of it gets forgotten.\n"
    "Каждый день ты делаешь что-то стоящее — на работе, дома, для себя. "
    "Большинство из этого забывается.\n\n"
    "Chronicle fixes that. Just write what went well — big or small. "
    "I'll save your wins, track your goals, and show how far you've come.\n"
    "Chronicle это меняет. Просто пиши что пошло хорошо — большое или маленькое. "
    "Я сохраню победы, прослежу за целями и покажу как далеко ты зашёл.\n\n"
    "Choose your language / Выбери язык 👇"
)


@router.message(Command("start"))
async def start_handler(message: Message, session) -> None:
    user = await session.scalar(select(User).filter_by(tg_id=message.from_user.id))
    if user is None:
        await message.answer(_WELCOME_NEW, reply_markup=get_language_keyboard())
        return

    lang = getattr(user, "language", "en")
    user.last_active_at = datetime.now(timezone.utc)
    session.add(user)
    await session.commit()
    await message.answer(t(lang, "welcome_back", name=user.name))
    await message.answer(t(lang, "main_menu"), reply_markup=get_main_menu_keyboard(lang))


@router.callback_query(F.data == "main:back")
async def main_back(query: CallbackQuery, session) -> None:
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    await query.answer()
    await query.message.answer(t(lang, "main_menu"), reply_markup=get_main_menu_keyboard(lang))


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
        user.last_active_at = datetime.now(timezone.utc)
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
        user.last_active_at = datetime.now(timezone.utc)
        session.add(user)

    await session.commit()
    await query.answer()
    await query.message.answer(
        t(lang, "tone_selected", tone=t(lang, f"tone_{tone}")),
        reply_markup=get_main_menu_keyboard(lang),
    )
