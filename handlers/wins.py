from datetime import datetime

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy import func, select

from ai import ask_praise
from db.models import Goal, User, Win, WinGoal
from keyboards import get_main_menu_keyboard, get_win_confirmation_keyboard

router = Router()


class WinStates(StatesGroup):
    waiting_for_confirmation = State()
    waiting_for_goal = State()


async def _show_main_menu(message: Message, session) -> None:
    await message.answer("Главное меню", reply_markup=get_main_menu_keyboard())


@router.message(F.text, ~StateFilter(WinStates.waiting_for_confirmation))
async def request_win_text(message: Message, state: FSMContext, session) -> None:
    if message.text is None or message.text.startswith("/"):
        return

    user = await session.scalar(select(User).filter_by(tg_id=message.from_user.id))
    if user is None:
        await message.answer("Пожалуйста, начни с /start.")
        return

    await state.update_data(raw_text=message.text)
    await state.set_state(WinStates.waiting_for_confirmation)

    user.last_active_at = datetime.utcnow()
    session.add(user)
    await session.commit()

    await message.answer(
        f"Вот что я получил:\n\n{message.text}",
        reply_markup=get_win_confirmation_keyboard(),
    )


@router.callback_query(F.data == "save_win")
async def save_win(query: CallbackQuery, state: FSMContext, session) -> None:
    data = await state.get_data()
    raw_text = data.get("raw_text")
    if not raw_text:
        await query.answer("Нет текста для сохранения.", show_alert=True)
        return

    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    if user is None:
        await query.answer("Пользователь не найден. Запусти /start.", show_alert=True)
        return

    win = Win(user_id=user.id, raw_text=raw_text, processed_text=raw_text)
    session.add(win)
    user.last_active_at = datetime.utcnow()
    session.add(user)
    await session.commit()

    count = await session.scalar(select(func.count()).select_from(Win).filter_by(user_id=user.id))
    await query.answer()
    try:
        praise = await ask_praise(user.tone, raw_text, count)
        await query.message.answer(praise)
    except Exception:
        tone_reply = {
            "friend": f"Saved! 🎉 That's win #{count}. Keep going!",
            "coach": f"Logged. #{count} total. What made this possible?",
            "mirror": f"Win #{count} recorded.",
        }
        await query.message.answer(tone_reply.get(user.tone, f"Win #{count} recorded."))
    await query.message.answer("Возвращаемся в главное меню:", reply_markup=get_main_menu_keyboard())
    await state.clear()


@router.callback_query(F.data == "edit_win")
async def edit_win(query: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await query.answer()
    await query.message.answer("Хорошо, напиши победу заново.")


@router.callback_query(F.data == "cancel_win")
async def cancel_win(query: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await query.answer()
    await query.message.answer("Ок, отменено. Главное меню:", reply_markup=get_main_menu_keyboard())


@router.callback_query(F.data == "link_goal")
async def link_goal(query: CallbackQuery, state: FSMContext, session) -> None:
    data = await state.get_data()
    raw_text = data.get("raw_text")
    if not raw_text:
        await query.answer("Нет текста для привязки.", show_alert=True)
        return

    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    if user is None:
        await query.answer("Пользователь не найден. Запусти /start.", show_alert=True)
        return

    goals = await session.scalars(select(Goal).filter_by(user_id=user.id, status="active"))
    goals = goals.all()
    if not goals:
        await query.answer()
        await query.message.answer("Сначала создай цель в разделе My goals")
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
    buttons.append([InlineKeyboardButton(text="← Back", callback_data="cancel_win")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await query.answer()
    await query.message.answer("Выбери цель для этой победы:", reply_markup=keyboard)


@router.callback_query(F.data.startswith("win:link:"), StateFilter(WinStates.waiting_for_goal))
async def link_win_to_goal(query: CallbackQuery, state: FSMContext, session) -> None:
    goal_id = int(query.data.split(":", 2)[2])
    data = await state.get_data()
    win_id = data.get("win_id")
    if not win_id:
        await query.answer("Нет сохранённой победы для привязки.", show_alert=True)
        await state.clear()
        return

    goal = await session.scalar(select(Goal).filter_by(id=goal_id, user_id=query.from_user.id, status="active"))
    if goal is None:
        await query.answer("Цель не найдена.", show_alert=True)
        await state.clear()
        return

    existing = await session.scalar(select(WinGoal).filter_by(win_id=win_id, goal_id=goal.id))
    if existing is None:
        link = WinGoal(win_id=win_id, goal_id=goal.id)
        session.add(link)
        await session.commit()

    await query.answer()
    await query.message.answer("Победа привязана к цели.")
    await query.message.answer("Возвращаемся в главное меню:", reply_markup=get_main_menu_keyboard())
    await state.clear()


@router.callback_query(F.data.startswith("menu:"))
async def main_menu_handler(query: CallbackQuery, state: FSMContext) -> None:
    action = query.data.split(":", 1)[1]
    await query.answer()

    if action == "record_win":
        await state.clear()
        await query.message.answer("Отправь текст своей победы, и я помогу сохранить её.")
        return

    await query.message.answer("Coming soon.")
