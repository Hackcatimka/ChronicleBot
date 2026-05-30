from datetime import datetime

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy import delete, select

from db.models import Goal, Reminder, User, Win
from keyboards import (
    get_delete_confirm_keyboard,
    get_language_keyboard,
    get_main_menu_keyboard,
    get_reminders_keyboard,
    get_settings_keyboard,
    get_settings_language_keyboard,
    get_tone_keyboard,
)
from locales import t
from scheduler import add_reminder_job, remove_reminder_job
from utils import edit_or_answer, edit_stored

router = Router()


class ReminderStates(StatesGroup):
    waiting_for_time = State()
    waiting_for_timezone = State()


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
    await edit_or_answer(query.message, t(lang, "settings_title"), get_settings_keyboard(lang))


@router.callback_query(F.data == "settings:reminders")
async def show_reminders_menu(query: CallbackQuery, session) -> None:
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    if user is None:
        await query.answer(t(lang, "user_not_found"), show_alert=True)
        return

    reminders = await _get_user_reminders(user.id, session)
    await query.answer()
    await edit_or_answer(query.message, t(lang, "reminders_title"), get_reminders_keyboard(lang, reminders))


@router.callback_query(F.data == "settings:tone")
async def change_tone(query: CallbackQuery, session) -> None:
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    await query.answer()
    await edit_or_answer(query.message, t(lang, "choose_tone"), get_tone_keyboard(lang))


@router.callback_query(F.data == "settings:back")
async def settings_back(query: CallbackQuery, session) -> None:
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    await query.answer()
    await edit_or_answer(query.message, t(lang, "back_to_menu"), get_main_menu_keyboard(lang))


@router.callback_query(F.data == "settings:show")
async def settings_show(query: CallbackQuery, session) -> None:
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    await query.answer()
    await edit_or_answer(query.message, t(lang, "settings_title"), get_settings_keyboard(lang))


@router.callback_query(F.data == "settings:timezone")
async def show_timezone_settings(query: CallbackQuery, state: FSMContext, session) -> None:
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    if user is None:
        await query.answer(t(lang, "user_not_found"), show_alert=True)
        return
    offset = getattr(user, "utc_offset", 0)
    offset_str = f"+{offset}" if offset >= 0 else str(offset)
    await state.set_state(ReminderStates.waiting_for_timezone)
    await query.answer()
    sent = await edit_or_answer(query.message, t(lang, "timezone_prompt", offset=offset_str))
    await state.update_data(bot_msg_id=sent.message_id, chat_id=sent.chat.id)


@router.message(StateFilter(ReminderStates.waiting_for_timezone), F.text)
async def save_timezone(message: Message, state: FSMContext, session) -> None:
    user = await session.scalar(select(User).filter_by(tg_id=message.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    data = await state.get_data()
    msg_id = data.get("bot_msg_id")

    if user is None:
        await edit_stored(message.bot, message.chat.id, msg_id, t(lang, "user_not_found"))
        await state.clear()
        return

    text = message.text.strip()
    try:
        offset = int(text.replace(" ", ""))
        if not (-12 <= offset <= 14):
            raise ValueError
    except ValueError:
        await edit_stored(message.bot, message.chat.id, msg_id, t(lang, "timezone_invalid"))
        return

    user.utc_offset = offset
    session.add(user)
    await session.commit()

    reminders = await _get_user_reminders(user.id, session)
    for reminder in reminders:
        if reminder.is_active:
            add_reminder_job(reminder, message.bot, offset)

    offset_str = f"+{offset}" if offset >= 0 else str(offset)
    await state.clear()
    await edit_stored(message.bot, message.chat.id, msg_id, t(lang, "timezone_saved", offset=offset_str), get_settings_keyboard(lang))


@router.callback_query(F.data == "settings:language")
async def show_language_settings(query: CallbackQuery, session) -> None:
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    await query.answer()
    await edit_or_answer(query.message, t(lang, "settings_language_title"), get_settings_language_keyboard(lang))


@router.callback_query(F.data.startswith("settings:lang:"))
async def change_language(query: CallbackQuery, session) -> None:
    new_lang = query.data.split(":", 2)[2]
    if new_lang not in {"en", "ru"}:
        await query.answer()
        return
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    if user is None:
        await query.answer()
        return
    user.language = new_lang
    session.add(user)
    await session.commit()
    await query.answer()
    await edit_or_answer(query.message, t(new_lang, "language_changed"), get_settings_keyboard(new_lang))


@router.callback_query(F.data == "settings:delete")
async def delete_data_step1(query: CallbackQuery, session) -> None:
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    await query.answer()
    await edit_or_answer(query.message, t(lang, "delete_confirm_1"), get_delete_confirm_keyboard(lang, 1))


@router.callback_query(F.data == "settings:delete:1")
async def delete_data_step2(query: CallbackQuery, session) -> None:
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    await query.answer()
    await edit_or_answer(query.message, t(lang, "delete_confirm_2"), get_delete_confirm_keyboard(lang, 2))


@router.callback_query(F.data == "settings:delete:2")
async def delete_data_step3(query: CallbackQuery, session) -> None:
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    await query.answer()
    await edit_or_answer(query.message, t(lang, "delete_confirm_3"), get_delete_confirm_keyboard(lang, 3))


@router.callback_query(F.data == "settings:delete:3")
async def delete_data_confirmed(query: CallbackQuery, state: FSMContext, session) -> None:
    from handlers.start import _WELCOME_NEW
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    if user is None:
        await query.answer()
        return
    reminders_to_cancel = (await session.scalars(
        select(Reminder).filter_by(user_id=user.id, is_active=True)
    )).all()
    for reminder in reminders_to_cancel:
        remove_reminder_job(reminder.id)
    await session.delete(user)
    await session.commit()
    await state.clear()
    await query.answer()
    await edit_or_answer(query.message, _WELCOME_NEW, get_language_keyboard())


@router.callback_query(F.data.startswith("reminder:add:"))
async def add_reminder(query: CallbackQuery, state: FSMContext, session) -> None:
    reminder_type = query.data.split(":", 2)[2]
    if reminder_type not in {"morning", "evening", "weekly"}:
        await query.answer()
        return
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
    sent = await edit_or_answer(query.message, prompt)
    await state.update_data(bot_msg_id=sent.message_id, chat_id=sent.chat.id)


@router.message(StateFilter(ReminderStates.waiting_for_time), F.text)
async def save_reminder_time(message: Message, state: FSMContext, session) -> None:
    data = await state.get_data()
    reminder_type = data.get("reminder_type")
    msg_id = data.get("bot_msg_id")
    if reminder_type is None:
        await state.clear()
        return

    user = await session.scalar(select(User).filter_by(tg_id=message.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    if user is None:
        await edit_stored(message.bot, message.chat.id, msg_id, t(lang, "user_not_found"))
        await state.clear()
        return
    parsed = _parse_time_input(reminder_type, message.text)
    if parsed is None:
        prompt = (
            t(lang, "reminder_invalid")
            if reminder_type in {"morning", "evening"}
            else t(lang, "reminder_weekly_invalid")
        )
        await edit_stored(message.bot, message.chat.id, msg_id, prompt)
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
    add_reminder_job(reminder, message.bot, getattr(user, "utc_offset", 0))

    reminders = await _get_user_reminders(user.id, session)
    await state.clear()
    await edit_stored(message.bot, message.chat.id, msg_id, t(lang, "reminder_saved"), get_reminders_keyboard(lang, reminders))


@router.callback_query(F.data.startswith("reminder:remove:"))
async def remove_reminder(query: CallbackQuery, session) -> None:
    reminder_type = query.data.split(":", 2)[2]
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    lang = getattr(user, "language", "en") if user else "en"
    if user is None:
        await query.answer(t(lang, "user_not_found"), show_alert=True)
        return

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
    await edit_or_answer(query.message, t(lang, "reminder_removed"), get_reminders_keyboard(lang, reminders))
