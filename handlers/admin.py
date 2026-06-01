import asyncio
from datetime import datetime, timedelta, timezone

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy import distinct, exists, func, select

from config import settings
from db.models import Goal, Reminder, User, Win
from locales import t

_TAG_EMOJI = {
    "work": "💼", "health": "💪", "learning": "📚", "personal": "🙂",
    "creative": "🎨", "social": "👥", "finance": "💰", "other": "🔹",
}

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


def _bar(value: int, max_value: int, width: int = 8) -> str:
    if max_value == 0:
        return "░" * width
    filled = round(value / max_value * width)
    return "█" * filled + "░" * (width - filled)


def _admin_keyboard(current: str) -> InlineKeyboardMarkup:
    periods = ["today", "week", "month", "year"]
    period_buttons = [
        InlineKeyboardButton(
            text=("▸ " if p == current else "") + _period_label(p),
            callback_data=f"admin:period:{p}",
        )
        for p in periods
    ]
    moments_button = InlineKeyboardButton(text="📊 Моменты подробно", callback_data=f"admin:moments:{current}")
    users_button = InlineKeyboardButton(text="👥 Пользователи подробно", callback_data=f"admin:users:{current}")
    nudge_button = InlineKeyboardButton(text="📣 Напомнить молчащим 24ч+", callback_data="admin:nudge")
    return InlineKeyboardMarkup(inline_keyboard=[period_buttons, [moments_button], [users_button], [nudge_button]])


def _moments_detail_keyboard(period: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="← Назад", callback_data=f"admin:period:{period}")
    ]])


def _users_detail_keyboard(period: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="← Назад", callback_data=f"admin:period:{period}")
    ]])


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
        f"  Активных (есть моменты): <b>{active_users}</b>",
        f"  Без единого момента: <b>{users_no_wins}</b>",
        f"  Языки: {lang_str}",
        "",
        "<b>🏆 Моменты</b>",
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


async def _build_moments_detail(session, period: str) -> str:
    start, now = _period_range(period)
    label = _period_label(period)
    lines = [f"<b>📊 Моменты подробно — {label}</b>"]

    # Daily trend: last 7 days or day-by-day if period == today
    trend_days = 7 if period != "today" else 1
    trend_start = now - timedelta(days=trend_days)
    daily_rows = (await session.execute(
        select(
            func.date_trunc("day", Win.created_at).label("day"),
            func.count(Win.id).label("cnt"),
        )
        .where(Win.created_at >= trend_start)
        .group_by("day")
        .order_by("day")
    )).all()
    day_map = {row.day.date(): row.cnt for row in daily_rows}
    days_range = [(now.date() - timedelta(days=trend_days - 1 - i)) for i in range(trend_days)]
    max_day = max((day_map.get(d, 0) for d in days_range), default=1) or 1
    lines.append("")
    lines.append("<b>📈 Тренд по дням</b>")
    for d in days_range:
        cnt = day_map.get(d, 0)
        lines.append(f"  {_RU_DAYS[d.weekday()]} {d.strftime('%d.%m')}  {_bar(cnt, max_day)}  {cnt}")

    # Full tag breakdown
    tag_rows = (await session.execute(
        select(Win.tag, func.count(Win.id).label("cnt"))
        .where(Win.created_at >= start, Win.tag.isnot(None))
        .group_by(Win.tag)
        .order_by(func.count(Win.id).desc())
    )).all()
    total_tagged = sum(r.cnt for r in tag_rows)
    max_tag = tag_rows[0].cnt if tag_rows else 1
    lines.append("")
    lines.append("<b>🏷 Теги</b>")
    if tag_rows:
        for row in tag_rows:
            pct = round(row.cnt / total_tagged * 100) if total_tagged else 0
            emoji = _TAG_EMOJI.get(row.tag, "•")
            lines.append(f"  {emoji} {row.tag:<10} {_bar(row.cnt, max_tag)}  {row.cnt} ({pct}%)")
    else:
        lines.append("  нет данных")

    # Engagement buckets
    user_counts = (await session.execute(
        select(Win.user_id, func.count(Win.id).label("cnt"))
        .where(Win.created_at >= start)
        .group_by(Win.user_id)
    )).all()
    buckets = {"1": 0, "2–5": 0, "6–15": 0, "16+": 0}
    for row in user_counts:
        if row.cnt == 1:
            buckets["1"] += 1
        elif row.cnt <= 5:
            buckets["2–5"] += 1
        elif row.cnt <= 15:
            buckets["6–15"] += 1
        else:
            buckets["16+"] += 1
    total_active = sum(buckets.values()) or 1
    lines.append("")
    lines.append("<b>🎯 Вовлечённость</b>")
    for label_key, cnt in buckets.items():
        pct = round(cnt / total_active * 100)
        lines.append(f"  {label_key} момент(ов): <b>{cnt}</b> юз. ({pct}%)")

    # Time of day (UTC)
    hour_rows = (await session.execute(
        select(
            func.extract("hour", Win.created_at).label("hr"),
            func.count(Win.id).label("cnt"),
        )
        .where(Win.created_at >= start)
        .group_by("hr")
    )).all()
    tod = {"🌙 Ночь 0–6": 0, "🌅 Утро 6–12": 0, "☀️ День 12–18": 0, "🌆 Вечер 18–24": 0}
    for row in hour_rows:
        hr = int(row.hr)
        if hr < 6:
            tod["🌙 Ночь 0–6"] += row.cnt
        elif hr < 12:
            tod["🌅 Утро 6–12"] += row.cnt
        elif hr < 18:
            tod["☀️ День 12–18"] += row.cnt
        else:
            tod["🌆 Вечер 18–24"] += row.cnt
    total_tod = sum(tod.values()) or 1
    max_tod = max(tod.values(), default=1) or 1
    lines.append("")
    lines.append("<b>🕐 Время суток (UTC)</b>")
    for tod_label, cnt in tod.items():
        pct = round(cnt / total_tod * 100)
        lines.append(f"  {tod_label}  {_bar(cnt, max_tod)}  {pct}%")

    return "\n".join(lines)


_TONE_EMOJI = {"friend": "👋", "coach": "💪", "mirror": "🪞"}
_RU_DAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]


async def _build_users_detail(session, period: str) -> str:
    now = datetime.now(timezone.utc)
    lines = ["<b>👥 Пользователи подробно</b>"]

    # Registration trend — last 7 days
    trend_start = now - timedelta(days=7)
    reg_rows = (await session.execute(
        select(
            func.date_trunc("day", User.created_at).label("day"),
            func.count(User.id).label("cnt"),
        )
        .where(User.created_at >= trend_start)
        .group_by("day")
        .order_by("day")
    )).all()
    day_map = {row.day.date(): row.cnt for row in reg_rows}
    days_range = [(now.date() - timedelta(days=6 - i)) for i in range(7)]
    max_reg = max((day_map.get(d, 0) for d in days_range), default=1) or 1
    lines.append("")
    lines.append("<b>📈 Регистрации (7 дней)</b>")
    for d in days_range:
        cnt = day_map.get(d, 0)
        lines.append(f"  {_RU_DAYS[d.weekday()]} {d.strftime('%d.%m')}  {_bar(cnt, max_reg)}  {cnt}")

    # Retention D1 / D7 / D30
    lines.append("")
    lines.append("<b>🔄 Retention</b>")
    for days, label in [(1, "Day-1 "), (7, "Day-7 "), (30, "Day-30")]:
        cutoff = now - timedelta(days=days)
        total = await session.scalar(select(func.count(User.id)).where(User.created_at < cutoff))
        if total:
            retained = await session.scalar(
                select(func.count(User.id)).where(
                    User.created_at < cutoff,
                    exists(
                        select(Win.id).where(
                            Win.user_id == User.id,
                            Win.created_at >= User.created_at + timedelta(days=days),
                        )
                    ),
                )
            )
            pct = round(retained / total * 100)
            lines.append(f"  {label}  {_bar(retained, total)}  {pct}% ({retained}/{total})")
        else:
            lines.append(f"  {label}  — нет данных")

    # Churn by silence
    lines.append("")
    lines.append("<b>😶 Отток (тишина)</b>")
    for days, label in [(7, "7 дн "), (14, "14 дн"), (30, "30 дн")]:
        cutoff = now - timedelta(days=days)
        silent = await session.scalar(
            select(func.count(User.id)).where(
                User.last_active_at < cutoff,
                User.created_at < cutoff,
            )
        )
        lines.append(f"  {label}  не писали: <b>{silent}</b>")

    # Tone breakdown
    tone_rows = (await session.execute(
        select(User.tone, func.count(User.id).label("cnt"))
        .group_by(User.tone)
        .order_by(func.count(User.id).desc())
    )).all()
    total_users = sum(r.cnt for r in tone_rows) or 1
    max_tone = tone_rows[0].cnt if tone_rows else 1
    lines.append("")
    lines.append("<b>🎭 Тон</b>")
    for row in tone_rows:
        pct = round(row.cnt / total_users * 100)
        emoji = _TONE_EMOJI.get(row.tone, "•")
        lines.append(f"  {emoji} {row.tone:<8} {_bar(row.cnt, max_tone)}  {row.cnt} ({pct}%)")

    return "\n".join(lines)


@router.message(Command("admin"))
async def cmd_admin(message: Message, session) -> None:
    if message.from_user.id != settings.ADMIN_TG_ID:
        return
    text = await _build_stats(session, "week")
    await message.answer(text, reply_markup=_admin_keyboard("week"))


@router.callback_query(F.data.startswith("admin:period:"))
async def switch_period(query: CallbackQuery, session) -> None:
    if query.from_user.id != settings.ADMIN_TG_ID:
        await query.answer()
        return
    period = query.data.split(":", 2)[2]
    text = await _build_stats(session, period)
    await query.answer()
    await query.message.edit_text(text, reply_markup=_admin_keyboard(period))


@router.callback_query(F.data.startswith("admin:users:"))
async def show_users_detail(query: CallbackQuery, session) -> None:
    if query.from_user.id != settings.ADMIN_TG_ID:
        await query.answer()
        return
    period = query.data.split(":", 2)[2]
    await query.answer()
    text = await _build_users_detail(session, period)
    await query.message.edit_text(text, reply_markup=_users_detail_keyboard(period))


@router.callback_query(F.data.startswith("admin:moments:"))
async def show_moments_detail(query: CallbackQuery, session) -> None:
    if query.from_user.id != settings.ADMIN_TG_ID:
        await query.answer()
        return
    period = query.data.split(":", 2)[2]
    await query.answer()
    text = await _build_moments_detail(session, period)
    await query.message.edit_text(text, reply_markup=_moments_detail_keyboard(period))


@router.callback_query(F.data == "admin:nudge")
async def send_nudge(query: CallbackQuery, session) -> None:
    if query.from_user.id != settings.ADMIN_TG_ID:
        await query.answer()
        return

    await query.answer("Отправляю...")

    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    users = (await session.scalars(
        select(User).where(User.last_active_at < cutoff)
    )).all()

    sent = 0
    failed = 0
    bot = query.bot
    for user in users:
        text = t(user.language, "inactivity_nudge")
        try:
            await bot.send_message(user.tg_id, text)
            sent += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)

    await query.message.answer(
        f"📣 Рассылка завершена\n\nОтправлено: <b>{sent}</b>\nНе доставлено: <b>{failed}</b>"
    )
