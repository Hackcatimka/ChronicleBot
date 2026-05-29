import random
from datetime import datetime, timedelta, timezone

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.chat_action import ChatActionSender
from sqlalchemy import select

from ai import ask_reflect
from db.models import User, Win
from keyboards import get_main_menu_keyboard
from locales import t
from ratelimit import check as rate_check
from utils import edit_or_answer

router = Router()


def get_time_machine_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "btn_show_another"), callback_data="then:another")],
        [InlineKeyboardButton(text=t(lang, "btn_back"), callback_data="then:back")],
    ])


def _format_date(dt: datetime) -> str:
    return dt.strftime("%d %b %Y")


async def _get_user_and_old_win_ids(query: CallbackQuery, session):
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    if user is None:
        return None, []

    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    ids = await session.scalars(
        select(Win.id).filter(Win.user_id == user.id, Win.created_at < cutoff)
    )
    return user, ids.all()


async def _fetch_win_by_id(session, win_id: int, user_id: int):
    return await session.scalar(select(Win).filter_by(id=win_id, user_id=user_id))


async def _select_random_old_win(session, query: CallbackQuery, exclude_id: int | None = None):
    user, ids = await _get_user_and_old_win_ids(query, session)
    if user is None:
        return None, None, None

    available_ids = [win_id for win_id in ids if win_id != exclude_id]
    if not available_ids:
        return user, None, ids

    selected_id = random.choice(available_ids)
    win = await _fetch_win_by_id(session, selected_id, user.id)
    return user, win, ids


@router.callback_query(F.data == "menu:time_machine")
async def show_time_machine(query: CallbackQuery, state: FSMContext, session, bot: Bot) -> None:
    if not rate_check(query.from_user.id):
        await query.answer(t("en", "rate_limited"), show_alert=True)
        return
    user, ids = await _get_user_and_old_win_ids(query, session)
    lang = getattr(user, "language", "en") if user else "en"
    if user is None:
        await query.answer(t(lang, "user_not_found"), show_alert=True)
        return

    if not ids:
        await query.answer()
        await query.message.answer(
            t(lang, "no_memories"),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t(lang, "btn_back"), callback_data="then:back")]]),
        )
        return

    win_id = random.choice(ids)
    win = await _fetch_win_by_id(session, win_id, user.id)
    if win is None:
        await query.answer(t(lang, "goal_not_found"), show_alert=True)
        return

    days_ago = (datetime.now(timezone.utc).date() - win.created_at.date()).days
    await state.update_data(last_win_id=win.id)
    await query.answer()
    await query.message.answer(
        t(lang, "memory", date=_format_date(win.created_at), text=win.raw_text, days=days_ago),
        reply_markup=get_time_machine_keyboard(lang),
    )
    try:
        async with ChatActionSender.typing(bot=bot, chat_id=query.message.chat.id):
            reflection = await ask_reflect(user.tone, win.raw_text, days_ago, lang)
        await query.message.answer(reflection)
    except Exception:
        pass


@router.callback_query(F.data == "then:another")
async def show_another(query: CallbackQuery, state: FSMContext, session, bot: Bot) -> None:
    if not rate_check(query.from_user.id):
        await query.answer(t("en", "rate_limited"), show_alert=True)
        return
    data = await state.get_data()
    last_win_id = data.get("last_win_id")
    user, win, ids = await _select_random_old_win(session, query, exclude_id=last_win_id)
    lang = getattr(user, "language", "en") if user else "en"
    if user is None:
        await query.answer(t(lang, "user_not_found"), show_alert=True)
        await state.clear()
        return

    if win is None:
        await query.answer()
        await query.message.answer(
            t(lang, "only_memory"),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t(lang, "btn_back"), callback_data="then:back")]]),
        )
        return

    days_ago = (datetime.now(timezone.utc).date() - win.created_at.date()).days
    await state.update_data(last_win_id=win.id)
    await query.answer()
    await query.message.answer(
        t(lang, "memory", date=_format_date(win.created_at), text=win.raw_text, days=days_ago),
        reply_markup=get_time_machine_keyboard(lang),
    )
    try:
        async with ChatActionSender.typing(bot=bot, chat_id=query.message.chat.id):
            reflection = await ask_reflect(user.tone, win.raw_text, days_ago, lang)
        await query.message.answer(reflection)
    except Exception:
        pass


@router.callback_query(F.data == "then:back")
async def time_machine_back(query: CallbackQuery, state: FSMContext, session) -> None:
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    await state.clear()
    await query.answer()
    await edit_or_answer(query.message, t(lang, "main_menu"), get_main_menu_keyboard(lang))
