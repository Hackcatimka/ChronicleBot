import logging
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select

from ai import ask_weekly_narrative
from locales import t

from db.engine import async_session
from db.models import Reminder, User, Win

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()


def _make_job_id(reminder_id: int) -> str:
    return f"reminder_{reminder_id}"


def _build_trigger(reminder: Reminder) -> CronTrigger:
    if reminder.type in {"morning", "evening"}:
        hour, minute = reminder.time.split(":")
        return CronTrigger(hour=int(hour), minute=int(minute))

    if reminder.type == "weekly":
        parts = reminder.time.split()
        day_part = parts[0].lower()
        hour, minute = parts[1].split(":")
        return CronTrigger(day_of_week=day_part, hour=int(hour), minute=int(minute))

    raise ValueError("Unknown reminder type")


async def _send_weekly_digest(user: User, session) -> str:
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    wins = (await session.scalars(
        select(Win).filter(Win.user_id == user.id, Win.created_at >= cutoff).order_by(Win.created_at)
    )).all()

    if wins:
        try:
            wins_with_tags = [(win.raw_text, win.tag or "other") for win in wins]
            return await ask_weekly_narrative(user.tone, wins_with_tags, user.language)
        except Exception:
            logger.exception("Failed to generate AI weekly narrative for user %s", user.id)

    lang = getattr(user, "language", "en")
    lines = [
        t(lang, "weekly_digest_title"),
        "",
        t(lang, "weekly_digest_summary", count=len(wins)),
    ]
    if wins:
        for win in wins:
            lines.append(f"— {win.raw_text}")
    else:
        lines.append(t(lang, "weekly_digest_no_wins"))
    lines.append("")
    lines.append(t(lang, "weekly_digest_encouragement"))
    return "\n".join(lines)


async def _send_reminder(reminder_id: int, bot) -> None:
    async with async_session() as session:
        reminder = await session.scalar(select(Reminder).filter_by(id=reminder_id, is_active=True))
        if reminder is None:
            try:
                scheduler.remove_job(_make_job_id(reminder_id))
            except Exception:
                pass
            return

        user = await session.scalar(select(User).filter_by(id=reminder.user_id))
        if user is None:
            return

        if reminder.type == "morning":
            text = t(user.language, "morning_checkin")
        elif reminder.type == "evening":
            text = t(user.language, "evening_checkin")
        elif reminder.type == "weekly":
            text = await _send_weekly_digest(user, session)
        else:
            return

        try:
            await bot.send_message(user.tg_id, text)
        except Exception as exc:
            logger.exception("Failed to send reminder %s: %s", reminder_id, exc)


def add_reminder_job(reminder: Reminder, bot) -> None:
    job_id = _make_job_id(reminder.id)
    trigger = _build_trigger(reminder)
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
    scheduler.add_job(_send_reminder, trigger, args=[reminder.id, bot], id=job_id, replace_existing=True)


def remove_reminder_job(reminder_id: int) -> None:
    job_id = _make_job_id(reminder_id)
    try:
        scheduler.remove_job(job_id)
    except Exception:
        pass


async def init_scheduler(bot) -> None:
    async with async_session() as session:
        reminders = (await session.scalars(select(Reminder).filter_by(is_active=True))).all()
        for reminder in reminders:
            add_reminder_job(reminder, bot)
    scheduler.start()
