import html
from datetime import datetime, timezone

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from db.models import User
from keyboards import get_language_keyboard, get_main_menu_keyboard, get_tone_keyboard
from locales import t
from utils import edit_or_answer, edit_stored

router = Router()


class OnboardingStates(StatesGroup):
    waiting_for_timezone = State()


_WELCOME_NEW = "🌍 Choose your language / Выбери язык:"


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
    await message.answer(t(lang, "welcome_back", name=html.escape(user.name)))
    await message.answer(t(lang, "main_menu"), reply_markup=get_main_menu_keyboard(lang))


@router.callback_query(F.data == "main:back")
async def main_back(query: CallbackQuery, session) -> None:
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    await query.answer()
    await edit_or_answer(query.message, t(lang, "main_menu"), get_main_menu_keyboard(lang))


@router.callback_query(F.data.startswith("lang:"))
async def language_callback(query: CallbackQuery, state: FSMContext, session) -> None:
    lang = query.data.split(":", 1)[1]
    if lang not in {"en", "ru"}:
        await query.answer()
        return
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))

    is_new_user = user is None
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
    if is_new_user:
        await state.update_data(onboarding=True)
    await query.answer()
    text = t(lang, "onboarding_welcome") if is_new_user else t(lang, "choose_tone")
    await edit_or_answer(query.message, text, get_tone_keyboard(lang))


@router.callback_query(F.data.startswith("tone:"))
async def tone_callback(query: CallbackQuery, state: FSMContext, session) -> None:
    tone = query.data.split(":", 1)[1]
    if tone not in {"friend", "coach", "mirror"}:
        await query.answer()
        return
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
    data = await state.get_data()
    await query.answer()

    if data.get("onboarding"):
        await state.set_state(OnboardingStates.waiting_for_timezone)
        sent = await edit_or_answer(query.message, t(lang, "onboarding_timezone_prompt"))
        await state.update_data(bot_msg_id=sent.message_id, chat_id=sent.chat.id)
    else:
        await state.clear()
        await edit_or_answer(
            query.message,
            t(lang, "tone_selected", tone=t(lang, f"tone_{tone}")),
            get_main_menu_keyboard(lang),
        )


@router.message(StateFilter(OnboardingStates.waiting_for_timezone), F.text)
async def onboarding_timezone(message: Message, state: FSMContext, session) -> None:
    user = await session.scalar(select(User).filter_by(tg_id=message.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    data = await state.get_data()
    msg_id = data.get("bot_msg_id")

    text = message.text.strip()
    try:
        offset = int(text.replace(" ", ""))
        if not (-12 <= offset <= 14):
            raise ValueError
    except ValueError:
        sent = await edit_stored(message.bot, message.chat.id, msg_id, t(lang, "timezone_invalid"))
        await state.update_data(bot_msg_id=sent.message_id)
        return

    if user:
        user.utc_offset = offset
        session.add(user)
        await session.commit()

    offset_str = f"+{offset}" if offset >= 0 else str(offset)
    await state.clear()
    await edit_stored(
        message.bot, message.chat.id, msg_id,
        t(lang, "onboarding_timezone_saved", offset=offset_str),
        get_main_menu_keyboard(lang),
    )
