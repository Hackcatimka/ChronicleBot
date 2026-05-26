from datetime import datetime, timezone

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from db.models import Goal, User
from keyboards import (
    get_main_menu_keyboard,
    get_goal_list_keyboard,
    get_goal_detail_buttons,
    get_goal_menu_keyboard,
    get_category_keyboard,
    get_abandon_confirm_buttons,
)
from locales import t

router = Router()


class AddGoalStates(StatesGroup):
    title = State()
    deadline = State()
    category = State()


def _format_date(dt: datetime | None, lang: str) -> str:
    if dt:
        return dt.strftime("%d %b %Y")
    return t(lang, "goal_no_deadline")


async def _get_active_goals(user_id: int, session):
    goals = await session.scalars(
        select(Goal).filter_by(user_id=user_id, status="active").order_by(Goal.created_at)
    )
    return goals.all()


def _render_goals_list(goals: list[Goal], lang: str) -> str:
    if not goals:
        return t(lang, "goal_list_empty")

    lines = [t(lang, "goal_list_title"), ""]
    for idx, goal in enumerate(goals, start=1):
        deadline = _format_date(goal.deadline, lang)
        lines.append(f"{idx}. {goal.title} — {deadline}")
    return "\n".join(lines)


@router.callback_query(F.data == "menu:goals")
async def show_goals_menu(query: CallbackQuery, session) -> None:
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    if user is None:
        await query.answer(t(lang, "user_not_found"), show_alert=True)
        return

    goals = await _get_active_goals(user.id, session)
    await query.answer()
    await query.message.answer(
        _render_goals_list(goals, lang),
        reply_markup=get_goal_menu_keyboard(lang, bool(goals)),
    )


@router.callback_query(F.data == "goals:add")
async def add_goal_start(query: CallbackQuery, state: FSMContext, session) -> None:
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    await state.set_state(AddGoalStates.title)
    await state.update_data({})
    await query.answer()
    await query.message.answer(t(lang, "goal_title_prompt"))


@router.message(StateFilter(AddGoalStates.title), F.text)
async def add_goal_title(message: Message, state: FSMContext, session) -> None:
    user = await session.scalar(select(User).filter_by(tg_id=message.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    await state.update_data(title=message.text.strip())
    await state.set_state(AddGoalStates.deadline)
    await message.answer(t(lang, "goal_deadline_prompt"))


@router.message(StateFilter(AddGoalStates.deadline), F.text)
async def add_goal_deadline(message: Message, state: FSMContext, session) -> None:
    text = message.text.strip()
    if text.lower() == "нет" or text.lower() == "no":
        deadline = None
    else:
        try:
            deadline = datetime.strptime(text, "%d.%m.%Y").date()
        except ValueError:
            user = await session.scalar(select(User).filter_by(tg_id=message.from_user.id))
            lang = getattr(user, "language", "en") if user else "en"
            await message.answer(t(lang, "goal_deadline_invalid"))
            return

    user = await session.scalar(select(User).filter_by(tg_id=message.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    await state.update_data(deadline=deadline)
    await state.set_state(AddGoalStates.category)
    await message.answer(t(lang, "goal_category_prompt"), reply_markup=get_category_keyboard(lang))


async def _save_goal_from_state(user: User, state: FSMContext, session) -> Goal:
    data = await state.get_data()
    title = data.get("title")
    deadline = data.get("deadline")
    category = data.get("category")
    goal = Goal(user_id=user.id, title=title, deadline=deadline, category=category, status="active")
    session.add(goal)
    await session.commit()
    return goal


@router.callback_query(F.data.startswith("goals:category:"))
async def add_goal_category_button(query: CallbackQuery, state: FSMContext, session) -> None:
    category = query.data.split(":", 2)[2]
    category_value = None if category == "Skip" else category

    await state.update_data(category=category_value)
    await query.answer()
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    if user is None:
        await query.answer(t(lang, "user_not_found"), show_alert=True)
        await state.clear()
        return

    await _save_goal_from_state(user, state, session)
    await state.clear()
    goals = await _get_active_goals(user.id, session)
    await query.message.answer(
        _render_goals_list(goals, lang),
        reply_markup=get_goal_menu_keyboard(lang, True),
    )


@router.message(StateFilter(AddGoalStates.category), F.text)
async def add_goal_category_text(message: Message, state: FSMContext, session) -> None:
    category_value = message.text.strip()
    user = await session.scalar(select(User).filter_by(tg_id=message.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    if not category_value:
        await message.answer(t(lang, "goal_category_invalid"))
        return

    await state.update_data(category=category_value)
    user = await session.scalar(select(User).filter_by(tg_id=message.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    if user is None:
        await message.answer(t(lang, "user_not_found"))
        await state.clear()
        return

    await _save_goal_from_state(user, state, session)
    await state.clear()
    goals = await _get_active_goals(user.id, session)
    await message.answer(
        _render_goals_list(goals, lang),
        reply_markup=get_goal_menu_keyboard(lang, True),
    )


@router.callback_query(F.data == "goals:list")
async def list_goals(query: CallbackQuery, session) -> None:
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    if user is None:
        await query.answer(t(lang, "user_not_found"), show_alert=True)
        return

    goals = await _get_active_goals(user.id, session)
    if not goals:
        await query.answer()
        await query.message.answer(
            t(lang, "goal_list_empty"),
            reply_markup=get_goal_menu_keyboard(lang, False),
        )
        return

    await query.answer()
    await query.message.answer(t(lang, "goal_choose"), reply_markup=get_goal_list_keyboard(lang, goals))


@router.callback_query(F.data == "goals:back")
async def goals_back(query: CallbackQuery, session) -> None:
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    await query.answer()
    await query.message.answer(t(lang, "back_to_menu"), reply_markup=get_main_menu_keyboard(lang))


@router.callback_query(F.data.startswith("goal:view:"))
async def view_goal(query: CallbackQuery, session) -> None:
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    goal_id = int(query.data.split(":", 2)[2])
    goal = await session.scalar(select(Goal).filter_by(id=goal_id, status="active"))
    if goal is None:
        await query.answer(t(lang, "goal_not_found"), show_alert=True)
        return

    wins = goal.wins
    lines = [
        t(lang, "goal_view_header", title=goal.title),
        "",
        t(lang, "goal_view_category", category=goal.category or t(lang, "goal_no_category")),
        t(lang, "goal_view_deadline", deadline=_format_date(goal.deadline, lang)),
        t(lang, "goal_view_status", status=goal.status.capitalize()),
        "",
        t(lang, "goal_view_wins"),
    ]
    if wins:
        for win in wins:
            lines.append(f"— {win.raw_text} ({win.created_at.strftime('%d %b')})")
    else:
        lines.append(t(lang, "goal_view_no_wins"))

    await query.answer()
    await query.message.answer("\n".join(lines), reply_markup=get_goal_detail_buttons(lang, goal.id))


@router.callback_query(F.data.startswith("goal:done:"))
async def complete_goal(query: CallbackQuery, session) -> None:
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    goal_id = int(query.data.split(":", 2)[2])
    goal = await session.scalar(select(Goal).filter_by(id=goal_id, status="active"))
    if goal is None:
        await query.answer(t(lang, "goal_not_found"), show_alert=True)
        return

    goal.status = "done"
    await session.commit()
    days = (datetime.now(timezone.utc).date() - goal.created_at.date()).days
    await query.answer()
    await query.message.answer(t(lang, "goal_done", title=goal.title, days=days))

    goals = await _get_active_goals(user.id, session)
    await query.message.answer(
        _render_goals_list(goals, lang),
        reply_markup=get_goal_menu_keyboard(lang, bool(goals)),
    )


@router.callback_query(F.data.startswith("goal:abandon:"))
async def abandon_goal(query: CallbackQuery, session) -> None:
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    goal_id = int(query.data.split(":", 2)[2])
    goal = await session.scalar(select(Goal).filter_by(id=goal_id, status="active"))
    if goal is None:
        await query.answer(t(lang, "goal_not_found"), show_alert=True)
        return

    await query.answer()
    await query.message.answer(
        t(lang, "goal_abandon_confirm"),
        reply_markup=get_abandon_confirm_buttons(lang, goal_id),
    )


@router.callback_query(F.data.startswith("goal:abandon:confirm:"))
async def confirm_abandon_goal(query: CallbackQuery, session) -> None:
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    goal_id = int(query.data.split(":", 3)[3])
    goal = await session.scalar(select(Goal).filter_by(id=goal_id, status="active"))
    if goal is None:
        await query.answer(t(lang, "goal_not_found"), show_alert=True)
        return

    goal.status = "abandoned"
    await session.commit()
    await query.answer()
    await query.message.answer(t(lang, "goal_abandoned"))

    goals = await _get_active_goals(user.id, session)
    await query.message.answer(
        _render_goals_list(goals, lang),
        reply_markup=get_goal_menu_keyboard(lang, bool(goals)),
    )


@router.callback_query(F.data.startswith("goal:abandon:cancel:"))
async def cancel_abandon_goal(query: CallbackQuery, session) -> None:
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    goal_id = int(query.data.split(":", 3)[3])
    goal = await session.scalar(select(Goal).filter_by(id=goal_id, status="active"))
    if goal is None:
        await query.answer(t(lang, "goal_not_found"), show_alert=True)
        return

    await query.answer()
    await query.message.answer(t(lang, "goal_abandon_cancelled"))
    await query.message.answer(t(lang, "goal_choose"), reply_markup=get_goal_list_keyboard(lang, [goal]))
