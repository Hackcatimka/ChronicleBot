import logging

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy import select

from db.models import User, Win
from keyboards import (get_main_menu_keyboard, get_search_after_edit_keyboard, get_search_all_keyboard,
                       get_search_moment_keyboard, get_search_prompt_keyboard, get_search_results_keyboard)
from locales import t
from utils import edit_or_answer, edit_stored, format_date

router = Router()
logger = logging.getLogger(__name__)

_PAGE_SIZE = 5


class SearchStates(StatesGroup):
    waiting_for_query = State()
    editing = State()


def _format_results(wins: list[Win], query_text: str, total: int, offset: int, lang: str) -> str:
    lines = [t(lang, "search_results", query=query_text, count=total), ""]
    for i, win in enumerate(wins, start=1):
        date_str = format_date(win.created_at, lang)
        lines.append(f"{i}. {date_str} — {win.raw_text}")
    end = offset + len(wins)
    lines += ["", t(lang, "search_showing", start=offset + 1, end=end, total=total)]
    return "\n".join(lines)


@router.callback_query(F.data == "menu:search")
async def start_search(query: CallbackQuery, state: FSMContext, session) -> None:
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    await state.set_state(SearchStates.waiting_for_query)
    await query.answer()
    msg = await edit_or_answer(query.message, t(lang, "search_prompt"), get_search_prompt_keyboard(lang))
    await state.update_data(chat_id=query.message.chat.id, bot_msg_id=msg.message_id, lang=lang)


@router.message(StateFilter(SearchStates.waiting_for_query), F.text)
async def handle_search_query(message: Message, state: FSMContext, session) -> None:
    data = await state.get_data()
    msg_id = data.get("bot_msg_id")
    chat_id = data.get("chat_id")
    user = await session.scalar(select(User).filter_by(tg_id=message.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"

    query_text = message.text.strip()
    if not query_text:
        return

    wins = (await session.scalars(
        select(Win)
        .filter(Win.user_id == user.id, Win.raw_text.ilike(f"%{query_text}%"))
        .order_by(Win.created_at.desc())
    )).all()

    total = len(wins)
    page = wins[:_PAGE_SIZE]

    if not page:
        text = t(lang, "search_no_results", query=query_text)
        keyboard = get_search_results_keyboard(lang, False)
    else:
        text = _format_results(page, query_text, total, 0, lang)
        keyboard = get_search_results_keyboard(lang, total > _PAGE_SIZE, [w.id for w in page])

    sent = await edit_stored(message.bot, chat_id, msg_id, text, keyboard)
    await state.update_data(bot_msg_id=sent.message_id, query=query_text, offset=_PAGE_SIZE)


@router.callback_query(F.data == "search:more", StateFilter(SearchStates.waiting_for_query))
async def load_more_results(query: CallbackQuery, state: FSMContext, session) -> None:
    data = await state.get_data()
    query_text = data.get("query", "")
    offset = data.get("offset", _PAGE_SIZE)
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"

    wins = (await session.scalars(
        select(Win)
        .filter(Win.user_id == user.id, Win.raw_text.ilike(f"%{query_text}%"))
        .order_by(Win.created_at.desc())
    )).all()

    total = len(wins)
    page = wins[offset:offset + _PAGE_SIZE]
    has_more = offset + _PAGE_SIZE < total

    text = _format_results(page, query_text, total, offset, lang)
    await query.answer()
    await edit_or_answer(query.message, text, get_search_results_keyboard(lang, has_more, [w.id for w in page]))
    await state.update_data(offset=offset + _PAGE_SIZE)


def _format_all_moments(wins: list[Win], total: int, offset: int, lang: str) -> str:
    lines = [t(lang, "search_all_title", total=total), ""]
    for i, win in enumerate(wins, start=1):
        date_str = format_date(win.created_at, lang)
        lines.append(f"{i}. {date_str} — {win.raw_text}")
    end = offset + len(wins)
    lines += ["", t(lang, "search_showing", start=offset + 1, end=end, total=total)]
    return "\n".join(lines)


@router.callback_query(F.data == "search:all")
async def show_all_moments(query: CallbackQuery, state: FSMContext, session) -> None:
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    if user is None:
        await query.answer()
        return

    wins = (await session.scalars(
        select(Win).filter_by(user_id=user.id).order_by(Win.created_at.desc())
    )).all()

    total = len(wins)
    await query.answer()

    if not wins:
        await edit_or_answer(query.message, t(lang, "search_all_empty"), get_search_all_keyboard(lang, False))
        return

    page = wins[:_PAGE_SIZE]
    has_more = total > _PAGE_SIZE
    await edit_or_answer(query.message, _format_all_moments(page, total, 0, lang), get_search_all_keyboard(lang, has_more, [w.id for w in page]))
    await state.update_data(all_offset=_PAGE_SIZE)


@router.callback_query(F.data == "search:all:more")
async def load_more_all_moments(query: CallbackQuery, state: FSMContext, session) -> None:
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    data = await state.get_data()
    offset = data.get("all_offset", _PAGE_SIZE)

    wins = (await session.scalars(
        select(Win).filter_by(user_id=user.id).order_by(Win.created_at.desc())
    )).all()

    total = len(wins)
    page = wins[offset:offset + _PAGE_SIZE]
    has_more = offset + _PAGE_SIZE < total

    await query.answer()
    await edit_or_answer(query.message, _format_all_moments(page, total, offset, lang), get_search_all_keyboard(lang, has_more, [w.id for w in page]))
    await state.update_data(all_offset=offset + _PAGE_SIZE)


@router.callback_query(F.data.startswith("search:view:"))
async def view_moment(query: CallbackQuery, session) -> None:
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
    date_str = format_date(win.created_at, lang)
    text = f"📝 {date_str}\n\n{win.raw_text}"
    await query.answer()
    await edit_or_answer(query.message, text, get_search_moment_keyboard(lang, win_id))


@router.callback_query(F.data.startswith("search:edit:"))
async def edit_moment(query: CallbackQuery, state: FSMContext, session) -> None:
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
    await state.update_data(editing_win_id=win_id, bot_msg_id=sent.message_id, chat_id=query.message.chat.id)
    await state.set_state(SearchStates.editing)


@router.message(StateFilter(SearchStates.editing), F.text)
async def save_edited_moment(message: Message, state: FSMContext, session) -> None:
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
    await edit_stored(message.bot, message.chat.id, msg_id, t(lang, "win_edited"), get_search_after_edit_keyboard(lang))


@router.callback_query(F.data.startswith("search:delete:") & ~F.data.startswith("search:delete:confirm:"))
async def delete_moment_confirm(query: CallbackQuery, session) -> None:
    try:
        win_id = int(query.data.split(":", 2)[2])
    except ValueError:
        await query.answer()
        return
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    if user is None:
        await query.answer()
        return
    win = await session.scalar(select(Win).filter_by(id=win_id, user_id=user.id))
    if win is None:
        await query.answer()
        return
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "btn_delete_confirm"), callback_data=f"search:delete:confirm:{win_id}"),
         InlineKeyboardButton(text=t(lang, "btn_cancel"), callback_data="search:back")],
    ])
    await query.answer()
    await edit_or_answer(query.message, t(lang, "win_delete_confirm"), keyboard)


@router.callback_query(F.data.startswith("search:delete:confirm:"))
async def delete_moment(query: CallbackQuery, state: FSMContext, session) -> None:
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
    await state.clear()
    await query.answer()
    await edit_or_answer(query.message, t(lang, "win_deleted"), get_search_after_edit_keyboard(lang))


@router.callback_query(F.data == "search:back")
async def search_back(query: CallbackQuery, state: FSMContext, session) -> None:
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    await state.clear()
    await query.answer()
    await edit_or_answer(query.message, t(lang, "main_menu"), get_main_menu_keyboard(lang))
