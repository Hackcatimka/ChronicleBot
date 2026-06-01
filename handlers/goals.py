import logging
from datetime import datetime, timezone

from aiogram import Bot, F, Router
from ai import ask_goal_progress, suggest_goal_title
from config import settings
from ratelimit import check as rate_check
from stickers import send_random_sticker
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from aiogram.utils.chat_action import ChatActionSender
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from db.models import Goal, User, Win, WinGoal
from keyboards import (
    get_main_menu_keyboard,
    get_goal_list_keyboard,
    get_goal_detail_buttons,
    get_goal_edit_keyboard,
    get_goal_menu_keyboard,
    get_goal_suggestion_keyboard,
    get_category_keyboard,
    get_abandon_confirm_buttons,
)
from locales import t
from scheduler import remove_deadline_job, schedule_deadline_job
from utils import edit_or_answer, edit_stored, format_date, try_delete

router = Router()
logger = logging.getLogger(__name__)
_MAX_TEXT_LEN = 2000
_VALID_CATEGORIES = {"Career", "Learning", "Health", "Personal", "Other", "Skip"}


class AddGoalStates(StatesGroup):
    title = State()
    deadline = State()
    category = State()


class GoalEditStates(StatesGroup):
    title = State()
    deadline = State()
    category = State()


def _format_date(dt: datetime | None, lang: str) -> str:
    if dt is None:
        return t(lang, "goal_no_deadline")
    return format_date(dt, lang)


async def _get_active_goals(user_id: int, session):
    goals = await session.scalars(
        select(Goal).filter_by(user_id=user_id, status="active")
        .options(selectinload(Goal.wins))
        .order_by(Goal.created_at)
    )
    return goals.all()


def _render_goals_list(goals: list[Goal], lang: str) -> str:
    if not goals:
        return t(lang, "goal_list_empty")

    today = datetime.now(timezone.utc).date()
    lines = [t(lang, "goal_list_title"), ""]
    for idx, goal in enumerate(goals, start=1):
        days = (today - goal.created_at.date()).days
        win_count = len(goal.wins)
        deadline = _format_date(goal.deadline, lang)
        lines.append(f"{idx}. {goal.title}")
        lines.append(f"   {t(lang, 'goal_progress_line', count=win_count, days=days)} · {deadline}")
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
    await edit_or_answer(query.message, _render_goals_list(goals, lang), get_goal_menu_keyboard(lang, bool(goals)))


@router.callback_query(F.data == "goals:add")
async def add_goal_start(query: CallbackQuery, state: FSMContext, session) -> None:
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    await state.set_state(AddGoalStates.title)
    await query.answer()
    sent = await edit_or_answer(query.message, t(lang, "goal_title_prompt"))
    await state.update_data(bot_msg_id=sent.message_id, chat_id=sent.chat.id)


@router.message(StateFilter(AddGoalStates.title), F.text)
async def add_goal_title(message: Message, state: FSMContext, session) -> None:
    user = await session.scalar(select(User).filter_by(tg_id=message.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    data = await state.get_data()
    msg_id = data.get("bot_msg_id")
    if len(message.text) > _MAX_TEXT_LEN:
        sent = await edit_stored(message.bot, message.chat.id, msg_id, t(lang, "input_too_long"))
        await state.update_data(bot_msg_id=sent.message_id)
        return
    await state.update_data(title=message.text.strip())
    await state.set_state(AddGoalStates.deadline)
    sent = await edit_stored(message.bot, message.chat.id, msg_id, t(lang, "goal_deadline_prompt"))
    await state.update_data(bot_msg_id=sent.message_id)


@router.message(StateFilter(AddGoalStates.deadline), F.text)
async def add_goal_deadline(message: Message, state: FSMContext, session) -> None:
    data = await state.get_data()
    msg_id = data.get("bot_msg_id")
    text = message.text.strip()
    if text.lower() == "нет" or text.lower() == "no":
        deadline = None
    else:
        try:
            deadline = datetime.strptime(text, "%d.%m.%Y").date()
        except ValueError:
            user = await session.scalar(select(User).filter_by(tg_id=message.from_user.id))
            lang = getattr(user, "language", "en") if user else "en"
            sent = await edit_stored(message.bot, message.chat.id, msg_id, t(lang, "goal_deadline_invalid"))
            await state.update_data(bot_msg_id=sent.message_id)
            return

    user = await session.scalar(select(User).filter_by(tg_id=message.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    await state.update_data(deadline=deadline)
    await state.set_state(AddGoalStates.category)
    sent = await edit_stored(message.bot, message.chat.id, msg_id, t(lang, "goal_category_prompt"), get_category_keyboard(lang))
    await state.update_data(bot_msg_id=sent.message_id)


async def _save_goal_from_state(user: User, state: FSMContext, session) -> Goal:
    data = await state.get_data()
    title = data.get("title")
    deadline = data.get("deadline")
    category = data.get("category")
    goal = Goal(user_id=user.id, title=title, deadline=deadline, category=category, status="active")
    session.add(goal)
    await session.commit()
    return goal


@router.callback_query(F.data.startswith("goals:category:"), StateFilter(AddGoalStates.category))
async def add_goal_category_button(query: CallbackQuery, state: FSMContext, session) -> None:
    category = query.data.split(":", 2)[2]
    if category not in _VALID_CATEGORIES:
        await query.answer()
        return
    category_value = None if category == "Skip" else category

    await state.update_data(category=category_value)
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    if user is None:
        await query.answer(t(lang, "user_not_found"), show_alert=True)
        await state.clear()
        return
    await query.answer()

    goal = await _save_goal_from_state(user, state, session)
    schedule_deadline_job(goal, user, query.bot)
    await state.clear()
    goals = await _get_active_goals(user.id, session)
    await edit_or_answer(
        query.message,
        _render_goals_list(goals, lang),
        get_goal_menu_keyboard(lang, True),
    )


@router.message(StateFilter(AddGoalStates.category), F.text)
async def add_goal_category_text(message: Message, state: FSMContext, session) -> None:
    category_value = message.text.strip()
    user = await session.scalar(select(User).filter_by(tg_id=message.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    data = await state.get_data()
    msg_id = data.get("bot_msg_id")
    if user is None:
        sent = await edit_stored(message.bot, message.chat.id, msg_id, t(lang, "user_not_found"))
        await state.update_data(bot_msg_id=sent.message_id)
        await state.clear()
        return
    if len(category_value) > 100:
        sent = await edit_stored(message.bot, message.chat.id, msg_id, t(lang, "input_too_long"))
        await state.update_data(bot_msg_id=sent.message_id)
        return
    if not category_value:
        sent = await edit_stored(message.bot, message.chat.id, msg_id, t(lang, "goal_category_invalid"))
        await state.update_data(bot_msg_id=sent.message_id)
        return

    await state.update_data(category=category_value)

    goal = await _save_goal_from_state(user, state, session)
    schedule_deadline_job(goal, user, message.bot)
    await state.clear()
    goals = await _get_active_goals(user.id, session)
    await edit_stored(
        message.bot, message.chat.id, msg_id,
        _render_goals_list(goals, lang),
        get_goal_menu_keyboard(lang, True),
    )


@router.callback_query(F.data == "goals:list")
async def list_goals(query: CallbackQuery, session) -> None:
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    if user is None:
        await query.answer(t(lang, "user_not_found"), show_alert=True)
        return

    goals = await _get_active_goals(user.id, session)
    await query.answer()
    if not goals:
        await edit_or_answer(
            query.message,
            t(lang, "goal_list_empty"),
            get_goal_menu_keyboard(lang, False),
        )
        return

    await edit_or_answer(query.message, t(lang, "goal_choose"), get_goal_list_keyboard(lang, goals))


@router.callback_query(F.data == "goals:back")
async def goals_back(query: CallbackQuery, session) -> None:
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    await query.answer()
    await edit_or_answer(query.message, t(lang, "back_to_menu"), get_main_menu_keyboard(lang))


@router.callback_query(F.data.startswith("goal:view:"))
async def view_goal(query: CallbackQuery, session) -> None:
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    if user is None:
        await query.answer(t(lang, "user_not_found"), show_alert=True)
        return

    try:
        goal_id = int(query.data.split(":", 2)[2])
    except ValueError:
        await query.answer()
        return
    goal = await session.scalar(
        select(Goal).filter_by(id=goal_id, user_id=user.id, status="active")
        .options(selectinload(Goal.wins))
    )
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
            lines.append(f"— {win.raw_text} ({format_date(win.created_at, lang, year=False)})")
    else:
        lines.append(t(lang, "goal_view_no_wins"))

    await query.answer()
    await edit_or_answer(query.message, "\n".join(lines), get_goal_detail_buttons(lang, goal.id, has_wins=bool(wins)))


@router.callback_query(F.data.startswith("goal:analyse:"))
async def analyse_goal(query: CallbackQuery, session, bot: Bot) -> None:
    if not rate_check(query.from_user.id):
        await query.answer(t("en", "rate_limited"), show_alert=True)
        return
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    if user is None:
        await query.answer(t(lang, "user_not_found"), show_alert=True)
        return

    try:
        goal_id = int(query.data.split(":", 2)[2])
    except ValueError:
        await query.answer()
        return
    goal = await session.scalar(
        select(Goal).filter_by(id=goal_id, user_id=user.id)
        .options(selectinload(Goal.wins))
    )
    if goal is None:
        await query.answer(t(lang, "goal_not_found"), show_alert=True)
        return

    days_elapsed = (datetime.now(timezone.utc).date() - goal.created_at.date()).days
    deadline_days = (goal.deadline - datetime.now(timezone.utc).date()).days if goal.deadline else None
    wins_texts = [win.raw_text for win in goal.wins]

    await query.answer()
    chat_id = query.message.chat.id
    msg = await edit_or_answer(query.message, t(lang, "goal_analysing"))

    try:
        async with ChatActionSender.typing(bot=bot, chat_id=chat_id):
            analysis = await ask_goal_progress(
                user.tone, goal.title, wins_texts, days_elapsed, deadline_days, lang
            )
    except Exception:
        logger.warning("AI goal analysis failed for user %s goal %s", user.id, goal_id, exc_info=True)
        analysis = t(lang, "goal_analysis_error")

    stickers_enabled = getattr(user, "stickers_enabled", False)
    if stickers_enabled:
        await try_delete(msg)
        await send_random_sticker(bot, chat_id, settings.STICKER_SET_NAME, True)
        await bot.send_message(chat_id, analysis)
    else:
        await edit_or_answer(msg, analysis)
    await bot.send_message(chat_id, goal.title, reply_markup=get_goal_detail_buttons(lang, goal_id))


@router.callback_query(F.data.startswith("goal:done:"))
async def complete_goal(query: CallbackQuery, session, bot: Bot) -> None:
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    if user is None:
        await query.answer(t(lang, "user_not_found"), show_alert=True)
        return

    try:
        goal_id = int(query.data.split(":", 2)[2])
    except ValueError:
        await query.answer()
        return
    goal = await session.scalar(select(Goal).filter_by(id=goal_id, user_id=user.id, status="active"))
    if goal is None:
        await query.answer(t(lang, "goal_not_found"), show_alert=True)
        return

    goal.status = "done"
    await session.commit()
    remove_deadline_job(goal.id)
    days = (datetime.now(timezone.utc).date() - goal.created_at.date()).days
    goals = await _get_active_goals(user.id, session)
    combined = f"{t(lang, 'goal_done', title=goal.title, days=days)}\n\n{_render_goals_list(goals, lang)}"
    stickers_enabled = getattr(user, "stickers_enabled", False)
    chat_id = query.message.chat.id
    await query.answer()
    if stickers_enabled:
        await try_delete(query.message)
        await send_random_sticker(bot, chat_id, settings.STICKER_SET_NAME, True)
        await bot.send_message(chat_id, combined, reply_markup=get_goal_menu_keyboard(lang, bool(goals)))
    else:
        await edit_or_answer(query.message, combined, get_goal_menu_keyboard(lang, bool(goals)))


@router.callback_query(F.data.regexp(r"^goal:edit:\d+$"))
async def edit_goal_menu(query: CallbackQuery, session) -> None:
    goal_id = int(query.data.split(":", 2)[2])
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    await query.answer()
    await edit_or_answer(query.message, t(lang, "goal_edit_menu"), get_goal_edit_keyboard(lang, goal_id))


@router.callback_query(F.data.startswith("goal:edit:title:"))
async def edit_goal_title_start(query: CallbackQuery, state: FSMContext, session) -> None:
    goal_id = int(query.data.split(":", 3)[3])
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    await query.answer()
    sent = await edit_or_answer(query.message, t(lang, "goal_edit_title_prompt"))
    await state.update_data(editing_goal_id=goal_id, bot_msg_id=sent.message_id)
    await state.set_state(GoalEditStates.title)


@router.message(StateFilter(GoalEditStates.title), F.text)
async def edit_goal_title_save(message: Message, state: FSMContext, session) -> None:
    user = await session.scalar(select(User).filter_by(tg_id=message.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    data = await state.get_data()
    goal_id = data.get("editing_goal_id")
    msg_id = data.get("bot_msg_id")
    new_title = message.text.strip()
    if len(new_title) > 2000:
        sent = await edit_stored(message.bot, message.chat.id, msg_id, t(lang, "input_too_long"))
        await state.update_data(bot_msg_id=sent.message_id)
        return
    goal = await session.scalar(select(Goal).filter_by(id=goal_id, user_id=user.id, status="active"))
    if goal is None:
        await edit_stored(message.bot, message.chat.id, msg_id, t(lang, "goal_not_found"))
        await state.clear()
        return
    goal.title = new_title
    await session.commit()
    await state.clear()
    await edit_stored(message.bot, message.chat.id, msg_id, t(lang, "goal_title_updated"), get_goal_detail_buttons(lang, goal_id))


@router.callback_query(F.data.startswith("goal:edit:deadline:"))
async def edit_goal_deadline_start(query: CallbackQuery, state: FSMContext, session) -> None:
    goal_id = int(query.data.split(":", 3)[3])
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    await query.answer()
    sent = await edit_or_answer(query.message, t(lang, "goal_edit_deadline_prompt"))
    await state.update_data(editing_goal_id=goal_id, bot_msg_id=sent.message_id)
    await state.set_state(GoalEditStates.deadline)


@router.message(StateFilter(GoalEditStates.deadline), F.text)
async def edit_goal_deadline_save(message: Message, state: FSMContext, session) -> None:
    user = await session.scalar(select(User).filter_by(tg_id=message.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    data = await state.get_data()
    goal_id = data.get("editing_goal_id")
    msg_id = data.get("bot_msg_id")
    text = message.text.strip()
    if text.lower() in ("no", "нет"):
        new_deadline = None
        confirmation_key = "goal_deadline_removed"
    else:
        try:
            new_deadline = datetime.strptime(text, "%d.%m.%Y").date()
            confirmation_key = "goal_deadline_updated"
        except ValueError:
            sent = await edit_stored(message.bot, message.chat.id, msg_id, t(lang, "goal_deadline_invalid"))
            await state.update_data(bot_msg_id=sent.message_id)
            return
    goal = await session.scalar(select(Goal).filter_by(id=goal_id, user_id=user.id, status="active"))
    if goal is None:
        await edit_stored(message.bot, message.chat.id, msg_id, t(lang, "goal_not_found"))
        await state.clear()
        return
    old_deadline = goal.deadline
    goal.deadline = new_deadline
    await session.commit()
    remove_deadline_job(goal_id)
    if new_deadline:
        schedule_deadline_job(goal, user, message.bot)
    await state.clear()
    await edit_stored(message.bot, message.chat.id, msg_id, t(lang, confirmation_key), get_goal_detail_buttons(lang, goal_id))


@router.callback_query(F.data.startswith("goal:edit:category:"))
async def edit_goal_category_start(query: CallbackQuery, state: FSMContext, session) -> None:
    goal_id = int(query.data.split(":", 3)[3])
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    await query.answer()
    sent = await edit_or_answer(query.message, t(lang, "goal_edit_category_prompt"), get_category_keyboard(lang))
    await state.update_data(editing_goal_id=goal_id, bot_msg_id=sent.message_id)
    await state.set_state(GoalEditStates.category)


@router.callback_query(F.data.startswith("goals:category:"), StateFilter(GoalEditStates.category))
async def edit_goal_category_button(query: CallbackQuery, state: FSMContext, session) -> None:
    category = query.data.split(":", 2)[2]
    if category not in _VALID_CATEGORIES:
        await query.answer()
        return
    category_value = None if category == "Skip" else category
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    data = await state.get_data()
    goal_id = data.get("editing_goal_id")
    goal = await session.scalar(select(Goal).filter_by(id=goal_id, user_id=user.id, status="active"))
    if goal is None:
        await query.answer(t(lang, "goal_not_found"), show_alert=True)
        await state.clear()
        return
    goal.category = category_value
    await session.commit()
    await state.clear()
    await query.answer()
    await edit_or_answer(query.message, t(lang, "goal_category_updated"), get_goal_detail_buttons(lang, goal_id))


@router.message(StateFilter(GoalEditStates.category), F.text)
async def edit_goal_category_text(message: Message, state: FSMContext, session) -> None:
    user = await session.scalar(select(User).filter_by(tg_id=message.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    data = await state.get_data()
    goal_id = data.get("editing_goal_id")
    msg_id = data.get("bot_msg_id")
    category_value = message.text.strip()
    if len(category_value) > 100:
        sent = await edit_stored(message.bot, message.chat.id, msg_id, t(lang, "input_too_long"))
        await state.update_data(bot_msg_id=sent.message_id)
        return
    goal = await session.scalar(select(Goal).filter_by(id=goal_id, user_id=user.id, status="active"))
    if goal is None:
        await edit_stored(message.bot, message.chat.id, msg_id, t(lang, "goal_not_found"))
        await state.clear()
        return
    goal.category = category_value
    await session.commit()
    await state.clear()
    await edit_stored(message.bot, message.chat.id, msg_id, t(lang, "goal_category_updated"), get_goal_detail_buttons(lang, goal_id))


@router.callback_query(F.data.startswith("goal:manage_wins:"))
async def manage_goal_wins(query: CallbackQuery, session) -> None:
    goal_id = int(query.data.split(":", 2)[2])
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    goal = await session.scalar(
        select(Goal).filter_by(id=goal_id, user_id=user.id)
        .options(selectinload(Goal.wins))
    )
    if goal is None:
        await query.answer(t(lang, "goal_not_found"), show_alert=True)
        return
    if not goal.wins:
        await query.answer(t(lang, "no_wins_linked"), show_alert=True)
        return
    buttons = []
    for win in goal.wins:
        preview = win.raw_text[:45] + ("…" if len(win.raw_text) > 45 else "")
        buttons.append([InlineKeyboardButton(
            text=f"✂️ {preview}",
            callback_data=f"win:unlink:{win.id}:{goal_id}",
        )])
    buttons.append([InlineKeyboardButton(text=t(lang, "btn_back"), callback_data=f"goal:view:{goal_id}")])
    await query.answer()
    await edit_or_answer(query.message, t(lang, "choose_win_to_unlink"), InlineKeyboardMarkup(inline_keyboard=buttons))


@router.callback_query(F.data.startswith("win:unlink:"))
async def unlink_win_from_goal(query: CallbackQuery, session) -> None:
    parts = query.data.split(":")
    win_id, goal_id = int(parts[2]), int(parts[3])
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    win_goal = await session.scalar(select(WinGoal).filter_by(win_id=win_id, goal_id=goal_id))
    if win_goal:
        await session.delete(win_goal)
        await session.commit()
    await query.answer()
    await edit_or_answer(query.message, t(lang, "win_unlinked"), get_goal_detail_buttons(lang, goal_id))


@router.callback_query(F.data == "goals:suggest")
async def suggest_goal(query: CallbackQuery, state: FSMContext, session, bot: Bot) -> None:
    from handlers.wins import WinStates
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    if user is None:
        await query.answer(t(lang, "user_not_found"), show_alert=True)
        return

    row = (await session.execute(
        select(Win.tag, func.count(Win.id).label("cnt"))
        .filter(Win.user_id == user.id, Win.tag.isnot(None))
        .group_by(Win.tag)
        .order_by(func.count(Win.id).desc())
        .limit(1)
    )).first()

    if row is None or row.cnt < 5:
        await query.answer()
        goals = await _get_active_goals(user.id, session)
        await edit_or_answer(query.message, t(lang, "goals_suggest_no_data"), get_goal_menu_keyboard(lang, bool(goals)))
        return

    top_tag = row.tag
    recent_wins = await session.scalars(
        select(Win).filter_by(user_id=user.id, tag=top_tag).order_by(Win.created_at.desc()).limit(5)
    )
    win_texts = [w.raw_text for w in recent_wins.all()]
    await query.answer()
    try:
        async with ChatActionSender.typing(bot=bot, chat_id=query.message.chat.id):
            suggested_title = await suggest_goal_title(top_tag, win_texts, lang)
    except Exception:
        logger.warning("Goal suggestion failed in goals:suggest for user %s", user.id, exc_info=True)
        goals = await _get_active_goals(user.id, session)
        await edit_or_answer(query.message, t(lang, "goals_suggest_no_data"), get_goal_menu_keyboard(lang, bool(goals)))
        return

    suggestion_msg = await edit_or_answer(
        query.message,
        t(lang, "goal_suggestion", tag=t(lang, f"tag_{top_tag}"), title=suggested_title),
        get_goal_suggestion_keyboard(lang),
    )
    await state.set_state(WinStates.waiting_for_goal_suggestion)
    await state.update_data(suggested_title=suggested_title, bot_msg_id=suggestion_msg.message_id)


@router.callback_query(F.data.regexp(r"^goal:abandon:\d+$"))
async def abandon_goal(query: CallbackQuery, session) -> None:
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    if user is None:
        await query.answer(t(lang, "user_not_found"), show_alert=True)
        return

    try:
        goal_id = int(query.data.split(":", 2)[2])
    except ValueError:
        await query.answer()
        return
    goal = await session.scalar(select(Goal).filter_by(id=goal_id, user_id=user.id, status="active"))
    if goal is None:
        await query.answer(t(lang, "goal_not_found"), show_alert=True)
        return

    await query.answer()
    await edit_or_answer(query.message, t(lang, "goal_abandon_confirm"), get_abandon_confirm_buttons(lang, goal_id))


@router.callback_query(F.data.startswith("goal:abandon:confirm:"))
async def confirm_abandon_goal(query: CallbackQuery, session) -> None:
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    if user is None:
        await query.answer(t(lang, "user_not_found"), show_alert=True)
        return

    try:
        goal_id = int(query.data.split(":", 3)[3])
    except ValueError:
        await query.answer()
        return
    goal = await session.scalar(select(Goal).filter_by(id=goal_id, user_id=user.id, status="active"))
    if goal is None:
        await query.answer(t(lang, "goal_not_found"), show_alert=True)
        return

    goal.status = "abandoned"
    await session.commit()
    remove_deadline_job(goal.id)
    goals = await _get_active_goals(user.id, session)
    combined = f"{t(lang, 'goal_abandoned')}\n\n{_render_goals_list(goals, lang)}"
    await query.answer()
    await edit_or_answer(query.message, combined, get_goal_menu_keyboard(lang, bool(goals)))


@router.callback_query(F.data.startswith("goal:abandon:cancel:"))
async def cancel_abandon_goal(query: CallbackQuery, session) -> None:
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    if user is None:
        await query.answer(t(lang, "user_not_found"), show_alert=True)
        return

    try:
        goal_id = int(query.data.split(":", 3)[3])
    except ValueError:
        await query.answer()
        return
    goal = await session.scalar(select(Goal).filter_by(id=goal_id, user_id=user.id, status="active"))
    if goal is None:
        await query.answer(t(lang, "goal_not_found"), show_alert=True)
        return

    goals = await _get_active_goals(user.id, session)
    await query.answer()
    await edit_or_answer(query.message, _render_goals_list(goals, lang), get_goal_menu_keyboard(lang, bool(goals)))
