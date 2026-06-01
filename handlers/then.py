import logging
import random
from datetime import datetime, timedelta, timezone

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from aiogram.utils.chat_action import ChatActionSender
from sqlalchemy import select

from ai import ask_reflect
from config import settings
from db.models import User, Win
from keyboards import get_main_menu_keyboard
from locales import t
from ratelimit import check as rate_check
from stickers import send_random_sticker
from utils import edit_or_answer, edit_stored, format_date, try_delete

from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

router = Router()
logger = logging.getLogger(__name__)


class TimeMachineEditStates(StatesGroup):
    editing = State()


def get_time_machine_keyboard(lang: str, win_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "btn_edit_win"), callback_data=f"then:edit:{win_id}"),
         InlineKeyboardButton(text=t(lang, "btn_delete_win"), callback_data=f"then:delete:{win_id}")],
        [InlineKeyboardButton(text=t(lang, "btn_show_another"), callback_data="then:another")],
        [InlineKeyboardButton(text=t(lang, "btn_back"), callback_data="then:back")],
    ])


def _back_only_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "btn_back"), callback_data="then:back")],
    ])


def _after_edit_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "btn_show_another"), callback_data="then:another")],
        [InlineKeyboardButton(text=t(lang, "btn_back"), callback_data="then:back")],
    ])


def _format_date(dt: datetime, lang: str = "en") -> str:
    return format_date(dt, lang)


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
        await edit_or_answer(query.message, t(lang, "no_memories"), _back_only_keyboard(lang))
        return

    win_id = random.choice(ids)
    win = await _fetch_win_by_id(session, win_id, user.id)
    if win is None:
        await query.answer(t(lang, "goal_not_found"), show_alert=True)
        return

    days_ago = (datetime.now(timezone.utc).date() - win.created_at.date()).days
    await state.update_data(last_win_id=win.id)
    await query.answer()

    memory_text = t(lang, "memory", date=_format_date(win.created_at, lang), text=win.raw_text, days=days_ago)
    stickers_enabled = getattr(user, "stickers_enabled", False)
    chat_id = query.message.chat.id
    msg = await edit_or_answer(query.message, memory_text, get_time_machine_keyboard(lang, win.id))

    try:
        async with ChatActionSender.typing(bot=bot, chat_id=chat_id):
            reflection = await ask_reflect(user.tone, win.raw_text, days_ago, lang)
        final_text = f"{memory_text}\n\n{reflection}"
        if stickers_enabled:
            await try_delete(msg)
            await send_random_sticker(bot, chat_id, settings.STICKER_SET_NAME, True)
            await bot.send_message(chat_id, final_text, reply_markup=get_time_machine_keyboard(lang, win.id))
        else:
            await edit_or_answer(msg, final_text, get_time_machine_keyboard(lang, win.id))
    except Exception:
        logger.warning("AI reflection failed for user %s win %s", user.id, win.id, exc_info=True)


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
        await edit_or_answer(query.message, t(lang, "only_memory"), _back_only_keyboard(lang))
        return

    days_ago = (datetime.now(timezone.utc).date() - win.created_at.date()).days
    await state.update_data(last_win_id=win.id)
    await query.answer()

    memory_text = t(lang, "memory", date=_format_date(win.created_at, lang), text=win.raw_text, days=days_ago)
    stickers_enabled = getattr(user, "stickers_enabled", False)
    chat_id = query.message.chat.id
    msg = await edit_or_answer(query.message, memory_text, get_time_machine_keyboard(lang, win.id))

    try:
        async with ChatActionSender.typing(bot=bot, chat_id=chat_id):
            reflection = await ask_reflect(user.tone, win.raw_text, days_ago, lang)
        final_text = f"{memory_text}\n\n{reflection}"
        if stickers_enabled:
            await try_delete(msg)
            await send_random_sticker(bot, chat_id, settings.STICKER_SET_NAME, True)
            await bot.send_message(chat_id, final_text, reply_markup=get_time_machine_keyboard(lang, win.id))
        else:
            await edit_or_answer(msg, final_text, get_time_machine_keyboard(lang, win.id))
    except Exception:
        logger.warning("AI reflection failed for user %s win %s", user.id, win.id, exc_info=True)


@router.callback_query(F.data.startswith("then:edit:"))
async def edit_memory(query: CallbackQuery, state: FSMContext, session) -> None:
    try:
        win_id = int(query.data.split(":", 2)[2])
    except ValueError:
        await query.answer()
        return
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    win = await session.scalar(select(Win).filter_by(id=win_id, user_id=user.id))
    if win is None:
        await query.answer(t(lang, "no_text_to_save"), show_alert=True)
        return
    await query.answer()
    sent = await edit_or_answer(query.message, t(lang, "win_edit_new_text"))
    await state.update_data(editing_win_id=win_id, bot_msg_id=sent.message_id)
    await state.set_state(TimeMachineEditStates.editing)


@router.message(StateFilter(TimeMachineEditStates.editing), F.text)
async def save_edited_memory(message: Message, state: FSMContext, session) -> None:
    user = await session.scalar(select(User).filter_by(tg_id=message.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    data = await state.get_data()
    win_id = data.get("editing_win_id")
    msg_id = data.get("bot_msg_id")
    new_text = message.text.strip()
    if len(new_text) > 2000:
        sent = await edit_stored(message.bot, message.chat.id, msg_id, t(lang, "input_too_long"))
        await state.update_data(bot_msg_id=sent.message_id)
        return
    win = await session.scalar(select(Win).filter_by(id=win_id, user_id=user.id))
    if win is None:
        await edit_stored(message.bot, message.chat.id, msg_id, t(lang, "no_text_to_save"))
        await state.clear()
        return
    win.raw_text = new_text
    win.processed_text = new_text
    await session.commit()
    await state.clear()
    await edit_stored(message.bot, message.chat.id, msg_id, t(lang, "win_edited"), _after_edit_keyboard(lang))


@router.callback_query(F.data.startswith("then:delete:") & ~F.data.startswith("then:delete:confirm:"))
async def delete_memory_confirm(query: CallbackQuery, session) -> None:
    try:
        win_id = int(query.data.split(":", 2)[2])
    except ValueError:
        await query.answer()
        return
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "btn_delete_confirm"), callback_data=f"then:delete:confirm:{win_id}"),
         InlineKeyboardButton(text=t(lang, "btn_cancel"), callback_data="then:back")],
    ])
    await query.answer()
    await edit_or_answer(query.message, t(lang, "win_delete_confirm"), keyboard)


@router.callback_query(F.data.startswith("then:delete:confirm:"))
async def delete_memory(query: CallbackQuery, state: FSMContext, session) -> None:
    try:
        win_id = int(query.data.split(":", 3)[3])
    except ValueError:
        await query.answer()
        return
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    win = await session.scalar(select(Win).filter_by(id=win_id, user_id=user.id))
    if win:
        await session.delete(win)
        await session.commit()
    await state.update_data(last_win_id=None)
    await query.answer()
    await edit_or_answer(query.message, t(lang, "win_deleted"), _after_edit_keyboard(lang))


@router.callback_query(F.data == "then:back")
async def time_machine_back(query: CallbackQuery, state: FSMContext, session) -> None:
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    await state.clear()
    await query.answer()
    await edit_or_answer(query.message, t(lang, "main_menu"), get_main_menu_keyboard(lang))
