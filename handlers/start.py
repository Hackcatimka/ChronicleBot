from datetime import datetime

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from db.models import User
from keyboards import get_main_menu_keyboard, get_tone_keyboard

router = Router()


async def _show_main_menu(message: Message, session) -> None:
    await message.answer("Главное меню", reply_markup=get_main_menu_keyboard())


@router.message(Command("start"))
async def start_handler(message: Message, session) -> None:
    user = await session.scalar(select(User).filter_by(tg_id=message.from_user.id))
    if user is None:
        await message.answer("Привет! Выбери тон общения:", reply_markup=get_tone_keyboard())
        return

    user.last_active_at = datetime.utcnow()
    session.add(user)
    await session.commit()
    await _show_main_menu(message, session)


@router.callback_query(F.data.startswith("tone:"))
async def tone_callback(query: CallbackQuery, session) -> None:
    tone = query.data.split(":", 1)[1]
    user = await session.scalar(select(User).filter_by(tg_id=query.from_user.id))

    if user is None:
        user = User(
            tg_id=query.from_user.id,
            name=query.from_user.full_name or "Telegram User",
            tone=tone,
        )
        session.add(user)
    else:
        user.tone = tone
        user.last_active_at = datetime.utcnow()
        session.add(user)

    await session.commit()
    await query.answer()
    await query.message.answer("Отлично! Теперь главное меню:", reply_markup=get_main_menu_keyboard())
