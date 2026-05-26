from datetime import datetime

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from db.models import Reminder, User
from keyboards import get_main_menu_keyboard, get_reminders_keyboard, get_settings_keyboard, get_tone_keyboard
from locales import t
from scheduler import add_reminder_job, remove_reminder_job

router = Router()


class ReminderStates(StatesGroup):
    waiting_for_time = State()


def _parse_time_input(reminder_type: str, text: str) -> str | None:
    value = text.strip()
    if reminder_type in {"morning", "evening"}:
        try:
            parsed = datetime.strptime(value, "%H:%M")
            return parsed.strftime("%H:%M")
        except ValueError:
            return None

    if reminder_type == "weekly":
        parts = value.split()
        if len(parts) != 2:
            return None
        day, time_part = parts
        day_key = day.strip()[:3].lower()
        valid_days = {
            "mon": "Mon",
            "tue": "Tue",
            "wed": "Wed",
            "thu": "Thu",
            "fri": "Fri",
            "sat": "Sat",
            "sun": "Sun",
        }
        if day_key not in valid_days:
            return None
        try:
            parsed = datetime.strptime(time_part, "%H:%M")
        except ValueError:
            return None
        return f"{valid_days[day_key]} {parsed.strftime('%H:%M')}"

    return None


async def _get_user_reminders(user_id: int, session):
    reminders = await session.scalars(select(Reminder).filter_by(user_id=user_id))
    return reminders.all()


@router.callback_query(F.data == "menu:settings")
async def show_settings_menu(query: CallbackQuery, session) -> None:
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    await query.answer()
    await query.message.answer(t(lang, "settings_title"), reply_markup=get_settings_keyboard(lang))


@router.callback_query(F.data == "settings:reminders")
async def show_reminders_menu(query: CallbackQuery, session) -> None:
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    if user is None:
        await query.answer(t("en", "user_not_found"), show_alert=True)
        return

    lang = getattr(user, "language", "en")
    reminders = await _get_user_reminders(user.id, session)
    await query.answer()
    await query.message.answer(t(lang, "reminders_title"), reply_markup=get_reminders_keyboard(lang, reminders))


@router.callback_query(F.data == "settings:tone")
async def change_tone(query: CallbackQuery, session) -> None:
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    await query.answer()
    await query.message.answer(t(lang, "choose_tone"), reply_markup=get_tone_keyboard(lang))


@router.callback_query(F.data == "settings:back")
async def settings_back(query: CallbackQuery, session) -> None:
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    await query.answer()
    await query.message.answer(t(lang, "back_to_menu"), reply_markup=get_main_menu_keyboard(lang))


@router.callback_query(F.data.startswith("reminder:add:"))
async def add_reminder(query: CallbackQuery, state: FSMContext, session) -> None:
    reminder_type = query.data.split(":", 2)[2]
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    await state.update_data(reminder_type=reminder_type)
    await state.set_state(ReminderStates.waiting_for_time)
    await query.answer()

    prompt = (
        t(lang, "reminder_time_prompt")
        if reminder_type in {"morning", "evening"}
        else t(lang, "reminder_weekly_prompt")
    )
    await query.message.answer(prompt)


@router.message(StateFilter(ReminderStates.waiting_for_time), F.text)
async def save_reminder_time(message: Message, state: FSMContext, session) -> None:
    data = await state.get_data()
    reminder_type = data.get("reminder_type")
    if reminder_type is None:
        await state.clear()
        return

    user = await session.scalar(select(User).filter_by(tg_id=message.from_user.id))
    if user is None:
        await message.answer(t("en", "user_not_found"))
        await state.clear()
        return

    lang = getattr(user, "language", "en")
    parsed = _parse_time_input(reminder_type, message.text)
    if parsed is None:
        prompt = (
            t(lang, "reminder_invalid")
            if reminder_type in {"morning", "evening"}
            else t(lang, "reminder_weekly_invalid")
        )
        await message.answer(prompt)
        return

    reminder = await session.scalar(
        select(Reminder).filter_by(user_id=user.id, type=reminder_type, is_active=True)
    )
    if reminder is not None:
        reminder.time = parsed
    else:
        reminder = Reminder(user_id=user.id, type=reminder_type, time=parsed, is_active=True)
        session.add(reminder)

    await session.commit()
    add_reminder_job(reminder, message.bot)

    reminders = await _get_user_reminders(user.id, session)
    await state.clear()
    await message.answer(t(lang, "reminder_saved"), reply_markup=get_reminders_keyboard(lang, reminders))


@router.callback_query(F.data.startswith("reminder:remove:"))
async def remove_reminder(query: CallbackQuery, session) -> None:
    reminder_type = query.data.split(":", 2)[2]
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    if user is None:
        await query.answer(t("en", "user_not_found"), show_alert=True)
        return

    lang = getattr(user, "language", "en")
    reminder = await session.scalar(
        select(Reminder).filter_by(user_id=user.id, type=reminder_type, is_active=True)
    )
    if reminder is None:
        await query.answer(t(lang, "reminder_not_found"), show_alert=True)
        return

    reminder.is_active = False
    session.add(reminder)
    await session.commit()
    remove_reminder_job(reminder.id)

    reminders = await _get_user_reminders(user.id, session)
    await query.answer()
    await query.message.answer(t(lang, "reminder_removed"), reply_markup=get_reminders_keyboard(lang, reminders))
