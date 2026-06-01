from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from locales import t


def get_language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("en", "language_english"), callback_data="lang:en"),
         InlineKeyboardButton(text=t("en", "language_russian"), callback_data="lang:ru")],
    ])


def get_tone_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "tone_friend"), callback_data="tone:friend"),
         InlineKeyboardButton(text=t(lang, "tone_coach"), callback_data="tone:coach"),
         InlineKeyboardButton(text=t(lang, "tone_mirror"), callback_data="tone:mirror")],
    ])


def get_main_menu_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=t(lang, "btn_stats"), callback_data="menu:stats"),
            InlineKeyboardButton(text=t(lang, "btn_goals"), callback_data="menu:goals"),
        ],
        [
            InlineKeyboardButton(text=t(lang, "btn_reflect"), callback_data="menu:reflect"),
            InlineKeyboardButton(text=t(lang, "btn_time_machine"), callback_data="menu:time_machine"),
        ],
        [
            InlineKeyboardButton(text=t(lang, "btn_search"), callback_data="menu:search"),
            InlineKeyboardButton(text=t(lang, "btn_settings"), callback_data="menu:settings"),
        ],
    ])


def get_win_confirmation_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "btn_save"), callback_data="save_win"),
         InlineKeyboardButton(text=t(lang, "btn_link_goal"), callback_data="link_goal")],
        [InlineKeyboardButton(text=t(lang, "btn_edit"), callback_data="edit_win"),
         InlineKeyboardButton(text=t(lang, "btn_cancel"), callback_data="cancel_win")],
    ])


def get_intent_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "btn_add_as_goal"), callback_data="intent:as_goal"),
         InlineKeyboardButton(text=t(lang, "btn_save_as_win"), callback_data="intent:as_win")],
        [InlineKeyboardButton(text=t(lang, "btn_edit"), callback_data="edit_win"),
         InlineKeyboardButton(text=t(lang, "btn_cancel"), callback_data="cancel_win")],
    ])


def get_stats_menu_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "btn_this_week"), callback_data="stats:week"),
         InlineKeyboardButton(text=t(lang, "btn_this_month"), callback_data="stats:month")],
        [InlineKeyboardButton(text=t(lang, "btn_all_time"), callback_data="stats:all"),
         InlineKeyboardButton(text=t(lang, "btn_compare"), callback_data="stats:compare")],
        [InlineKeyboardButton(text=t(lang, "btn_back"), callback_data="stats:back")],
    ])


def get_back_to_stats_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "btn_back_to_stats"), callback_data="stats:back")],
    ])


def get_compare_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "btn_this_week"), callback_data="compare:first:this_week"),
         InlineKeyboardButton(text=t(lang, "btn_last_week"), callback_data="compare:first:last_week")],
        [InlineKeyboardButton(text=t(lang, "btn_this_month"), callback_data="compare:first:this_month"),
         InlineKeyboardButton(text=t(lang, "btn_last_month"), callback_data="compare:first:last_month")],
    ])


def get_second_compare_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "btn_this_week"), callback_data="compare:second:this_week"),
         InlineKeyboardButton(text=t(lang, "btn_last_week"), callback_data="compare:second:last_week")],
        [InlineKeyboardButton(text=t(lang, "btn_this_month"), callback_data="compare:second:this_month"),
         InlineKeyboardButton(text=t(lang, "btn_last_month"), callback_data="compare:second:last_month")],
    ])


def get_settings_keyboard(lang: str, stickers_enabled: bool = True) -> InlineKeyboardMarkup:
    stickers_btn = t(lang, "btn_stickers_on" if stickers_enabled else "btn_stickers_off")
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "btn_reminders"), callback_data="settings:reminders"),
         InlineKeyboardButton(text=t(lang, "btn_change_tone"), callback_data="settings:tone")],
        [InlineKeyboardButton(text=t(lang, "btn_change_language"), callback_data="settings:language"),
         InlineKeyboardButton(text=t(lang, "btn_set_timezone"), callback_data="settings:timezone")],
        [InlineKeyboardButton(text=stickers_btn, callback_data="settings:stickers")],
        [InlineKeyboardButton(text=t(lang, "btn_delete_data"), callback_data="settings:delete")],
        [InlineKeyboardButton(text=t(lang, "btn_back"), callback_data="settings:back")],
    ])


def get_settings_language_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("en", "language_english"), callback_data="settings:lang:en"),
         InlineKeyboardButton(text=t("en", "language_russian"), callback_data="settings:lang:ru")],
        [InlineKeyboardButton(text=t(lang, "btn_back"), callback_data="settings:show")],
    ])


def get_delete_confirm_keyboard(lang: str, step: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "btn_delete_yes"), callback_data=f"settings:delete:{step}"),
         InlineKeyboardButton(text=t(lang, "btn_delete_no"), callback_data="settings:show")],
    ])


def get_reminders_keyboard(lang: str, reminders: list) -> InlineKeyboardMarkup:
    rows = []
    active = {rem.type: rem for rem in reminders if rem.is_active}
    for reminder_type in ["morning", "evening", "weekly"]:
        reminder = active.get(reminder_type)
        label = t(lang, f"reminder_type_{reminder_type}")
        if reminder is not None:
            rows.append([
                InlineKeyboardButton(
                    text=t(lang, "reminder_active", reminder=label, time=reminder.time),
                    callback_data=f"reminder:remove:{reminder_type}",
                )
            ])
        else:
            rows.append([
                InlineKeyboardButton(
                    text=t(lang, "reminder_inactive", reminder=label),
                    callback_data=f"reminder:add:{reminder_type}",
                )
            ])
    rows.append([InlineKeyboardButton(text=t(lang, "btn_back"), callback_data="settings:show")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_goal_menu_keyboard(lang: str, has_goals: bool) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=t(lang, "btn_add_goal"), callback_data="goals:add"),
         InlineKeyboardButton(text=t(lang, "goals_suggest_btn"), callback_data="goals:suggest")],
    ]
    if has_goals:
        buttons.append([InlineKeyboardButton(text=t(lang, "btn_goal_details"), callback_data="goals:list")])
    buttons.append([InlineKeyboardButton(text=t(lang, "btn_back"), callback_data="goals:back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_goal_list_keyboard(lang: str, goals: list) -> InlineKeyboardMarkup:
    buttons = [[InlineKeyboardButton(text=f"🎯 {goal.title}", callback_data=f"goal:view:{goal.id}")] for goal in goals]
    buttons.append([InlineKeyboardButton(text=t(lang, "btn_back"), callback_data="goals:back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_goal_detail_buttons(lang: str, goal_id: int, has_wins: bool = False) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=t(lang, "btn_mark_done"), callback_data=f"goal:done:{goal_id}"),
         InlineKeyboardButton(text=t(lang, "btn_abandon"), callback_data=f"goal:abandon:{goal_id}")],
        [InlineKeyboardButton(text=t(lang, "btn_analyse_goal"), callback_data=f"goal:analyse:{goal_id}"),
         InlineKeyboardButton(text=t(lang, "btn_edit_goal"), callback_data=f"goal:edit:{goal_id}")],
    ]
    if has_wins:
        rows.append([InlineKeyboardButton(text=t(lang, "btn_manage_wins"), callback_data=f"goal:manage_wins:{goal_id}")])
    rows.append([InlineKeyboardButton(text=t(lang, "btn_back"), callback_data="goals:list")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_goal_edit_keyboard(lang: str, goal_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "btn_edit_goal_title"), callback_data=f"goal:edit:title:{goal_id}"),
         InlineKeyboardButton(text=t(lang, "btn_edit_goal_deadline"), callback_data=f"goal:edit:deadline:{goal_id}")],
        [InlineKeyboardButton(text=t(lang, "btn_edit_goal_category"), callback_data=f"goal:edit:category:{goal_id}")],
        [InlineKeyboardButton(text=t(lang, "btn_back"), callback_data=f"goal:view:{goal_id}")],
    ])


def get_abandon_confirm_buttons(lang: str, goal_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "btn_yes_abandon"), callback_data=f"goal:abandon:confirm:{goal_id}"),
         InlineKeyboardButton(text=t(lang, "btn_keep"), callback_data=f"goal:abandon:cancel:{goal_id}")],
    ])


def get_goal_suggestion_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "btn_suggest_accept"), callback_data="goal_suggest:accept"),
         InlineKeyboardButton(text=t(lang, "btn_suggest_custom"), callback_data="goal_suggest:custom")],
        [InlineKeyboardButton(text=t(lang, "btn_suggest_skip"), callback_data="goal_suggest:skip")],
    ])


def get_search_results_keyboard(lang: str, has_more: bool) -> InlineKeyboardMarkup:
    buttons = []
    if has_more:
        buttons.append([InlineKeyboardButton(text=t(lang, "btn_search_more"), callback_data="search:more")])
    buttons.append([InlineKeyboardButton(text=t(lang, "btn_back"), callback_data="search:back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_category_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Career", callback_data="goals:category:Career"),
         InlineKeyboardButton(text="Learning", callback_data="goals:category:Learning")],
        [InlineKeyboardButton(text="Health", callback_data="goals:category:Health")],
        [InlineKeyboardButton(text="Personal", callback_data="goals:category:Personal"),
         InlineKeyboardButton(text="Other", callback_data="goals:category:Other")],
        [InlineKeyboardButton(text=t(lang, "btn_cancel"), callback_data="goals:back")],
    ])
