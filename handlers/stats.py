import calendar
from datetime import datetime, date, timedelta

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import select

from db.models import User, Win
from keyboards import get_main_menu_keyboard

router = Router()


def get_stats_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 This week", callback_data="stats:week"),
         InlineKeyboardButton(text="📆 This month", callback_data="stats:month")],
        [InlineKeyboardButton(text="🗓 All time", callback_data="stats:all"),
         InlineKeyboardButton(text="⚖️ Compare", callback_data="stats:compare")],
        [InlineKeyboardButton(text="← Back", callback_data="stats:back")],
    ])


def get_back_to_stats_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="← Back to stats", callback_data="stats:back")],
    ])


def get_compare_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="This week", callback_data="compare:first:this_week"),
         InlineKeyboardButton(text="Last week", callback_data="compare:first:last_week")],
        [InlineKeyboardButton(text="This month", callback_data="compare:first:this_month"),
         InlineKeyboardButton(text="Last month", callback_data="compare:first:last_month")],
    ])


def get_second_compare_keyboard(first_choice: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="This week", callback_data=f"compare:second:this_week"),
         InlineKeyboardButton(text="Last week", callback_data=f"compare:second:last_week")],
        [InlineKeyboardButton(text="This month", callback_data=f"compare:second:this_month"),
         InlineKeyboardButton(text="Last month", callback_data=f"compare:second:last_month")],
    ])


class CompareStates(StatesGroup):
    choosing_first = State()
    choosing_second = State()


def _get_period_range(period_key: str) -> tuple[datetime, datetime]:
    today = datetime.utcnow().date()
    if period_key == "this_week":
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=7)
    elif period_key == "last_week":
        start_date = today - timedelta(days=today.weekday() + 7)
        end_date = start_date + timedelta(days=7)
    elif period_key == "this_month":
        start_date = today.replace(day=1)
        next_month = start_date.replace(day=28) + timedelta(days=4)
        end_date = next_month.replace(day=1)
    elif period_key == "last_month":
        first_of_this_month = today.replace(day=1)
        last_month_end = first_of_this_month - timedelta(days=1)
        start_date = last_month_end.replace(day=1)
        end_date = first_of_this_month
    else:
        raise ValueError("Unknown period key")

    return (
        datetime.combine(start_date, datetime.min.time()),
        datetime.combine(end_date, datetime.min.time()),
    )


def _format_date(dt: datetime, with_year: bool = True) -> str:
    if with_year:
        return dt.strftime("%d %b %Y")
    return dt.strftime("%a, %d %b")


def _period_label(period_key: str) -> str:
    return {
        "this_week": "This week",
        "last_week": "Last week",
        "this_month": "This month",
        "last_month": "Last month",
    }[period_key]


def _get_wins_stats(wins: list[Win], start: datetime | None = None, end: datetime | None = None) -> tuple[int, int, list[Win]]:
    filtered = [win for win in wins if (start is None or win.created_at >= start) and (end is None or win.created_at < end)]
    days = {win.created_at.date() for win in filtered}
    return len(filtered), len(days), sorted(filtered, key=lambda win: win.created_at)


def _build_period_report(period_name: str, wins: list[Win], days_in_period: int) -> str:
    total, active_days, filtered = _get_wins_stats(wins)
    lines = [f"📊 {period_name}", "", f"Wins recorded: {total}", f"Active days: {active_days} out of {days_in_period}", ""]
    if filtered:
        lines.append("Your wins:")
        for win in filtered:
            lines.append(f"— {win.raw_text} ({_format_date(win.created_at, with_year=False)})")
    else:
        lines.append("No wins recorded yet.")
    return "\n".join(lines)


def _build_all_time_report(wins: list[Win]) -> str:
    total = len(wins)
    unique_days = {win.created_at.date() for win in wins}
    if wins:
        first = wins[0].created_at
        latest = wins[-1].created_at
        month_counts: dict[tuple[int, int], int] = {}
        for win in wins:
            key = (win.created_at.year, win.created_at.month)
            month_counts[key] = month_counts.get(key, 0) + 1
        most_active = max(month_counts.items(), key=lambda item: item[1])
        month_name = calendar.month_name[most_active[0][1]]
        month_count = most_active[1]
        lines = [
            "📊 All time",
            "",
            f"Total wins: {total}",
            f"Days with the bot: {len(unique_days)}",
            f"Most active month: {month_name} ({month_count} wins)",
            f"First win: {_format_date(first)}",
            f"Latest win: {_format_date(latest)}",
        ]
    else:
        lines = [
            "📊 All time",
            "",
            "Total wins: 0",
            "Days with the bot: 0",
            "Most active month: —",
            "First win: —",
            "Latest win: —",
        ]
    return "\n".join(lines)


def _format_compare_report(first_key: str, second_key: str, first_stats: tuple[int, int], second_stats: tuple[int, int]) -> str:
    first_label = _period_label(first_key)
    second_label = _period_label(second_key)
    first_wins, first_days = first_stats
    second_wins, second_days = second_stats
    diff = first_wins - second_wins
    if diff > 0:
        diff_line = f"+{diff} wins compared to {second_label} 📈"
    elif diff < 0:
        diff_line = f"{diff} wins compared to {second_label} 📉"
    else:
        diff_line = f"Same wins as {second_label}."

    return "\n".join([
        f"⚖️ {first_label} vs {second_label}",
        "",
        f"{first_label}:  {first_wins} wins, {first_days} active days",
        f"{second_label}:  {second_wins} wins, {second_days} active days",
        "",
        diff_line,
    ])


async def _get_user_and_wins(query: CallbackQuery, session) -> tuple[User | None, list[Win]]:
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    if user is None:
        return None, []
    wins = (await session.scalars(select(Win).filter_by(user_id=user.id).order_by(Win.created_at))).all()
    return user, wins


@router.callback_query(F.data == "menu:stats")
async def show_stats_menu(query: CallbackQuery, session) -> None:
    await query.answer()
    await query.message.answer("📊 Stats", reply_markup=get_stats_menu_keyboard())


@router.callback_query(F.data == "stats:back")
async def back_to_stats(query: CallbackQuery, session) -> None:
    await query.answer()
    await query.message.answer("📊 Stats", reply_markup=get_stats_menu_keyboard())


@router.callback_query(F.data == "stats:week")
async def show_this_week(query: CallbackQuery, session) -> None:
    user, wins = await _get_user_and_wins(query, session)
    if user is None:
        await query.answer("Пользователь не найден. Запусти /start.", show_alert=True)
        return

    start, end = _get_period_range("this_week")
    filtered = [win for win in wins if start <= win.created_at < end]
    total = len(filtered)
    active = len({win.created_at.date() for win in filtered})
    lines = [
        "📊 This week",
        "",
        f"Wins recorded: {total}",
        f"Active days: {active} out of 7",
        "",
    ]
    if filtered:
        lines.append("Your wins:")
        for win in filtered:
            lines.append(f"— {win.raw_text} ({_format_date(win.created_at, with_year=False)})")
    else:
        lines.append("No wins recorded yet.")

    await query.answer()
    await query.message.answer("\n".join(lines), reply_markup=get_back_to_stats_keyboard())


@router.callback_query(F.data == "stats:month")
async def show_this_month(query: CallbackQuery, session) -> None:
    user, wins = await _get_user_and_wins(query, session)
    if user is None:
        await query.answer("Пользователь не найден. Запусти /start.", show_alert=True)
        return

    start, end = _get_period_range("this_month")
    filtered = [win for win in wins if start <= win.created_at < end]
    total = len(filtered)
    active = len({win.created_at.date() for win in filtered})
    days_in_month = calendar.monthrange(start.year, start.month)[1]
    month_name = calendar.month_name[start.month]

    lines = [
        f"📊 {month_name} {start.year}",
        "",
        f"Wins recorded: {total}",
        f"Active days: {active} out of {days_in_month}",
        "",
    ]
    if filtered:
        lines.append("Your wins:")
        for win in filtered:
            lines.append(f"— {win.raw_text} ({_format_date(win.created_at, with_year=False)})")
    else:
        lines.append("No wins recorded yet.")

    await query.answer()
    await query.message.answer("\n".join(lines), reply_markup=get_back_to_stats_keyboard())


@router.callback_query(F.data == "stats:all")
async def show_all_time(query: CallbackQuery, session) -> None:
    user, wins = await _get_user_and_wins(query, session)
    if user is None:
        await query.answer("Пользователь не найден. Запусти /start.", show_alert=True)
        return

    total = len(wins)
    unique_days = len({win.created_at.date() for win in wins})
    lines = [
        "📊 All time",
        "",
        f"Total wins: {total}",
        f"Days with the bot: {unique_days}",
    ]

    if wins:
        month_counts: dict[tuple[int, int], int] = {}
        for win in wins:
            key = (win.created_at.year, win.created_at.month)
            month_counts[key] = month_counts.get(key, 0) + 1
        most_active = max(month_counts.items(), key=lambda item: item[1])
        most_active_name = calendar.month_name[most_active[0][1]]
        lines.extend([
            f"Most active month: {most_active_name} ({most_active[1]} wins)",
            f"First win: {_format_date(wins[0].created_at)}",
            f"Latest win: {_format_date(wins[-1].created_at)}",
        ])
    else:
        lines.extend([
            "Most active month: —",
            "First win: —",
            "Latest win: —",
        ])

    await query.answer()
    await query.message.answer("\n".join(lines), reply_markup=get_back_to_stats_keyboard())


@router.callback_query(F.data == "stats:compare")
async def start_compare(query: CallbackQuery, state: FSMContext, session) -> None:
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    if user is None:
        await query.answer("Пользователь не найден. Запусти /start.", show_alert=True)
        return

    await state.set_state(CompareStates.choosing_first)
    await query.answer()
    await query.message.answer("Выбери первый период для сравнения:", reply_markup=get_compare_keyboard())


@router.callback_query(F.data.startswith("compare:first:"), StateFilter(CompareStates.choosing_first))
async def choose_first_period(query: CallbackQuery, state: FSMContext, session) -> None:
    first_choice = query.data.split(":", 2)[2]
    await state.update_data(first_choice=first_choice)
    await state.set_state(CompareStates.choosing_second)
    await query.answer()
    await query.message.answer("Теперь выбери второй период:", reply_markup=get_second_compare_keyboard(first_choice))


@router.callback_query(F.data.startswith("compare:second:"), StateFilter(CompareStates.choosing_second))
async def choose_second_period(query: CallbackQuery, state: FSMContext, session) -> None:
    data = await state.get_data()
    first_choice = data.get("first_choice")
    if not first_choice:
        await query.answer("Выбери первый период заново.", show_alert=True)
        await state.clear()
        return

    second_choice = query.data.split(":", 2)[2]
    user, wins = await _get_user_and_wins(query, session)
    if user is None:
        await query.answer("Пользователь не найден. Запусти /start.", show_alert=True)
        await state.clear()
        return

    first_start, first_end = _get_period_range(first_choice)
    second_start, second_end = _get_period_range(second_choice)
    first_stats = _get_wins_stats(wins, first_start, first_end)
    second_stats = _get_wins_stats(wins, second_start, second_end)

    await query.answer()
    await query.message.answer(
        _format_compare_report(first_choice, second_choice, first_stats[:2], second_stats[:2]),
        reply_markup=get_back_to_stats_keyboard(),
    )
    await state.clear()
