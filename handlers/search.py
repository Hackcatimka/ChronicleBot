import logging

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from db.models import User, Win
from keyboards import get_main_menu_keyboard, get_search_results_keyboard
from locales import t
from utils import edit_or_answer, edit_stored

router = Router()
logger = logging.getLogger(__name__)

_PAGE_SIZE = 5


class SearchStates(StatesGroup):
    waiting_for_query = State()


def _format_results(wins: list[Win], query_text: str, total: int, offset: int, lang: str) -> str:
    lines = [t(lang, "search_results", query=query_text, count=total), ""]
    for win in wins:
        date_str = win.created_at.strftime("%d %b %Y")
        lines.append(f"— {date_str}: {win.raw_text}")
    end = offset + len(wins)
    lines += ["", t(lang, "search_showing", start=offset + 1, end=end, total=total)]
    return "\n".join(lines)


@router.callback_query(F.data == "menu:search")
async def start_search(query: CallbackQuery, state: FSMContext, session) -> None:
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    await state.set_state(SearchStates.waiting_for_query)
    await query.answer()
    msg = await edit_or_answer(query.message, t(lang, "search_prompt"))
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
        keyboard = get_search_results_keyboard(lang, total > _PAGE_SIZE)

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
    await edit_or_answer(query.message, text, get_search_results_keyboard(lang, has_more))
    await state.update_data(offset=offset + _PAGE_SIZE)


@router.callback_query(F.data == "search:back")
async def search_back(query: CallbackQuery, state: FSMContext, session) -> None:
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    await state.clear()
    await query.answer()
    await edit_or_answer(query.message, t(lang, "main_menu"), get_main_menu_keyboard(lang))
