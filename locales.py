TEXTS = {
    "en": {
        "choose_language": "Choose your language:",
        "language_english": "🇬🇧 English",
        "language_russian": "🇷🇺 Русский",
        "onboarding_welcome": (
            "👋 Hi! I'm <b>Chronicle</b> — your personal wins journal.\n\n"
            "Most days you do something worth remembering. Most of it gets forgotten. "
            "Chronicle fixes that — just write what went well, and I'll take care of the rest.\n\n"
            "✨ AI reaction after every moment\n"
            "🎯 Goals with progress analysis\n"
            "🔮 30-day reflection — what you're becoming\n"
            "⏪ Time machine — revisit your past moments\n"
            "📊 Stats and reminders\n\n"
            "One quick question — how should I talk to you?\n\n"
            "👋 <b>Friend</b>\n"
            "Warm and casual. Celebrates your wins, keeps things light.\n\n"
            "💪 <b>Coach</b>\n"
            "Direct and motivating. Pushes you to reflect — what made this possible? What's next?\n\n"
            "🪞 <b>Mirror</b>\n"
            "Neutral and factual. Just your progress, no hype.\n\n"
            "You can change this later in Settings."
        ),
        "choose_tone": (
            "How should I talk to you?\n\n"
            "👋 <b>Friend</b>\n"
            "Warm and casual. Celebrates your wins with you, cheers you on, "
            "keeps things light and encouraging.\n\n"
            "💪 <b>Coach</b>\n"
            "Direct and motivating. Pushes you to reflect — what made this possible? "
            "What's next? Focused on growth.\n\n"
            "🪞 <b>Mirror</b>\n"
            "Neutral and factual. Just reflects your progress back to you. "
            "No hype, no commentary — only what's there.\n\n"
            "You can change this later in Settings."
        ),
        "tone_selected": "Got it — I'll be your {tone}.\n\nNow just write me anything that went well today. Or tap a button below.",
        "welcome_back": "Welcome back, {name} 👋",

        "main_menu": "What happened today? Just write.",
        "btn_record_win": "🏆 Record a moment",
        "btn_goals": "🎯 My goals",
        "btn_reflect": "🔮 What changed",
        "btn_stats": "📊 Stats",
        "btn_time_machine": "⏪ Time machine",
        "btn_settings": "⚙️ Settings",

        "intent_goal_question": "Looks like a goal 🎯 — want to add it or save as a moment?",
        "btn_add_as_goal": "🎯 Add as goal",
        "btn_save_as_win": "🏆 Save as moment",
        "goal_saved_quick": "🎯 Goal added: \"{title}\"\n\nYou can set a deadline and category in Goals.",
        "goal_title_from_win": "What should this goal be called? Send a short title:",
        "win_received": "Got it:\n\n{text}\n\nSave this as a moment?",
        "btn_save": "✅ Save",
        "btn_link_goal": "🎯 Link to goal",
        "btn_edit": "✏️ Edit",
        "btn_cancel": "❌ Cancel",
        "win_edit_prompt": "Rewrite it:",
        "win_cancelled": "No worries. What do you want to do?",
        "win_record_prompt": "Tell me what went well. Big or small — everything counts. 🏆",
        "no_text_to_save": "No text to save.",
        "user_not_found": "Use /start first.",
        "rate_limited": "You're sending messages too fast. Please wait a moment.",
        "input_too_long": "Message is too long (max 2000 characters). Please shorten it.",
        "choose_goal_for_win": "Choose a goal for this moment:",
        "win_linked": "Win linked to a goal.",

        "tone_reply_friend": "Saved! 🎉 That's moment #{count}. Keep going!",
        "tone_reply_coach": "Moment #{count} logged. What made this possible?",
        "tone_reply_mirror": "Moment #{count} recorded.",
        "back_to_menu": "Back to menu:",

        "stats_title": "📊 Stats",
        "btn_this_week": "📅 This week",
        "btn_this_month": "📆 This month",
        "btn_all_time": "🗓 All time",
        "btn_compare": "⚖️ Compare",
        "btn_last_week": "Last week",
        "btn_last_month": "Last month",
        "btn_back": "← Back",
        "btn_back_to_stats": "← Back to stats",
        "no_wins_yet": "No moments recorded yet.",
        "wins_recorded": "Moments recorded: {n}",
        "active_days": "Active days: {n} out of {total}",
        "compare_first": "Choose first period:",
        "compare_second": "Choose second period:",
        "compare_result": "⚖️ {first} vs {second}\n\n{first}: {w1} moments, {d1} active days\n{second}: {w2} moments, {d2} active days\n\n{diff}",
        "period_this_week": "This week",
        "period_last_week": "Last week",
        "period_this_month": "This month",
        "period_last_month": "Last month",
        "report_title": "📊 {title}",
        "report_no_wins": "No moments recorded yet.",
        "report_your_wins": "Your moments:",
        "report_total_wins": "Total moments: {n}",
        "report_days_with_bot": "Days with the bot: {n}",
        "report_most_active_month": "Most active month: {month} ({count} moments)",
        "report_first_win": "First moment: {date}",
        "report_latest_win": "Latest moment: {date}",
        "compare_diff_positive": "+{diff} moments compared to {other} 📈",
        "compare_diff_negative": "{diff} moments compared to {other} 📉",
        "compare_diff_same": "Same wins as {other}.",
        "choose_first_period_prompt": "Choose first period for comparison:",
        "choose_second_period_prompt": "Now choose second period:",

        "no_memories": "⏪ Time machine\n\nNo memories yet. Keep recording your moments —\nin a week I'll have something to show you.",
        "memory": "⏪ Time machine\n\nOn {date} you wrote:\n\n\"{text}\"\n\nThat was {days} days ago.",
        "only_memory": "That's the only memory I have so far. Keep going! 🏆",
        "time_machine_nav": "📅 {date}",
        "btn_show_another": "🎲 Show another",

        "no_goals": "🎯 My goals\n\nNo goals yet. Let's set one!",
        "btn_add_goal": "➕ Add goal",
        "btn_goal_details": "📋 Goal details",
        "goal_title_prompt": "Write the goal title",
        "goal_deadline_prompt": "Add a deadline? Write DD.MM.YYYY or \"no\"",
        "goal_deadline_invalid": "Invalid format. Use DD.MM.YYYY or write \"no\"",
        "goal_category_prompt": "What category? Write or choose:",
        "goal_category_invalid": "Write a category or choose one from buttons.",
        "goal_done": "🏆 Goal completed!\n\n\"{title}\" is done.\nThat took {days} days.",
        "goal_abandon_confirm": "Are you sure you want to abandon this goal?",
        "btn_mark_done": "✅ Mark as done",
        "btn_abandon": "🗑 Abandon",
        "btn_yes_abandon": "✅ Yes, abandon",
        "btn_keep": "❌ Keep it",
        "no_wins_linked": "No moments linked yet.",
        "wins_linked": "Moments linked to this goal:",
        "goal_list_title": "🎯 My goals",
        "goal_list_empty": "No goals yet. Let's set one!",
        "goal_view_status": "Status: {status}",
        "goal_view_category": "Category: {category}",
        "goal_view_deadline": "Deadline: {deadline}",
        "goal_no_deadline": "No deadline",
        "goal_view_label": "🎯 {title}",
        "goal_view_header": "🎯 {title}",
        "goal_view_wins": "Moments linked to this goal:",
        "goal_view_no_wins": "No moments linked yet.",
        "goal_no_category": "None",

        "settings_title": "Settings",
        "btn_reminders": "🔔 Reminders",
        "btn_change_tone": "🎭 Change tone",
        "reminders_title": "Reminders",
        "reminder_saved": "Reminder saved.",
        "reminder_removed": "Reminder off.",
        "reminder_time_prompt": "What time? Write HH:MM (e.g. 09:00)",
        "reminder_weekly_prompt": "What day and time? e.g. Mon 10:00",
        "reminder_invalid": "Invalid format. Use HH:MM (e.g. 09:00)",
        "reminder_weekly_invalid": "Invalid format. Use e.g. Mon 10:00",
        "morning_checkin": "🌅 Morning check-in\n\nWhat's one thing you want to achieve today?",
        "evening_checkin": "🌙 Evening check-in\n\nWhat went well today? Write me a moment.",
        "reminder_type_morning": "Morning",
        "reminder_type_evening": "Evening",
        "reminder_type_weekly": "Weekly digest",
        "reminder_active": "✅ {reminder} — {time}  ❌",
        "reminder_inactive": "➕ {reminder}",
        "reminder_not_found": "Reminder not found.",
        "weekly_digest_title": "📊 Weekly digest",
        "weekly_digest_summary": "This week you recorded {count} moments.",
        "weekly_digest_no_wins": "No moments yet.",
        "weekly_digest_encouragement": "Keep it up!",
        "inactivity_nudge": "Hey, it's been a quiet day — anything worth remembering? Even something small counts ✨",

        "tone_friend": "Friend 👋",
        "tone_coach": "Coach 💪",
        "tone_mirror": "Mirror 🪞",
        "tone_friend_desc": "Warm, casual",
        "tone_coach_desc": "Direct, questions",
        "tone_mirror_desc": "Facts only",

        "period_caption": "{label}",
        "goal_no_goals": "🎯 My goals\n\nNo goals yet. Let's set one!",
        "goal_choose": "Choose a goal:",
        "goal_abandoned": "Goal abandoned.",
        "goal_abandon_cancelled": "Abandon cancelled.",
        "goal_not_found": "Goal not found.",

        "btn_analyse_goal": "🤖 Analyse progress",
        "goal_analysing": "Analysing your progress...",
        "goal_analysis_error": "Couldn't generate analysis right now. Try again later.",

        "reflect_analysing": "Looking at your last 30 days...",
        "reflect_no_wins": "No moments in the last 30 days yet. Write a few first — then come back here.",
        "reflect_error": "Couldn't generate reflection right now. Try again later.",

        "onboarding_timezone_prompt": (
            "Last step — what's your UTC offset?\n\n"
            "This is needed for reminders to arrive at the right time.\n\n"
            "Examples: <b>+3</b> Moscow · <b>+1</b> Berlin · <b>0</b> London · <b>-5</b> New York\n\n"
            "Just type a number like <b>+3</b> or <b>-5</b>:"
        ),
        "onboarding_timezone_saved": "Got it — UTC{offset}. You're all set!\n\nNow just write me what went well today. Or tap a button below.",
        "btn_set_timezone": "🕐 Timezone",
        "timezone_prompt": "Enter your UTC offset — e.g. +3 for Moscow, +1 for Berlin, 0 for London, -5 for New York.\n\nCurrent: UTC{offset}",
        "timezone_invalid": "Invalid format. Use +3, -5, 0, etc.",
        "timezone_saved": "Timezone saved: UTC{offset}. All reminders updated.",
        "btn_change_language": "🌐 Language",
        "btn_delete_data": "🗑 Delete all data",
        "btn_stickers_on": "🐱 Catification ✅",
        "btn_stickers_off": "🐱 Catification ❌",
        "stickers_toggled_on": "🐱 Catification on!",
        "stickers_toggled_off": "Catification off.",
        "settings_language_title": "Choose your language:",
        "language_changed": "Language updated.",
        "btn_delete_yes": "Yes, delete",
        "btn_delete_no": "Cancel",
        "delete_confirm_1": "⚠️ Are you sure? All your wins and goals will be permanently deleted. Step 1 of 3.",
        "delete_confirm_2": "⚠️ Really sure? This cannot be undone. Step 2 of 3.",
        "delete_confirm_3": "🚨 Last chance. ALL your wins, goals and linked data will be gone forever. Step 3 of 3.",
        "delete_done": "Done. All your wins and goals have been deleted.",

        "tag_work": "💼 Work",
        "tag_health": "💪 Health",
        "tag_learning": "📚 Learning",
        "tag_personal": "🌟 Personal",
        "tag_creative": "🎨 Creative",
        "tag_social": "🤝 Social",
        "tag_finance": "💰 Finance",
        "tag_other": "✨ Other",

        "stats_by_tag": "By category:",

        "btn_search": "🔍 Search",
        "search_prompt": "Enter a word or phrase to search your moments:",
        "search_no_results": "No moments found for \"{query}\".",
        "search_results": "🔍 \"{query}\" — {count} found:",
        "search_showing": "Showing {start}–{end} of {total}",
        "btn_search_more": "Load more",
        "btn_search_all": "📋 All moments",
        "btn_search_again": "🔍 New search",
        "search_all_title": "📋 All moments — {total} total",
        "search_all_empty": "No moments recorded yet.",

        "deadline_reminder": "⏰ Goal \"{title}\" is due in 3 days — {deadline}.\n\nHow's it going?",

        "milestone": "🎉 Moment #{count} — a milestone!\n\n",

        "btn_edit_win": "✏️ Edit",
        "btn_delete_win": "🗑 Delete",
        "win_delete_confirm": "Delete this moment? This can't be undone.",
        "btn_delete_confirm": "✅ Yes, delete",
        "win_deleted": "Moment deleted.",
        "win_edit_new_text": "Send the new text for this moment:",
        "win_edited": "Moment updated.",

        "btn_manage_wins": "✂️ Manage moments",
        "choose_win_to_unlink": "Choose a moment to unlink from this goal:",
        "win_unlinked": "Moment unlinked.",
        "btn_edit_goal": "✏️ Edit",
        "goal_edit_menu": "What do you want to change?",
        "btn_edit_goal_title": "✏️ Title",
        "btn_edit_goal_deadline": "📅 Deadline",
        "btn_edit_goal_category": "🏷 Category",
        "goal_edit_title_prompt": "Write a new goal title:",
        "goal_edit_deadline_prompt": "Write a new deadline (DD.MM.YYYY) or \"no\" to remove:",
        "goal_edit_category_prompt": "Write a new category or choose one:",
        "goal_title_updated": "Goal title updated.",
        "goal_deadline_updated": "Deadline updated.",
        "goal_deadline_removed": "Deadline removed.",
        "goal_category_updated": "Category updated.",

        "goal_progress_line": "{count} moments · {days} days",

        "stats_streak": "🔥 Streak: {n} days",
        "btn_skills_map": "🗺 Skill Map",
        "stats_skills_title": "🗺 Skill Map · {total} moments",
        "stats_skills_empty": "No moments recorded yet.",
        "btn_ai_review": "🤖 AI review",
        "stats_ai_loading": "Generating review...",
        "stats_ai_empty": "No moments recorded for this period.",

        "goals_suggest_btn": "💡 Suggest a goal",
        "goals_suggest_no_data": "Not enough moments yet to suggest a goal. Keep writing!",

        "win_saved_no_goals": "Moment saved. You have no goals yet.",
        "btn_create_first_goal": "🎯 Create a goal",

        "goal_suggestion": (
            "I notice a pattern — you often write about {tag}.\n\n"
            "Here's a goal that might fit:\n\n"
            "🎯 <b>{title}</b>\n\n"
            "Want to set it?"
        ),
        "btn_suggest_accept": "✅ Set this goal",
        "btn_suggest_custom": "✏️ Different name",
        "btn_suggest_skip": "❌ Not now",
        "goal_suggest_custom_prompt": "Write a goal title:",
        "goal_suggest_saved": "🎯 Goal set: \"{title}\"\n\nYou can add a deadline and category in Goals.",
        "goal_suggest_skipped": "Got it — no goal for now.",

        "btn_feedback": "💬 Feedback",
        "feedback_prompt": "Got something to say? Send your feedback — bug reports, ideas, or anything else. I read everything.",
        "feedback_sent": "Thanks! Your feedback has been sent.",
        "feedback_reply": "💬 Reply from the Chronicle team:\n\n{text}",
    },
    "ru": {
        "choose_language": "Выбери язык:",
        "language_english": "🇬🇧 English",
        "language_russian": "🇷🇺 Русский",
        "onboarding_welcome": (
            "👋 Привет! Я <b>Chronicle</b> — личный дневник твоих побед.\n\n"
            "Большинство дней ты делаешь что-то стоящее. Большинство из этого забывается. "
            "Chronicle это исправляет — просто пиши что пошло хорошо, а остальное я возьму на себя.\n\n"
            "✨ Реакция ИИ после каждого момента\n"
            "🎯 Цели с анализом прогресса\n"
            "🔮 30-дневная рефлексия — что ты становишься\n"
            "⏪ Машина времени — пересмотри прошлые моменты\n"
            "📊 Статистика и напоминания\n\n"
            "Один вопрос — как мне с тобой общаться?\n\n"
            "👋 <b>Друг</b>\n"
            "Тепло и неформально. Праздную победы вместе с тобой, держу тон лёгким.\n\n"
            "💪 <b>Коуч</b>\n"
            "Конкретно и мотивирующе. Задаю вопросы — что помогло? что дальше?\n\n"
            "🪞 <b>Зеркало</b>\n"
            "Нейтрально и по фактам. Только прогресс, без лишних слов.\n\n"
            "Это можно изменить в Настройках."
        ),
        "choose_tone": (
            "Как мне с тобой общаться?\n\n"
            "👋 <b>Друг</b>\n"
            "Тепло и неформально. Праздную победы вместе с тобой, подбадриваю, "
            "держу тон лёгким и поддерживающим.\n\n"
            "💪 <b>Коуч</b>\n"
            "Конкретно и мотивирующе. Задаю вопросы — что помогло? что дальше? "
            "Фокус на росте и движении вперёд.\n\n"
            "🪞 <b>Зеркало</b>\n"
            "Нейтрально и по фактам. Просто отражаю твой прогресс. "
            "Без лишних слов — только то, что есть.\n\n"
            "Это можно изменить в Настройках."
        ),
        "tone_selected": "Отлично, буду твоим {tone}.\n\nПросто напиши что пошло хорошо сегодня. Или нажми кнопку.",
        "welcome_back": "С возвращением, {name} 👋",

        "main_menu": "Что произошло сегодня? Просто напиши.",
        "btn_record_win": "🏆 Записать момент",
        "btn_goals": "🎯 Мои цели",
        "btn_reflect": "🔮 Что изменилось",
        "btn_stats": "📊 Статистика",
        "btn_time_machine": "⏪ Машина времени",
        "btn_settings": "⚙️ Настройки",

        "intent_goal_question": "Похоже на цель 🎯 — добавить как цель или сохранить как момент?",
        "btn_add_as_goal": "🎯 Добавить как цель",
        "btn_save_as_win": "🏆 Сохранить как момент",
        "goal_saved_quick": "🎯 Цель добавлена: \"{title}\"\n\nДедлайн и категорию можно задать в разделе Цели.",
        "goal_title_from_win": "Как назовём эту цель? Отправь короткий заголовок:",
        "win_received": "Вот что я получил:\n\n{text}\n\nСохранить как момент?",
        "btn_save": "✅ Сохранить",
        "btn_link_goal": "🎯 Привязать к цели",
        "btn_edit": "✏️ Изменить",
        "btn_cancel": "❌ Отмена",
        "win_edit_prompt": "Напиши заново:",
        "win_cancelled": "Окей, отменено. Что дальше?",
        "win_record_prompt": "Расскажи что пошло хорошо. Большое или маленькое — всё считается. 🏆",
        "no_text_to_save": "Нет текста для сохранения.",
        "user_not_found": "Начни с /start.",
        "rate_limited": "Слишком много сообщений подряд. Подожди немного.",
        "input_too_long": "Сообщение слишком длинное (макс. 2000 символов). Пожалуйста, сократи его.",
        "choose_goal_for_win": "Выбери цель для этого момента:",
        "win_linked": "Момент привязан к цели.",

        "tone_reply_friend": "Сохранено! 🎉 Это момент #{count}. Продолжай!",
        "tone_reply_coach": "Момент #{count} записан. Что помогло это сделать?",
        "tone_reply_mirror": "Момент #{count} записан.",
        "back_to_menu": "Главное меню:",

        "stats_title": "📊 Статистика",
        "btn_this_week": "📅 Эта неделя",
        "btn_this_month": "📆 Этот месяц",
        "btn_all_time": "🗓 За всё время",
        "btn_compare": "⚖️ Сравнить",
        "btn_last_week": "Прошлая неделя",
        "btn_last_month": "Прошлый месяц",
        "btn_back": "← Назад",
        "btn_back_to_stats": "← К статистике",
        "no_wins_yet": "Моментов пока нет.",
        "wins_recorded": "Моментов записано: {n}",
        "active_days": "Активных дней: {n} из {total}",
        "compare_first": "Выбери первый период:",
        "compare_second": "Выбери второй период:",
        "compare_result": "⚖️ {first} vs {second}\n\n{first}: {w1} моментов, {d1} активных дней\n{second}: {w2} моментов, {d2} активных дней\n\n{diff}",
        "period_this_week": "Эта неделя",
        "period_last_week": "Прошлая неделя",
        "period_this_month": "Этот месяц",
        "period_last_month": "Прошлый месяц",
        "report_title": "📊 {title}",
        "report_no_wins": "Моментов пока нет.",
        "report_your_wins": "Твои моменты:",
        "report_total_wins": "Всего моментов: {n}",
        "report_days_with_bot": "Дней с ботом: {n}",
        "report_most_active_month": "Самый активный месяц: {month} ({count} моментов)",
        "report_first_win": "Первый момент: {date}",
        "report_latest_win": "Последний момент: {date}",
        "compare_diff_positive": "+{diff} моментов по сравнению с {other} 📈",
        "compare_diff_negative": "{diff} моментов по сравнению с {other} 📉",
        "compare_diff_same": "Тот же результат, что и {other}.",
        "choose_first_period_prompt": "Выбери первый период для сравнения:",
        "choose_second_period_prompt": "Теперь выбери второй период:",

        "no_memories": "⏪ Машина времени\n\nВоспоминаний пока нет. Записывай моменты —\nчерез неделю будет что показать.",
        "memory": "⏪ Машина времени\n\n{date} ты написал:\n\n\"{text}\"\n\nЭто было {days} дней назад.",
        "only_memory": "Это пока единственное воспоминание. Продолжай! 🏆",
        "time_machine_nav": "📅 {date}",
        "btn_show_another": "🎲 Другое воспоминание",

        "no_goals": "🎯 Мои цели\n\nЦелей пока нет. Давай добавим!",
        "btn_add_goal": "➕ Добавить цель",
        "btn_goal_details": "📋 Детали целей",
        "goal_title_prompt": "Напиши название цели",
        "goal_deadline_prompt": "Добавить дедлайн? Напиши дату DD.MM.YYYY или \"нет\"",
        "goal_deadline_invalid": "Неверный формат. Используй DD.MM.YYYY или напиши \"нет\"",
        "goal_category_prompt": "К какой категории относится? Напиши или выбери:",
        "goal_category_invalid": "Напиши категорию или выбери одну из кнопок.",
        "goal_done": "🏆 Цель достигнута!\n\n\"{title}\" выполнена.\nЭто заняло {days} дней.",
        "goal_abandon_confirm": "Точно хочешь отказаться от этой цели?",
        "btn_mark_done": "✅ Выполнено",
        "btn_abandon": "🗑 Отказаться",
        "btn_yes_abandon": "✅ Да, отказаться",
        "btn_keep": "❌ Оставить",
        "no_wins_linked": "Моментов пока не привязано.",
        "wins_linked": "Моменты привязанные к цели:",
        "goal_list_title": "🎯 Мои цели",
        "goal_list_empty": "Целей пока нет. Давай добавим!",
        "goal_view_status": "Статус: {status}",
        "goal_view_category": "Категория: {category}",
        "goal_view_deadline": "Дедлайн: {deadline}",
        "goal_no_deadline": "Без дедлайна",
        "goal_view_label": "🎯 {title}",
        "goal_view_header": "🎯 {title}",
        "goal_view_wins": "Моменты привязанные к цели:",
        "goal_view_no_wins": "Моментов пока не привязано.",
        "goal_no_category": "Нет",

        "settings_title": "Настройки",
        "btn_reminders": "🔔 Напоминания",
        "btn_change_tone": "🎭 Изменить тон",
        "reminders_title": "Напоминания",
        "reminder_saved": "Напоминание сохранено.",
        "reminder_removed": "Напоминание отключено.",
        "reminder_time_prompt": "В какое время? Напиши HH:MM (например 09:00)",
        "reminder_weekly_prompt": "В какой день и время? Например: Mon 10:00",
        "reminder_invalid": "Неверный формат. Используй HH:MM (например 09:00)",
        "reminder_weekly_invalid": "Неверный формат. Например: Mon 10:00",
        "morning_checkin": "🌅 Утренний чекин\n\nЧто хочешь сделать сегодня?",
        "evening_checkin": "🌙 Вечерний чекин\n\nЧто пошло хорошо сегодня? Напиши момент.",
        "reminder_type_morning": "Утреннее",
        "reminder_type_evening": "Вечернее",
        "reminder_type_weekly": "Недельный дайджест",
        "reminder_active": "✅ {reminder} — {time}  ❌",
        "reminder_inactive": "➕ {reminder}",
        "reminder_not_found": "Напоминание не найдено.",
        "weekly_digest_title": "📊 Недельный дайджест",
        "weekly_digest_summary": "На этой неделе ты записал {count} моментов.",
        "weekly_digest_no_wins": "Моментов пока нет.",
        "weekly_digest_encouragement": "Так держать!",
        "inactivity_nudge": "Тихий день — может, всё же было что-то стоящее? Даже мелочь считается ✨",

        "tone_friend": "Друг 👋",
        "tone_coach": "Коуч 💪",
        "tone_mirror": "Зеркало 🪞",
        "tone_friend_desc": "Тепло, неформально",
        "tone_coach_desc": "Конкретно, с вопросами",
        "tone_mirror_desc": "Только факты",

        "period_caption": "{label}",
        "goal_choose": "Выберите цель:",
        "goal_abandoned": "Цель отменена.",
        "goal_abandon_cancelled": "Отказ от отмены.",
        "goal_not_found": "Цель не найдена.",

        "btn_analyse_goal": "🤖 Анализ прогресса",
        "goal_analysing": "Анализирую прогресс...",
        "goal_analysis_error": "Не удалось сгенерировать анализ. Попробуй позже.",

        "reflect_analysing": "Смотрю на твои последние 30 дней...",
        "reflect_no_wins": "За последние 30 дней моментов ещё нет. Запиши несколько — потом возвращайся.",
        "reflect_error": "Не удалось сгенерировать рефлексию. Попробуй позже.",

        "onboarding_timezone_prompt": (
            "Последний шаг — какое у тебя смещение от UTC?\n\n"
            "Это нужно чтобы напоминания приходили в нужное время.\n\n"
            "Примеры: <b>+3</b> Москва · <b>+2</b> Киев · <b>+1</b> Берлин · <b>0</b> Лондон\n\n"
            "Просто напиши число, например <b>+3</b> или <b>-5</b>:"
        ),
        "onboarding_timezone_saved": "Отлично — UTC{offset}. Всё готово!\n\nТеперь просто напиши что пошло хорошо сегодня. Или нажми кнопку ниже.",
        "btn_set_timezone": "🕐 Часовой пояс",
        "timezone_prompt": "Введи смещение от UTC — например +3 для Москвы, +1 для Берлина, 0 для Лондона, -5 для Нью-Йорка.\n\nСейчас: UTC{offset}",
        "timezone_invalid": "Неверный формат. Используй +3, -5, 0 и т.д.",
        "timezone_saved": "Часовой пояс сохранён: UTC{offset}. Все напоминания обновлены.",
        "btn_change_language": "🌐 Язык",
        "btn_delete_data": "🗑 Удалить все данные",
        "btn_stickers_on": "🐱 Котофикация ✅",
        "btn_stickers_off": "🐱 Котофикация ❌",
        "stickers_toggled_on": "🐱 Котофикация включена!",
        "stickers_toggled_off": "Котофикация выключена.",
        "settings_language_title": "Выбери язык:",
        "language_changed": "Язык обновлён.",
        "btn_delete_yes": "Да, удалить",
        "btn_delete_no": "Отмена",
        "delete_confirm_1": "⚠️ Точно? Все твои победы и цели будут удалены навсегда. Шаг 1 из 3.",
        "delete_confirm_2": "⚠️ Уверен? Это нельзя отменить. Шаг 2 из 3.",
        "delete_confirm_3": "🚨 Последний шанс. ВСЕ победы, цели и связанные данные исчезнут навсегда. Шаг 3 из 3.",
        "delete_done": "Готово. Все победы и цели удалены.",

        "tag_work": "💼 Работа",
        "tag_health": "💪 Здоровье",
        "tag_learning": "📚 Учёба",
        "tag_personal": "🌟 Личное",
        "tag_creative": "🎨 Творчество",
        "tag_social": "🤝 Общение",
        "tag_finance": "💰 Финансы",
        "tag_other": "✨ Другое",

        "stats_by_tag": "По категориям:",

        "btn_search": "🔍 Поиск",
        "search_prompt": "Введи слово или фразу для поиска по моментам:",
        "search_no_results": "По запросу \"{query}\" ничего не найдено.",
        "search_results": "🔍 \"{query}\" — найдено {count}:",
        "search_showing": "Показано {start}–{end} из {total}",
        "btn_search_more": "Показать ещё",
        "btn_search_all": "📋 Все моменты",
        "btn_search_again": "🔍 Новый поиск",
        "search_all_title": "📋 Все моменты — {total} всего",
        "search_all_empty": "Моментов пока нет.",

        "deadline_reminder": "⏰ Цель \"{title}\" — через 3 дня дедлайн ({deadline}).\n\nКак дела с ней?",

        "milestone": "🎉 Момент #{count} — это веха!\n\n",

        "btn_edit_win": "✏️ Изменить",
        "btn_delete_win": "🗑 Удалить",
        "win_delete_confirm": "Удалить этот момент? Это нельзя отменить.",
        "btn_delete_confirm": "✅ Да, удалить",
        "win_deleted": "Момент удалён.",
        "win_edit_new_text": "Отправь новый текст для этого момента:",
        "win_edited": "Момент обновлён.",

        "btn_manage_wins": "✂️ Управление моментами",
        "choose_win_to_unlink": "Выбери момент чтобы отвязать от цели:",
        "win_unlinked": "Момент отвязан.",
        "btn_edit_goal": "✏️ Изменить",
        "goal_edit_menu": "Что хочешь изменить?",
        "btn_edit_goal_title": "✏️ Название",
        "btn_edit_goal_deadline": "📅 Дедлайн",
        "btn_edit_goal_category": "🏷 Категория",
        "goal_edit_title_prompt": "Напиши новое название цели:",
        "goal_edit_deadline_prompt": "Напиши новый дедлайн (DD.MM.YYYY) или «нет» чтобы убрать:",
        "goal_edit_category_prompt": "Напиши новую категорию или выбери из кнопок:",
        "goal_title_updated": "Название цели обновлено.",
        "goal_deadline_updated": "Дедлайн обновлён.",
        "goal_deadline_removed": "Дедлайн убран.",
        "goal_category_updated": "Категория обновлена.",

        "goal_progress_line": "{count} моментов · {days} дней",

        "stats_streak": "🔥 Серия: {n} дней",
        "btn_skills_map": "🗺 Карта навыков",
        "stats_skills_title": "🗺 Карта навыков · {total} моментов",
        "stats_skills_empty": "Моментов пока нет.",
        "btn_ai_review": "🤖 AI-обзор",
        "stats_ai_loading": "Генерирую обзор...",
        "stats_ai_empty": "За этот период моментов нет.",

        "goals_suggest_btn": "💡 Предложить цель",
        "goals_suggest_no_data": "Запиши хотя бы 5 моментов чтобы получить предложение цели.",

        "win_saved_no_goals": "Момент сохранён. Активных целей пока нет.",
        "btn_create_first_goal": "🎯 Создать цель",

        "goal_suggestion": (
            "Я замечаю паттерн — ты часто пишешь про {tag}.\n\n"
            "Вот цель, которая может подойти:\n\n"
            "🎯 <b>{title}</b>\n\n"
            "Поставить её?"
        ),
        "btn_suggest_accept": "✅ Поставить цель",
        "btn_suggest_custom": "✏️ Другое название",
        "btn_suggest_skip": "❌ Не сейчас",
        "goal_suggest_custom_prompt": "Напиши название цели:",
        "goal_suggest_saved": "🎯 Цель поставлена: \"{title}\"\n\nДедлайн и категорию можно добавить в Целях.",
        "goal_suggest_skipped": "Хорошо — пока без цели.",

        "btn_feedback": "💬 Фидбек",
        "feedback_prompt": "Есть что сказать? Напиши — баг, идея, пожелание. Читаю всё.",
        "feedback_sent": "Спасибо! Фидбек отправлен.",
        "feedback_reply": "💬 Ответ от команды Chronicle:\n\n{text}",
    },
}


def t(lang: str, key: str, **kwargs) -> str:
    text = TEXTS.get(lang, TEXTS["en"]).get(key, TEXTS["en"].get(key, key))
    return text.format(**kwargs) if kwargs else text
