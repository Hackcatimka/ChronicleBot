from datetime import datetime, timedelta, timezone

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy import distinct, func, select

from db.models import Goal, Reminder, User, Win

ADMIN_TG_ID = 698310322

router = Router()


def _period_range(period: str) -> tuple[datetime, datetime]:
    now = datetime.now(timezone.utc)
    if period == "today":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "week":
        start = now - timedelta(days=7)
    elif period == "month":
        start = now - timedelta(days=30)
    else:  # year
        start = now - timedelta(days=365)
    return start, now


def _period_label(period: str) -> str:
    return {"today": "Сегодня", "week": "Неделя", "month": "Месяц", "year": "Год"}[period]


def _admin_keyboard(current: str) -> InlineKeyboardMarkup:
    periods = ["today", "week", "month", "year"]
    buttons = [
        InlineKeyboardButton(
            text=("▸ " if p == current else "") + _period_label(p),
            callback_data=f"admin:period:{p}",
        )
        for p in periods
    ]
    return InlineKeyboardMarkup(inline_keyboard=[buttons])


async def _build_stats(session, period: str) -> str:
    start, _ = _period_range(period)
    label = _period_label(period)

    total_users = await session.scalar(select(func.count(User.id)))
    new_users = await session.scalar(
        select(func.count(User.id)).where(User.created_at >= start)
    )
    active_users = await session.scalar(
        select(func.count(distinct(Win.user_id))).where(Win.created_at >= start)
    )

    lang_rows = (await session.execute(
        select(User.language, func.count(User.id)).group_by(User.language)
    )).all()
    lang_str = "  ".join(f"{lang}: {cnt}" for lang, cnt in lang_rows) or "—"

    total_wins = await session.scalar(select(func.count(Win.id)))
    wins_in_period = await session.scalar(
        select(func.count(Win.id)).where(Win.created_at >= start)
    )

    tag_rows = (await session.execute(
        select(Win.tag, func.count(Win.id))
        .where(Win.created_at >= start, Win.tag.isnot(None))
        .group_by(Win.tag)
        .order_by(func.count(Win.id).desc())
        .limit(3)
    )).all()
    top_tags = ", ".join(f"{tag} ({cnt})" for tag, cnt in tag_rows) or "—"

    goal_rows = (await session.execute(
        select(Goal.status, func.count(Goal.id)).group_by(Goal.status)
    )).all()
    goal_dict = {row[0]: row[1] for row in goal_rows}
    goals_in_period = await session.scalar(
        select(func.count(Goal.id)).where(Goal.created_at >= start)
    )

    users_with_reminders = await session.scalar(
        select(func.count(distinct(Reminder.user_id))).where(Reminder.is_active.is_(True))
    )
    reminder_rows = (await session.execute(
        select(Reminder.type, func.count(Reminder.id))
        .where(Reminder.is_active.is_(True))
        .group_by(Reminder.type)
    )).all()
    reminder_str = "  ".join(f"{rtype}: {cnt}" for rtype, cnt in reminder_rows) or "—"

    users_no_wins = await session.scalar(
        select(func.count(User.id)).where(
            User.id.not_in(select(distinct(Win.user_id)))
        )
    )

    avg_wins = round(wins_in_period / active_users, 1) if active_users else 0

    lines = [
        f"<b>📊 Admin — {label}</b>",
        "",
        "<b>👥 Пользователи</b>",
        f"  Всего: <b>{total_users}</b>",
        f"  Новых за период: <b>{new_users}</b>",
        f"  Активных (есть победы): <b>{active_users}</b>",
        f"  Без единой победы: <b>{users_no_wins}</b>",
        f"  Языки: {lang_str}",
        "",
        "<b>🏆 Победы</b>",
        f"  Всего в БД: <b>{total_wins}</b>",
        f"  За период: <b>{wins_in_period}</b>",
        f"  Топ теги: {top_tags}",
        f"  Avg на активного юзера: <b>{avg_wins}</b>",
        "",
        "<b>🎯 Цели</b>",
        f"  Активных: <b>{goal_dict.get('active', 0)}</b>  "
        f"Завершено: <b>{goal_dict.get('completed', 0)}</b>  "
        f"Брошено: <b>{goal_dict.get('abandoned', 0)}</b>",
        f"  Создано за период: <b>{goals_in_period}</b>",
        "",
        "<b>🔔 Напоминания</b>",
        f"  Юзеров с напоминаниями: <b>{users_with_reminders}</b>",
        f"  По типам: {reminder_str}",
    ]
    return "\n".join(lines)


@router.message(Command("admin"))
async def cmd_admin(message: Message, session) -> None:
    if message.from_user.id != ADMIN_TG_ID:
        return
    text = await _build_stats(session, "week")
    await message.answer(text, reply_markup=_admin_keyboard("week"))


@router.callback_query(F.data.startswith("admin:period:"))
async def switch_period(query: CallbackQuery, session) -> None:
    if query.from_user.id != ADMIN_TG_ID:
        await query.answer()
        return
    period = query.data.split(":", 2)[2]
    text = await _build_stats(session, period)
    await query.answer()
    await query.message.edit_text(text, reply_markup=_admin_keyboard(period))
