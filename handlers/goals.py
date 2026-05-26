from datetime import datetime

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy import select

from db.models import Goal, User, Win, WinGoal
from keyboards import get_main_menu_keyboard

router = Router()


class AddGoalStates(StatesGroup):
    title = State()
    deadline = State()
    category = State()


def _format_date(dt: datetime | None) -> str:
    return dt.strftime("%d %b %Y") if dt else "no deadline"


def _build_goals_keyboard(has_goals: bool) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="➕ Add goal", callback_data="goals:add")],
    ]
    if has_goals:
        buttons.append([InlineKeyboardButton(text="📋 Goal details", callback_data="goals:list")])
    buttons.append([InlineKeyboardButton(text="← Back", callback_data="goals:back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def _build_goal_list_keyboard(goals: list[Goal]) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=f"🎯 {goal.title}", callback_data=f"goal:view:{goal.id}")]
        for goal in goals
    ]
    buttons.append([InlineKeyboardButton(text="← Back", callback_data="goals:back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def _build_goal_detail_buttons(goal_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Mark as done", callback_data=f"goal:done:{goal_id}"),
         InlineKeyboardButton(text="🗑 Abandon", callback_data=f"goal:abandon:{goal_id}")],
        [InlineKeyboardButton(text="← Back", callback_data="goals:list")],
    ])


def _build_abandon_confirm_buttons(goal_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Yes, abandon", callback_data=f"goal:abandon:confirm:{goal_id}"),
         InlineKeyboardButton(text="❌ Keep it", callback_data=f"goal:abandon:cancel:{goal_id}")],
    ])


def _build_category_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Career", callback_data="goals:category:Career"),
         InlineKeyboardButton(text="Learning", callback_data="goals:category:Learning")],
        [InlineKeyboardButton(text="Health", callback_data="goals:category:Health")],
        [InlineKeyboardButton(text="Personal", callback_data="goals:category:Personal"),
         InlineKeyboardButton(text="Other", callback_data="goals:category:Other")],
        [InlineKeyboardButton(text="Skip", callback_data="goals:category:Skip")],
    ])


async def _get_active_goals(user_id: int, session):
    goals = await session.scalars(select(Goal).filter_by(user_id=user_id, status="active").order_by(Goal.created_at))
    return goals.all()


def _render_goals_list(goals: list[Goal]) -> str:
    lines = ["🎯 My goals", ""]
    for idx, goal in enumerate(goals, start=1):
        deadline = _format_date(goal.deadline)
        lines.append(f"{idx}. {goal.title} — {deadline}")
    return "\n".join(lines)


@router.callback_query(F.data == "menu:goals")
async def show_goals_menu(query: CallbackQuery, session) -> None:
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    if user is None:
        await query.answer("Пользователь не найден. Запусти /start.", show_alert=True)
        return

    goals = await _get_active_goals(user.id, session)
    await query.answer()
    if not goals:
        await query.message.answer(
            "🎯 My goals\n\nNo goals yet. Let's set one!",
            reply_markup=_build_goals_keyboard(False),
        )
        return

    await query.message.answer(_render_goals_list(goals), reply_markup=_build_goals_keyboard(True))


@router.callback_query(F.data == "goals:add")
async def add_goal_start(query: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AddGoalStates.title)
    await state.update_data({})
    await query.answer()
    await query.message.answer("Напиши название цели")


@router.message(StateFilter(AddGoalStates.title), F.text)
async def add_goal_title(message: Message, state: FSMContext) -> None:
    await state.update_data(title=message.text.strip())
    await state.set_state(AddGoalStates.deadline)
    await message.answer("Добавить дедлайн? Напиши дату в формате DD.MM.YYYY или напиши \"нет\"")


@router.message(StateFilter(AddGoalStates.deadline), F.text)
async def add_goal_deadline(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    if text.lower() == "нет":
        deadline = None
    else:
        try:
            deadline = datetime.strptime(text, "%d.%m.%Y").date()
        except ValueError:
            await message.answer("Неверный формат даты. Напиши в формате DD.MM.YYYY или \"нет\"")
            return

    await state.update_data(deadline=deadline)
    await state.set_state(AddGoalStates.category)
    await message.answer("К какой категории относится? Напиши или выбери:", reply_markup=_build_category_keyboard())


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
    if category == "Skip":
        category_value = None
    else:
        category_value = category

    await state.update_data(category=category_value)
    await query.answer()
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    if user is None:
        await query.answer("Пользователь не найден. Запусти /start.", show_alert=True)
        await state.clear()
        return

    await _save_goal_from_state(user, state, session)
    await state.clear()
    goals = await _get_active_goals(user.id, session)
    await query.message.answer(_render_goals_list(goals), reply_markup=_build_goals_keyboard(True))


@router.message(StateFilter(AddGoalStates.category), F.text)
async def add_goal_category_text(message: Message, state: FSMContext, session) -> None:
    category_value = message.text.strip()
    if not category_value:
        await message.answer("Напиши категорию или выбери одну из кнопок.")
        return

    await state.update_data(category=category_value)
    user = await session.scalar(select(User).filter_by(tg_id=message.from_user.id))
    if user is None:
        await message.answer("Пользователь не найден. Запусти /start.")
        await state.clear()
        return

    await _save_goal_from_state(user, state, session)
    await state.clear()
    goals = await _get_active_goals(user.id, session)
    await message.answer(_render_goals_list(goals), reply_markup=_build_goals_keyboard(True))


@router.callback_query(F.data == "goals:list")
async def list_goals(query: CallbackQuery, session) -> None:
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    if user is None:
        await query.answer("Пользователь не найден. Запусти /start.", show_alert=True)
        return

    goals = await _get_active_goals(user.id, session)
    if not goals:
        await query.answer()
        await query.message.answer("No goals yet. Let's set one!", reply_markup=_build_goals_keyboard(False))
        return

    await query.answer()
    await query.message.answer("🎯 Choose a goal:", reply_markup=_build_goal_list_keyboard(goals))


@router.callback_query(F.data == "goals:back")
async def goals_back(query: CallbackQuery) -> None:
    await query.answer()
    await query.message.answer("Главное меню", reply_markup=get_main_menu_keyboard())


@router.callback_query(F.data.startswith("goal:view:"))
async def view_goal(query: CallbackQuery, session) -> None:
    goal_id = int(query.data.split(":", 2)[2])
    goal = await session.scalar(select(Goal).filter_by(id=goal_id, status="active"))
    if goal is None:
        await query.answer("Goal not found.", show_alert=True)
        return

    wins = goal.wins
    lines = [
        f"🎯 {goal.title}",
        "",
        f"Category: {goal.category or 'None'}",
        f"Deadline: {_format_date(goal.deadline)}",
        f"Status: {goal.status.capitalize()}",
        "",
        "Wins linked to this goal:",
    ]
    if wins:
        for win in wins:
            lines.append(f"— {win.raw_text} ({win.created_at.strftime('%d %b')})")
    else:
        lines.append("No wins linked yet.")

    await query.answer()
    await query.message.answer("\n".join(lines), reply_markup=_build_goal_detail_buttons(goal.id))


@router.callback_query(F.data.startswith("goal:done:"))
async def complete_goal(query: CallbackQuery, session) -> None:
    goal_id = int(query.data.split(":", 2)[2])
    goal = await session.scalar(select(Goal).filter_by(id=goal_id, status="active"))
    if goal is None:
        await query.answer("Goal not found.", show_alert=True)
        return

    goal.status = "done"
    await session.commit()
    days = (datetime.utcnow().date() - goal.created_at.date()).days
    await query.answer()
    await query.message.answer(
        f"🏆 Goal completed!\n\n\"{goal.title}\" is done.\nThat took {days} days from start to finish."
    )

    user = await session.scalar(select(User).filter_by(id=goal.user_id))
    if user is None:
        return
    goals = await _get_active_goals(user.id, session)
    if goals:
        await query.message.answer(_render_goals_list(goals), reply_markup=_build_goals_keyboard(True))
    else:
        await query.message.answer("🎯 My goals\n\nNo goals yet. Let's set one!", reply_markup=_build_goals_keyboard(False))


@router.callback_query(F.data.startswith("goal:abandon:confirm:"))
async def confirm_abandon_goal(query: CallbackQuery, session) -> None:
    goal_id = int(query.data.split(":", 3)[3])
    goal = await session.scalar(select(Goal).filter_by(id=goal_id, status="active"))


@router.callback_query(F.data.startswith("goal:abandon:cancel:"))
async def cancel_abandon_goal(query: CallbackQuery, session) -> None:
    goal_id = int(query.data.split(":", 3)[3])
    goal = await session.scalar(select(Goal).filter_by(id=goal_id, status="active"))
    if goal is None:
        await query.answer("Goal not found.", show_alert=True)
        return

    await query.answer()
    await query.message.answer("Abandon cancelled.")
    await query.message.answer("🎯 Choose a goal:", reply_markup=_build_goal_list_keyboard([goal]))


@router.callback_query(F.data.startswith("goal:abandon:"))
async def abandon_goal(query: CallbackQuery, session) -> None:
    goal_id = int(query.data.split(":", 2)[2])
    await query.answer()
    await query.message.answer(
        "Are you sure you want to abandon this goal?",
        reply_markup=_build_abandon_confirm_buttons(goal_id),
    )
    if goal is None:
        await query.answer("Goal not found.", show_alert=True)
        return

    goal.status = "abandoned"
    await session.commit()
    await query.answer()
    await query.message.answer("Goal abandoned.")

    user = await session.scalar(select(User).filter_by(id=goal.user_id))
    if user is None:
        return
    goals = await _get_active_goals(user.id, session)
    if goals:
        await query.message.answer(_render_goals_list(goals), reply_markup=_build_goals_keyboard(True))
    else:
        await query.message.answer("🎯 My goals\n\nNo goals yet. Let's set one!", reply_markup=_build_goals_keyboard(False))


@router.callback_query(F.data.startswith("goal:abandon:cancel:"))
async def cancel_abandon_goal(query: CallbackQuery, session) -> None:
    goal_id = int(query.data.split(":", 3)[3])
    goal = await session.scalar(select(Goal).filter_by(id=goal_id, status="active"))
    if goal is None:
        await query.answer("Goal not found.", show_alert=True)
        return

    await query.answer()
    await query.message.answer("Abandon cancelled.")
    await query.message.answer("🎯 Choose a goal:", reply_markup=_build_goal_list_keyboard([goal]))
