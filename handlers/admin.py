import asyncio
from datetime import datetime, timedelta, timezone

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy import distinct, exists, func, select

from config import settings
from db.models import Feedback, Goal, Reminder, User, Win
from locales import t
from utils import edit_stored, split_tags


class AdminStates(StatesGroup):
    waiting_for_reply = State()

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


def _admin_keyboard(current: str, unread_feedback: int = 0) -> InlineKeyboardMarkup:
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
    feedback_label = f"💬 Фидбек ({unread_feedback} без ответа)" if unread_feedback else "💬 Фидбек"
    feedback_button = InlineKeyboardButton(text=feedback_label, callback_data="admin:feedback")
    return InlineKeyboardMarkup(inline_keyboard=[period_buttons, [moments_button], [users_button], [nudge_button], [feedback_button]])


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

    _raw_tag_rows = (await session.execute(
        select(Win.tag, func.count(Win.id))
        .where(Win.created_at >= start, Win.tag.isnot(None))
        .group_by(Win.tag)
    )).all()
    _tag_counts: dict[str, int] = {}
    for _raw_tag, _cnt in _raw_tag_rows:
        for _tg in split_tags(_raw_tag):
            _tag_counts[_tg] = _tag_counts.get(_tg, 0) + _cnt
    top_tags = ", ".join(
        f"{tg} ({cnt})" for tg, cnt in sorted(_tag_counts.items(), key=lambda x: -x[1])[:3]
    ) or "—"

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

    # Full tag breakdown (expand comma-separated tags)
    raw_tag_rows = (await session.execute(
        select(Win.tag, func.count(Win.id).label("cnt"))
        .where(Win.created_at >= start, Win.tag.isnot(None))
        .group_by(Win.tag)
    )).all()
    tag_expanded: dict[str, int] = {}
    for row in raw_tag_rows:
        for tg in split_tags(row.tag):
            tag_expanded[tg] = tag_expanded.get(tg, 0) + row.cnt
    tag_expanded_sorted = sorted(tag_expanded.items(), key=lambda x: -x[1])
    total_tagged = sum(tag_expanded.values())
    max_tag = tag_expanded_sorted[0][1] if tag_expanded_sorted else 1
    lines.append("")
    lines.append("<b>🏷 Теги</b>")
    if tag_expanded_sorted:
        for tg, cnt in tag_expanded_sorted:
            pct = round(cnt / total_tagged * 100) if total_tagged else 0
            emoji = _TAG_EMOJI.get(tg, "•")
            lines.append(f"  {emoji} {tg:<10} {_bar(cnt, max_tag)}  {cnt} ({pct}%)")
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


async def _unread_feedback_count(session) -> int:
    return await session.scalar(
        select(func.count(Feedback.id)).where(Feedback.reply_text.is_(None))
    )


@router.message(Command("admin"))
async def cmd_admin(message: Message, session) -> None:
    if message.from_user.id != settings.ADMIN_TG_ID:
        return
    text = await _build_stats(session, "week")
    unread = await _unread_feedback_count(session)
    await message.answer(text, reply_markup=_admin_keyboard("week", unread))


@router.callback_query(F.data.startswith("admin:period:"))
async def switch_period(query: CallbackQuery, session) -> None:
    if query.from_user.id != settings.ADMIN_TG_ID:
        await query.answer()
        return
    period = query.data.split(":", 2)[2]
    text = await _build_stats(session, period)
    unread = await _unread_feedback_count(session)
    await query.answer()
    await query.message.edit_text(text, reply_markup=_admin_keyboard(period, unread))


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


_FEEDBACK_PAGE = 8


def _feedback_list_keyboard(feedbacks: list, offset: int, total: int) -> InlineKeyboardMarkup:
    rows = []
    for fb in feedbacks:
        status = "✅ " if fb.reply_text else ""
        preview = fb.text[:35] + "…" if len(fb.text) > 35 else fb.text
        name = fb.username or str(fb.tg_id)
        rows.append([InlineKeyboardButton(
            text=f"{status}{name}: {preview}",
            callback_data=f"admin:feedback:view:{fb.id}",
        )])
    nav = []
    if offset > 0:
        nav.append(InlineKeyboardButton(text="← Старее", callback_data=f"admin:feedback:page:{offset - _FEEDBACK_PAGE}"))
    if offset + _FEEDBACK_PAGE < total:
        nav.append(InlineKeyboardButton(text="Новее →", callback_data=f"admin:feedback:page:{offset + _FEEDBACK_PAGE}"))
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton(text="← Назад", callback_data="admin:period:week")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _feedback_view_keyboard(feedback_id: int, is_replied: bool) -> InlineKeyboardMarkup:
    rows = []
    if not is_replied:
        rows.append([InlineKeyboardButton(text="💬 Ответить", callback_data=f"admin:feedback:reply:{feedback_id}")])
    rows.append([InlineKeyboardButton(text="← К списку", callback_data="admin:feedback")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def _render_feedback_list(query: CallbackQuery, session, offset: int = 0) -> None:
    total = await session.scalar(select(func.count(Feedback.id)))
    unread = await _unread_feedback_count(session)
    feedbacks = (await session.scalars(
        select(Feedback).order_by(Feedback.created_at.desc()).offset(offset).limit(_FEEDBACK_PAGE)
    )).all()
    header = f"<b>💬 Фидбек — {total} сообщений, {unread} без ответа</b>"
    await query.message.edit_text(header, reply_markup=_feedback_list_keyboard(feedbacks, offset, total))


@router.callback_query(F.data == "admin:feedback")
async def show_feedback_list(query: CallbackQuery, session) -> None:
    if query.from_user.id != settings.ADMIN_TG_ID:
        await query.answer()
        return
    await query.answer()
    await _render_feedback_list(query, session, offset=0)


@router.callback_query(F.data.startswith("admin:feedback:page:"))
async def feedback_page(query: CallbackQuery, session) -> None:
    if query.from_user.id != settings.ADMIN_TG_ID:
        await query.answer()
        return
    try:
        offset = int(query.data.split(":", 3)[3])
    except (ValueError, IndexError):
        await query.answer()
        return
    await query.answer()
    await _render_feedback_list(query, session, offset=offset)


@router.callback_query(F.data.startswith("admin:feedback:view:"))
async def view_feedback(query: CallbackQuery, session) -> None:
    if query.from_user.id != settings.ADMIN_TG_ID:
        await query.answer()
        return
    try:
        feedback_id = int(query.data.split(":", 3)[3])
    except (ValueError, IndexError):
        await query.answer()
        return

    fb = await session.scalar(select(Feedback).where(Feedback.id == feedback_id))
    if fb is None:
        await query.answer("Фидбек не найден", show_alert=True)
        return

    date_str = fb.created_at.strftime("%d.%m.%Y %H:%M")
    name = fb.username or str(fb.tg_id)
    lines = [
        f"<b>💬 Фидбек #{fb.id}</b>",
        f"От: {name} (tg_id: {fb.tg_id})",
        f"Дата: {date_str}",
        "",
        fb.text,
    ]
    if fb.reply_text:
        replied_str = fb.replied_at.strftime("%d.%m.%Y %H:%M") if fb.replied_at else "—"
        lines += ["", f"✅ <b>Ответ отправлен</b> ({replied_str}):", fb.reply_text]

    await query.answer()
    await query.message.edit_text("\n".join(lines), reply_markup=_feedback_view_keyboard(fb.id, bool(fb.reply_text)))


@router.callback_query(F.data.startswith("admin:feedback:reply:"))
async def start_feedback_reply(query: CallbackQuery, state: FSMContext, session) -> None:
    if query.from_user.id != settings.ADMIN_TG_ID:
        await query.answer()
        return
    try:
        feedback_id = int(query.data.split(":", 3)[3])
    except (ValueError, IndexError):
        await query.answer()
        return

    fb = await session.scalar(select(Feedback).where(Feedback.id == feedback_id))
    if fb is None:
        await query.answer("Фидбек не найден", show_alert=True)
        return

    await state.set_state(AdminStates.waiting_for_reply)
    await state.update_data(feedback_id=feedback_id, feedback_msg_id=query.message.message_id, chat_id=query.message.chat.id)
    await query.answer()
    await query.message.edit_text(
        f"Напиши ответ пользователю {fb.username or fb.tg_id}:\n\n<i>{fb.text[:200]}</i>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="Отмена", callback_data=f"admin:feedback:view:{feedback_id}")
        ]]),
    )


@router.message(StateFilter(AdminStates.waiting_for_reply), F.text)
async def send_feedback_reply(message: Message, state: FSMContext, session) -> None:
    if message.from_user.id != settings.ADMIN_TG_ID:
        return

    data = await state.get_data()
    feedback_id = data.get("feedback_id")
    msg_id = data.get("feedback_msg_id")
    chat_id = data.get("chat_id")

    fb = await session.scalar(select(Feedback).where(Feedback.id == feedback_id))
    if fb is None:
        await state.clear()
        return

    reply_text = message.text.strip()

    user = await session.scalar(select(User).where(User.id == fb.user_id)) if fb.user_id else None
    lang = getattr(user, "language", "ru") if user else "ru"

    try:
        await message.bot.send_message(fb.tg_id, t(lang, "feedback_reply", text=reply_text))
        delivered = True
    except Exception:
        delivered = False

    fb.reply_text = reply_text
    fb.replied_at = datetime.now(timezone.utc)
    session.add(fb)
    await session.commit()
    await state.clear()

    status = "✅ Доставлено" if delivered else "⚠️ Не доставлено (возможно, пользователь заблокировал бота)"
    await edit_stored(
        message.bot, chat_id, msg_id,
        f"Ответ отправлен\n\n{status}",
        InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="← К списку", callback_data="admin:feedback")
        ]]),
    )
