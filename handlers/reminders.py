from datetime import datetime

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy import select

from db.models import Reminder, User
from keyboards import get_main_menu_keyboard, get_tone_keyboard
from scheduler import add_reminder_job, remove_reminder_job

router = Router()


class ReminderStates(StatesGroup):
    waiting_for_time = State()


def _format_reminder_label(reminder_type: str) -> str:
    return {
        "morning": "Morning",
        "evening": "Evening",
        "weekly": "Weekly digest",
    }[reminder_type]


def _build_settings_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔔 Reminders", callback_data="settings:reminders"),
         InlineKeyboardButton(text="🎭 Change tone", callback_data="settings:tone")],
        [InlineKeyboardButton(text="← Back", callback_data="settings:back")],
    ])


def _build_reminders_keyboard(reminders: list[Reminder]) -> InlineKeyboardMarkup:
    rows = []
    active = {rem.type: rem for rem in reminders if rem.is_active}
    for reminder_type in ["morning", "evening", "weekly"]:
        reminder = active.get(reminder_type)
        if reminder is not None:
            rows.append([
                InlineKeyboardButton(
                    text=f"✅ {_format_reminder_label(reminder_type)} — {reminder.time}  ❌",
                    callback_data=f"reminder:remove:{reminder_type}",
                )
            ])
        else:
            rows.append([
                InlineKeyboardButton(
                    text=f"➕ {_format_reminder_label(reminder_type)} reminder",
                    callback_data=f"reminder:add:{reminder_type}",
                )
            ])

    rows.append([InlineKeyboardButton(text="← Back", callback_data="settings:back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


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
async def show_settings_menu(query: CallbackQuery) -> None:
    await query.answer()
    await query.message.answer("Settings", reply_markup=_build_settings_keyboard())


@router.callback_query(F.data == "settings:reminders")
async def show_reminders_menu(query: CallbackQuery, session) -> None:
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    if user is None:
        await query.answer("Пользователь не найден. Запусти /start.", show_alert=True)
        return

    reminders = await _get_user_reminders(user.id, session)
    await query.answer()
    await query.message.answer("Reminders", reply_markup=_build_reminders_keyboard(reminders))


@router.callback_query(F.data == "settings:tone")
async def change_tone(query: CallbackQuery) -> None:
    await query.answer()
    await query.message.answer("Выбери тон общения:", reply_markup=get_tone_keyboard())


@router.callback_query(F.data == "settings:back")
async def settings_back(query: CallbackQuery) -> None:
    await query.answer()
    await query.message.answer("Главное меню", reply_markup=get_main_menu_keyboard())


@router.callback_query(F.data.startswith("reminder:add:"))
async def add_reminder(query: CallbackQuery, state: FSMContext) -> None:
    reminder_type = query.data.split(":", 2)[2]
    await state.update_data(reminder_type=reminder_type)
    await state.set_state(ReminderStates.waiting_for_time)
    await query.answer()

    if reminder_type in {"morning", "evening"}:
        await query.message.answer("В какое время? Напиши в формате HH:MM (например 09:00)")
    else:
        await query.message.answer("В какой день и время? Напиши например: Mon 10:00")


@router.message(StateFilter(ReminderStates.waiting_for_time), F.text)
async def save_reminder_time(message: Message, state: FSMContext, session) -> None:
    data = await state.get_data()
    reminder_type = data.get("reminder_type")
    if reminder_type is None:
        await state.clear()
        return

    parsed = _parse_time_input(reminder_type, message.text)
    if parsed is None:
        prompt = (
            "Неверный формат. Напиши в формате HH:MM (например 09:00)"
            if reminder_type in {"morning", "evening"}
            else "Неверный формат. Напиши например: Mon 10:00"
        )
        await message.answer(prompt)
        return

    user = await session.scalar(select(User).filter_by(tg_id=message.from_user.id))
    if user is None:
        await message.answer("Пользователь не найден. Запусти /start.")
        await state.clear()
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
    await message.answer("Напоминание сохранено.", reply_markup=_build_reminders_keyboard(reminders))


@router.callback_query(F.data.startswith("reminder:remove:"))
async def remove_reminder(query: CallbackQuery, session) -> None:
    reminder_type = query.data.split(":", 2)[2]
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))
    if user is None:
        await query.answer("Пользователь не найден. Запусти /start.", show_alert=True)
        return

    reminder = await session.scalar(
        select(Reminder).filter_by(user_id=user.id, type=reminder_type, is_active=True)
    )
    if reminder is None:
        await query.answer("Напоминание не найдено.", show_alert=True)
        return

    reminder.is_active = False
    session.add(reminder)
    await session.commit()
    remove_reminder_job(reminder.id)

    reminders = await _get_user_reminders(user.id, session)
    await query.answer()
    await query.message.answer("Напоминание отключено.", reply_markup=_build_reminders_keyboard(reminders))
