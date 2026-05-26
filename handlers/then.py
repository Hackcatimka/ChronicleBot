import random
from datetime import datetime, timedelta

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import select

from ai import ask_reflect
from db.models import User, Win
from keyboards import get_main_menu_keyboard

router = Router()


def get_time_machine_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎲 Show another", callback_data="then:another")],
        [InlineKeyboardButton(text="← Back", callback_data="then:back")],
    ])


def _format_date(dt: datetime) -> str:
    return dt.strftime("%d %b %Y")


async def _get_user_and_old_win_ids(query: CallbackQuery, session):
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    if user is None:
        return None, []

    cutoff = datetime.utcnow() - timedelta(days=7)
    ids = await session.scalars(
        select(Win.id).filter(Win.user_id == user.id, Win.created_at < cutoff)
    )
    return user, ids.all()


async def _fetch_win_by_id(session, win_id: int):
    return await session.scalar(select(Win).filter_by(id=win_id))


async def _select_random_old_win(session, query: CallbackQuery, exclude_id: int | None = None):
    user, ids = await _get_user_and_old_win_ids(query, session)
    if user is None:
        return None, None, None

    available_ids = [win_id for win_id in ids if win_id != exclude_id]
    if not available_ids:
        return user, None, ids

    selected_id = random.choice(available_ids)
    win = await _fetch_win_by_id(session, selected_id)
    return user, win, ids


@router.callback_query(F.data == "menu:time_machine")
async def show_time_machine(query: CallbackQuery, state: FSMContext, session) -> None:
    user, ids = await _get_user_and_old_win_ids(query, session)
    if user is None:
        await query.answer("Пользователь не найден. Запусти /start.", show_alert=True)
        return

    if not ids:
        await query.answer()
        await query.message.answer(
            "⏪ Time machine\n\nNo memories yet. Keep recording your wins —\nin a week I'll have something to show you.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="← Back", callback_data="then:back")]]),
        )
        return

    win_id = random.choice(ids)
    win = await _fetch_win_by_id(session, win_id)
    if win is None:
        await query.answer("Ошибка при выборе памяти.", show_alert=True)
        return

    days_ago = (datetime.utcnow().date() - win.created_at.date()).days
    await state.update_data(last_win_id=win.id)
    await query.answer()
    try:
        reflection = await ask_reflect(user.tone, win.raw_text, days_ago)
        await query.message.answer(reflection, reply_markup=get_time_machine_keyboard())
    except Exception:
        await query.message.answer(
            f"⏪ Time machine\n\nOn {_format_date(win.created_at)} you wrote:\n\n\"{win.raw_text}\"\n\nThat was {days_ago} days ago.",
            reply_markup=get_time_machine_keyboard(),
        )


@router.callback_query(F.data == "then:another")
async def show_another(query: CallbackQuery, state: FSMContext, session) -> None:
    data = await state.get_data()
    last_win_id = data.get("last_win_id")
    user, win, ids = await _select_random_old_win(session, query, exclude_id=last_win_id)
    if user is None:
        await query.answer("Пользователь не найден. Запусти /start.", show_alert=True)
        await state.clear()
        return

    if win is None:
        await query.answer()
        await query.message.answer(
            "That's the only memory I have so far. Keep going! 🏆",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="← Back", callback_data="then:back")]]),
        )
        return

    days_ago = (datetime.utcnow().date() - win.created_at.date()).days
    await state.update_data(last_win_id=win.id)
    await query.answer()
    try:
        reflection = await ask_reflect(user.tone, win.raw_text, days_ago)
        await query.message.answer(reflection, reply_markup=get_time_machine_keyboard())
    except Exception:
        await query.message.answer(
            f"⏪ Time machine\n\nOn {_format_date(win.created_at)} you wrote:\n\n\"{win.raw_text}\"\n\nThat was {days_ago} days ago.",
            reply_markup=get_time_machine_keyboard(),
        )


@router.callback_query(F.data == "then:back")
async def time_machine_back(query: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await query.answer()
    await query.message.answer("Главное меню", reply_markup=get_main_menu_keyboard())
