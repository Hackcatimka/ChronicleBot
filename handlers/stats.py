import calendar
from datetime import datetime, timedelta, timezone

from aiogram import Bot, F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.chat_action import ChatActionSender
from sqlalchemy import select

from ai import ask_weekly_narrative
from db.models import User, Win
from locales import t
from ratelimit import check as rate_check
from utils import edit_or_answer, format_date

router = Router()


def get_stats_menu_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "btn_this_week"), callback_data="stats:week"),
         InlineKeyboardButton(text=t(lang, "btn_this_month"), callback_data="stats:month")],
        [InlineKeyboardButton(text=t(lang, "btn_all_time"), callback_data="stats:all"),
         InlineKeyboardButton(text=t(lang, "btn_compare"), callback_data="stats:compare")],
        [InlineKeyboardButton(text=t(lang, "btn_skills_map"), callback_data="stats:skills")],
        [InlineKeyboardButton(text=t(lang, "btn_back"), callback_data="main:back")],
    ])


def get_back_to_stats_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "btn_back_to_stats"), callback_data="stats:back")],
    ])


def get_back_to_stats_with_ai(lang: str, period: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "btn_ai_review"), callback_data=f"stats:ai:{period}")],
        [InlineKeyboardButton(text=t(lang, "btn_back_to_stats"), callback_data="stats:back")],
    ])


def get_compare_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "period_this_week"), callback_data="compare:first:this_week"),
         InlineKeyboardButton(text=t(lang, "period_last_week"), callback_data="compare:first:last_week")],
        [InlineKeyboardButton(text=t(lang, "period_this_month"), callback_data="compare:first:this_month"),
         InlineKeyboardButton(text=t(lang, "period_last_month"), callback_data="compare:first:last_month")],
    ])


def get_second_compare_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "period_this_week"), callback_data=f"compare:second:this_week"),
         InlineKeyboardButton(text=t(lang, "period_last_week"), callback_data=f"compare:second:last_week")],
        [InlineKeyboardButton(text=t(lang, "period_this_month"), callback_data=f"compare:second:this_month"),
         InlineKeyboardButton(text=t(lang, "period_last_month"), callback_data=f"compare:second:last_month")],
    ])


class CompareStates(StatesGroup):
    choosing_first = State()
    choosing_second = State()


def _get_period_range(period_key: str) -> tuple[datetime, datetime]:
    today = datetime.now(timezone.utc).date()
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
        datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc),
        datetime.combine(end_date, datetime.min.time(), tzinfo=timezone.utc),
    )


def _month_name(month: int, lang: str) -> str:
    if lang == "ru":
        return [
            "", "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
            "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь",
        ][month]
    return calendar.month_name[month]


def _format_date(dt: datetime, with_year: bool = True, lang: str = "en") -> str:
    return format_date(dt, lang, weekday=not with_year, year=with_year)


def _period_label(period_key: str, lang: str) -> str:
    return {
        "this_week": t(lang, "period_this_week"),
        "last_week": t(lang, "period_last_week"),
        "this_month": t(lang, "period_this_month"),
        "last_month": t(lang, "period_last_month"),
    }[period_key]


_TAG_ORDER = ["work", "health", "learning", "personal", "creative", "social", "finance", "other"]


def _compute_streak(wins: list[Win]) -> int:
    if not wins:
        return 0
    today = datetime.now(timezone.utc).date()
    days_with_wins = {win.created_at.date() for win in wins}
    for start in (today, today - timedelta(days=1)):
        if start not in days_with_wins:
            continue
        streak, day = 0, start
        while day in days_with_wins:
            streak += 1
            day -= timedelta(days=1)
        return streak
    return 0


def _build_skills_map(wins: list[Win], lang: str) -> str:
    counts: dict[str, int] = {}
    for win in wins:
        tag = win.tag or "other"
        counts[tag] = counts.get(tag, 0) + 1

    if not counts:
        return t(lang, "stats_skills_empty")

    total = sum(counts.values())
    max_count = max(counts.values())
    lines = [t(lang, "stats_skills_title", total=total), ""]
    for tag in _TAG_ORDER:
        n = counts.get(tag, 0)
        if n == 0:
            continue
        filled = round(n / max_count * 10)
        bar = "█" * filled + "░" * (10 - filled)
        lines.append(f"{t(lang, f'tag_{tag}')}")
        lines.append(f"{bar}  {n}")
        lines.append("")
    return "\n".join(lines).rstrip()


def _format_tag_breakdown(wins: list[Win], lang: str) -> str | None:
    counts: dict[str, int] = {}
    for win in wins:
        tag = win.tag or "other"
        counts[tag] = counts.get(tag, 0) + 1
    if not counts:
        return None
    parts = [f"{t(lang, f'tag_{tag}')} · {n}" for tag in _TAG_ORDER if (n := counts.get(tag))]
    return "  ".join(parts)


def _get_wins_stats(wins: list[Win], start: datetime | None = None, end: datetime | None = None) -> tuple[int, int, list[Win]]:
    filtered = [win for win in wins if (start is None or win.created_at >= start) and (end is None or win.created_at < end)]
    days = {win.created_at.date() for win in filtered}
    return len(filtered), len(days), sorted(filtered, key=lambda win: win.created_at)


def _build_period_report(period_name: str, wins: list[Win], days_in_period: int, lang: str) -> str:
    total, active_days, filtered = _get_wins_stats(wins)
    lines = [t(lang, "report_title", title=period_name), "", t(lang, "report_total_wins", n=total), t(lang, "active_days", n=active_days, total=days_in_period)]
    breakdown = _format_tag_breakdown(filtered, lang)
    if breakdown:
        lines += ["", t(lang, "stats_by_tag"), breakdown]
    lines.append("")
    if filtered:
        lines.append(t(lang, "report_your_wins"))
        for win in filtered:
            lines.append(f"— {win.raw_text} ({_format_date(win.created_at, with_year=False, lang=lang)})")
    else:
        lines.append(t(lang, "report_no_wins"))
    return "\n".join(lines)


def _build_all_time_report(wins: list[Win], lang: str) -> str:
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
        most_active_name = _month_name(most_active[0][1], lang)
        month_count = most_active[1]
        streak = _compute_streak(wins)
        lines = [
            t(lang, "report_title", title=t(lang, "period_caption", label=t(lang, "btn_all_time"))),
            "",
            t(lang, "report_total_wins", n=total),
            t(lang, "report_days_with_bot", n=len(unique_days)),
            t(lang, "report_most_active_month", month=most_active_name, count=month_count),
            t(lang, "report_first_win", date=_format_date(first, lang=lang)),
            t(lang, "report_latest_win", date=_format_date(latest, lang=lang)),
        ]
        if streak > 0:
            lines.append(t(lang, "stats_streak", n=streak))
        breakdown = _format_tag_breakdown(wins, lang)
        if breakdown:
            lines += ["", t(lang, "stats_by_tag"), breakdown]
    else:
        lines = [
            t(lang, "report_title", title=t(lang, "btn_all_time")),
            "",
            t(lang, "report_total_wins", n=0),
            t(lang, "report_days_with_bot", n=0),
            t(lang, "report_most_active_month", month="—", count=0),
            t(lang, "report_first_win", date="—"),
            t(lang, "report_latest_win", date="—"),
        ]
    return "\n".join(lines)


def _format_compare_report(first_key: str, second_key: str, first_stats: tuple[int, int], second_stats: tuple[int, int], lang: str) -> str:
    first_label = _period_label(first_key, lang)
    second_label = _period_label(second_key, lang)
    first_wins, first_days = first_stats
    second_wins, second_days = second_stats
    diff = first_wins - second_wins
    if diff > 0:
        diff_line = t(lang, "compare_diff_positive", diff=diff, other=second_label)
    elif diff < 0:
        diff_line = t(lang, "compare_diff_negative", diff=abs(diff), other=second_label)
    else:
        diff_line = t(lang, "compare_diff_same", other=second_label)

    return "\n".join([
        t(lang, "compare_result", first=first_label, second=second_label, w1=first_wins, d1=first_days, w2=second_wins, d2=second_days, diff=diff_line),
    ])


async def _get_user_and_wins(query: CallbackQuery, session) -> tuple[User | None, list[Win]]:
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    if user is None:
        return None, []
    wins = (await session.scalars(select(Win).filter_by(user_id=user.id).order_by(Win.created_at))).all()
    return user, wins


@router.callback_query(F.data == "menu:stats")
async def show_stats_menu(query: CallbackQuery, session) -> None:
    user, _ = await _get_user_and_wins(query, session)
    lang = getattr(user, "language", "en") if user else "en"
    await query.answer()
    await edit_or_answer(query.message, t(lang, "stats_title"), get_stats_menu_keyboard(lang))


@router.callback_query(F.data == "stats:back")
async def back_to_stats(query: CallbackQuery, session) -> None:
    user, _ = await _get_user_and_wins(query, session)
    lang = getattr(user, "language", "en") if user else "en"
    await query.answer()
    await edit_or_answer(query.message, t(lang, "stats_title"), get_stats_menu_keyboard(lang))


@router.callback_query(F.data == "stats:week")
async def show_this_week(query: CallbackQuery, session) -> None:
    user, wins = await _get_user_and_wins(query, session)
    lang = getattr(user, "language", "en") if user else "en"
    if user is None:
        await query.answer(t(lang, "user_not_found"), show_alert=True)
        return

    lang = getattr(user, "language", "en")
    start, end = _get_period_range("this_week")
    filtered = [win for win in wins if start <= win.created_at < end]
    await query.answer()
    await edit_or_answer(query.message, _build_period_report(t(lang, "period_this_week"), filtered, 7, lang), get_back_to_stats_with_ai(lang, "week"))


@router.callback_query(F.data == "stats:month")
async def show_this_month(query: CallbackQuery, session) -> None:
    user, wins = await _get_user_and_wins(query, session)
    lang = getattr(user, "language", "en") if user else "en"
    if user is None:
        await query.answer(t(lang, "user_not_found"), show_alert=True)
        return

    start, end = _get_period_range("this_month")
    filtered = [win for win in wins if start <= win.created_at < end]
    days_in_month = calendar.monthrange(start.year, start.month)[1]
    month_name = _month_name(start.month, lang)
    await query.answer()
    await edit_or_answer(query.message, _build_period_report(f"{month_name} {start.year}", filtered, days_in_month, lang), get_back_to_stats_with_ai(lang, "month"))


@router.callback_query(F.data == "stats:all")
async def show_all_time(query: CallbackQuery, session) -> None:
    user, wins = await _get_user_and_wins(query, session)
    lang = getattr(user, "language", "en") if user else "en"
    if user is None:
        await query.answer(t(lang, "user_not_found"), show_alert=True)
        return

    await query.answer()
    await edit_or_answer(query.message, _build_all_time_report(wins, lang), get_back_to_stats_keyboard(lang))


@router.callback_query(F.data == "stats:compare")
async def start_compare(query: CallbackQuery, state: FSMContext, session) -> None:
    user, _ = await _get_user_and_wins(query, session)
    lang = getattr(user, "language", "en") if user else "en"
    if user is None:
        await query.answer(t(lang, "user_not_found"), show_alert=True)
        return

    await state.set_state(CompareStates.choosing_first)
    await query.answer()
    await edit_or_answer(query.message, t(lang, "choose_first_period_prompt"), get_compare_keyboard(lang))


@router.callback_query(F.data.startswith("compare:first:"), StateFilter(CompareStates.choosing_first))
async def choose_first_period(query: CallbackQuery, state: FSMContext, session) -> None:
    first_choice = query.data.split(":", 2)[2]
    await state.update_data(first_choice=first_choice)
    await state.set_state(CompareStates.choosing_second)
    user, _ = await _get_user_and_wins(query, session)
    lang = getattr(user, "language", "en") if user else "en"
    await query.answer()
    await edit_or_answer(query.message, t(lang, "choose_second_period_prompt"), get_second_compare_keyboard(lang))


@router.callback_query(F.data.startswith("compare:second:"), StateFilter(CompareStates.choosing_second))
async def choose_second_period(query: CallbackQuery, state: FSMContext, session) -> None:
    data = await state.get_data()
    first_choice = data.get("first_choice")
    user, wins = await _get_user_and_wins(query, session)
    lang = getattr(user, "language", "en") if user else "en"
    if user is None:
        await query.answer(t(lang, "user_not_found"), show_alert=True)
        await state.clear()
        return
    if not first_choice:
        await query.answer(t(lang, "choose_first_period_prompt"), show_alert=True)
        await state.clear()
        return

    second_choice = query.data.split(":", 2)[2]
    first_start, first_end = _get_period_range(first_choice)
    second_start, second_end = _get_period_range(second_choice)
    first_stats = _get_wins_stats(wins, first_start, first_end)
    second_stats = _get_wins_stats(wins, second_start, second_end)

    await query.answer()
    await edit_or_answer(query.message, _format_compare_report(first_choice, second_choice, first_stats[:2], second_stats[:2], lang), get_back_to_stats_keyboard(lang))
    await state.clear()


@router.callback_query(F.data.startswith("stats:ai:"))
async def show_period_ai_review(query: CallbackQuery, session, bot: Bot) -> None:
    if not rate_check(query.from_user.id):
        await query.answer(t("en", "rate_limited"), show_alert=True)
        return
    user, wins = await _get_user_and_wins(query, session)
    lang = getattr(user, "language", "en") if user else "en"
    if user is None:
        await query.answer(t(lang, "user_not_found"), show_alert=True)
        return

    period = query.data.split(":", 2)[2]  # "week" or "month"
    period_key = "this_week" if period == "week" else "this_month"
    start, end = _get_period_range(period_key)
    recent = [w for w in wins if start <= w.created_at < end]
    await query.answer()

    if not recent:
        await edit_or_answer(query.message, t(lang, "stats_ai_empty"), get_back_to_stats_keyboard(lang))
        return

    msg = await edit_or_answer(query.message, t(lang, "stats_ai_loading"))
    try:
        async with ChatActionSender.typing(bot=bot, chat_id=query.message.chat.id):
            wins_with_tags = [(w.raw_text, w.tag or "other") for w in recent]
            digest = await ask_weekly_narrative(user.tone, wins_with_tags, lang, period=period)
    except Exception:
        digest = "\n".join(f"— {w.raw_text}" for w in recent)
    await edit_or_answer(msg, digest, get_back_to_stats_keyboard(lang))


@router.callback_query(F.data == "stats:skills")
async def show_skills_map(query: CallbackQuery, session) -> None:
    user, wins = await _get_user_and_wins(query, session)
    lang = getattr(user, "language", "en") if user else "en"
    if user is None:
        await query.answer(t(lang, "user_not_found"), show_alert=True)
        return
    await query.answer()
    await edit_or_answer(query.message, _build_skills_map(wins, lang), get_back_to_stats_keyboard(lang))
