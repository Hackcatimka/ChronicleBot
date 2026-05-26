from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_tone_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Friend", callback_data="tone:friend"),
         InlineKeyboardButton(text="Coach", callback_data="tone:coach"),
         InlineKeyboardButton(text="Mirror", callback_data="tone:mirror")],
    ])


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏆 Record a win", callback_data="menu:record_win"),
         InlineKeyboardButton(text="🎯 My goals", callback_data="menu:goals")],
        [InlineKeyboardButton(text="🔮 What changed", callback_data="menu:changed"),
         InlineKeyboardButton(text="📊 Stats", callback_data="menu:stats")],
        [InlineKeyboardButton(text="⏪ Time machine", callback_data="menu:time_machine"),
         InlineKeyboardButton(text="⚙️ Settings", callback_data="menu:settings")],
    ])


def get_win_confirmation_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Save", callback_data="save_win"),
         InlineKeyboardButton(text="🎯 Link to goal", callback_data="link_goal")],
        [InlineKeyboardButton(text="✏️ Edit", callback_data="edit_win"),
         InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_win")],
    ])
