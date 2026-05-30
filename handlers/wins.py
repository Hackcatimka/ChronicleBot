import asyncio
import logging
from datetime import datetime, timezone

from aiogram import Bot, F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from aiogram.utils.chat_action import ChatActionSender
from sqlalchemy import func, select

from ai import ask_praise, classify_intent, classify_tag
from dateparse import extract_win_date
from ratelimit import check as rate_check

_saving_users: set[int] = set()
_MAX_INPUT_LEN = 2000
from config import settings
from db.models import Goal, User, Win, WinGoal
from keyboards import get_intent_keyboard, get_main_menu_keyboard, get_win_confirmation_keyboard
from locales import t
from stickers import send_random_sticker
from utils import edit_or_answer, try_delete

router = Router()
logger = logging.getLogger(__name__)


class WinStates(StatesGroup):
    waiting_for_confirmation = State()
    waiting_for_goal = State()


async def _show_main_menu(message: Message, session) -> None:
    user = await session.scalar(select(User).filter_by(tg_id=message.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    await message.answer(t(lang, "main_menu"), reply_markup=get_main_menu_keyboard(lang))


@router.message(F.text, ~StateFilter(WinStates.waiting_for_confirmation))
async def request_win_text(message: Message, state: FSMContext, session, bot: Bot) -> None:
    if message.text is None or message.text.startswith("/"):
        return

    user = await session.scalar(select(User).filter_by(tg_id=message.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    if user is None:
        await message.answer(t(lang, "user_not_found"))
        return

    if not rate_check(message.from_user.id):
        await message.answer(t(lang, "rate_limited"))
        return
    if len(message.text) > _MAX_INPUT_LEN:
        await message.answer(t(lang, "input_too_long"))
        return

    user.last_active_at = datetime.now(timezone.utc)
    session.add(user)
    await session.commit()

    async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
        intent, tag = await asyncio.gather(
            classify_intent(message.text),
            classify_tag(message.text),
        )
    await state.update_data(raw_text=message.text, tag=tag)
    await state.set_state(WinStates.waiting_for_confirmation)

    if intent == "goal":
        await message.answer(
            t(lang, "intent_goal_question"),
            reply_markup=get_intent_keyboard(lang),
        )
    else:
        await message.answer(
            t(lang, "win_received", text=message.text),
            reply_markup=get_win_confirmation_keyboard(lang),
        )


@router.callback_query(F.data == "intent:as_win")
async def intent_as_win(query: CallbackQuery, state: FSMContext, session) -> None:
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    data = await state.get_data()
    raw_text = data.get("raw_text")
    if not raw_text:
        await query.answer(t(lang, "no_text_to_save"), show_alert=True)
        await state.clear()
        return
    await query.answer()
    await edit_or_answer(
        query.message,
        t(lang, "win_received", text=raw_text),
        get_win_confirmation_keyboard(lang),
    )


@router.callback_query(F.data == "intent:as_goal")
async def intent_as_goal(query: CallbackQuery, state: FSMContext, session) -> None:
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    data = await state.get_data()
    raw_text = data.get("raw_text")
    if not raw_text or user is None:
        await query.answer(t(lang, "no_text_to_save"), show_alert=True)
        await state.clear()
        return

    goal = Goal(user_id=user.id, title=raw_text, status="active")
    session.add(goal)
    await query.answer()
    await session.commit()
    await state.clear()
    await edit_or_answer(
        query.message,
        t(lang, "goal_saved_quick", title=raw_text),
        get_main_menu_keyboard(lang),
    )


@router.callback_query(F.data == "save_win", StateFilter(WinStates.waiting_for_confirmation))
async def save_win(query: CallbackQuery, state: FSMContext, session, bot: Bot) -> None:
    uid = query.from_user.id
    if uid in _saving_users:
        await query.answer()
        return
    _saving_users.add(uid)
    try:
        await _do_save_win(query, state, session, bot)
    finally:
        _saving_users.discard(uid)


async def _do_save_win(query: CallbackQuery, state: FSMContext, session, bot: Bot) -> None:
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"

    if user is None:
        await query.answer(t(lang, "user_not_found"), show_alert=True)
        return
    data = await state.get_data()
    raw_text = data.get("raw_text")
    if not raw_text:
        await query.answer(t(lang, "no_text_to_save"), show_alert=True)
        return
    tag = data.get("tag", "other")
    today = datetime.now(timezone.utc).date()
    win_date = extract_win_date(raw_text, today)
    created_at = datetime(win_date.year, win_date.month, win_date.day, tzinfo=timezone.utc) if win_date else None
    win = Win(user_id=user.id, raw_text=raw_text, processed_text=raw_text, tag=tag)
    if created_at:
        win.created_at = created_at
    session.add(win)
    user.last_active_at = datetime.now(timezone.utc)
    session.add(user)
    await session.commit()

    count = await session.scalar(select(func.count()).select_from(Win).filter_by(user_id=user.id))
    tag_label = t(lang, f"tag_{tag}")
    stickers_enabled = getattr(user, "stickers_enabled", True)
    chat_id = query.message.chat.id
    await query.answer()
    try:
        async with ChatActionSender.typing(bot=bot, chat_id=chat_id):
            praise = await ask_praise(user.tone, raw_text, count, lang)
        result_text = f"{praise}\n\n{tag_label}"
    except Exception:
        logger.warning("AI praise failed for user %s", user.id, exc_info=True)
        tone_reply = {
            "friend": t(lang, "tone_reply_friend", count=count),
            "coach": t(lang, "tone_reply_coach", count=count),
            "mirror": t(lang, "tone_reply_mirror", count=count),
        }
        result_text = tone_reply.get(user.tone, t(lang, "tone_reply_mirror", count=count)) + f"\n\n{tag_label}"

    if stickers_enabled:
        await try_delete(query.message)
        await send_random_sticker(bot, chat_id, settings.STICKER_SET_NAME, True)
        await bot.send_message(chat_id, result_text, reply_markup=get_main_menu_keyboard(lang))
    else:
        await edit_or_answer(query.message, result_text, get_main_menu_keyboard(lang))
    await state.clear()


@router.callback_query(F.data == "edit_win", StateFilter(WinStates.waiting_for_confirmation))
async def edit_win(query: CallbackQuery, state: FSMContext, session) -> None:
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    await state.clear()
    await query.answer()
    await edit_or_answer(query.message, t(lang, "win_edit_prompt"))


@router.callback_query(F.data == "cancel_win", StateFilter(WinStates.waiting_for_confirmation))
async def cancel_win(query: CallbackQuery, state: FSMContext, session) -> None:
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    await state.clear()
    await query.answer()
    await edit_or_answer(query.message, t(lang, "win_cancelled"), get_main_menu_keyboard(lang))


@router.callback_query(F.data == "link_goal", StateFilter(WinStates.waiting_for_confirmation))
async def link_goal(query: CallbackQuery, state: FSMContext, session) -> None:
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"

    data = await state.get_data()
    raw_text = data.get("raw_text")
    if not raw_text:
        await query.answer(t(lang, "no_text_to_save"), show_alert=True)
        return

    if user is None:
        await query.answer(t(lang, "user_not_found"), show_alert=True)
        return
    goals = await session.scalars(select(Goal).filter_by(user_id=user.id, status="active"))
    goals = goals.all()
    if not goals:
        await query.answer()
        await edit_or_answer(query.message, t(lang, "no_goals"), get_main_menu_keyboard(lang))
        await state.clear()
        return

    win = Win(user_id=user.id, raw_text=raw_text, processed_text=raw_text)
    session.add(win)
    await session.commit()

    await state.update_data(win_id=win.id)
    await state.set_state(WinStates.waiting_for_goal)

    buttons = [
        [InlineKeyboardButton(text=f"🎯 {goal.title}", callback_data=f"win:link:{goal.id}")] for goal in goals
    ]
    buttons.append([InlineKeyboardButton(text=t(lang, "btn_back"), callback_data="cancel_win")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await query.answer()
    await edit_or_answer(query.message, t(lang, "choose_goal_for_win"), keyboard)


@router.callback_query(F.data.startswith("win:link:"), StateFilter(WinStates.waiting_for_goal))
async def link_win_to_goal(query: CallbackQuery, state: FSMContext, session) -> None:
    try:
        goal_id = int(query.data.split(":", 2)[2])
    except ValueError:
        await query.answer()
        return
    data = await state.get_data()
    win_id = data.get("win_id")
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"

    if not win_id:
        await query.answer(t(lang, "no_text_to_save"), show_alert=True)
        await state.clear()
        return

    goal = await session.scalar(select(Goal).filter_by(id=goal_id, user_id=user.id, status="active"))
    if goal is None:
        await query.answer(t(lang, "goal_not_found"), show_alert=True)
        await state.clear()
        return

    existing = await session.scalar(select(WinGoal).filter_by(win_id=win_id, goal_id=goal.id))
    if existing is None:
        link = WinGoal(win_id=win_id, goal_id=goal.id)
        session.add(link)
        await session.commit()
    await query.answer()
    await edit_or_answer(query.message, t(lang, "win_linked"), get_main_menu_keyboard(lang))
    await state.clear()


@router.callback_query(F.data.startswith("menu:"))
async def main_menu_handler(query: CallbackQuery, state: FSMContext, session) -> None:
    action = query.data.split(":", 1)[1]
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    await query.answer()

    if action == "record_win":
        await state.clear()
        await edit_or_answer(query.message, t(lang, "win_record_prompt"))
        return

    await edit_or_answer(query.message, t(lang, "back_to_menu"))
