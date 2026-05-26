from groq import AsyncGroq

from config import settings

client = AsyncGroq(api_key=settings.GROQ_API_KEY)
MODEL = "llama3-70b-8192"


def _choose_style(tone: str) -> str:
    if tone == "friend":
        return "friendly and supportive"
    if tone == "coach":
        return "motivating and direct"
    if tone == "mirror":
        return "neutral and reflective"
    return "helpful"


def _language_instruction(lang: str) -> str:
    return "Respond in Russian." if lang == "ru" else "Respond in English."


async def _create_completion(system_prompt: str, user_prompt: str, max_tokens: int = 250) -> str:
    response = await client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content.strip()


async def ask_praise(tone: str, win_text: str, count: int, lang: str) -> str:
    style = _choose_style(tone)
    system_prompt = (
        "You are a Telegram assistant that writes brief, encouraging follow-ups after a user logs a win. "
        + _language_instruction(lang)
    )
    user_prompt = (
        f"A user recorded win #{count}: \"{win_text}\". "
        f"Write a short {style} reply, celebrate the win, and encourage the user to keep going."
    )
    return await _create_completion(system_prompt, user_prompt, max_tokens=120)


async def ask_reflect(tone: str, win_text: str, days_ago: int, lang: str) -> str:
    style = _choose_style(tone)
    system_prompt = (
        "You are a supportive reflection coach for a Telegram bot. "
        + _language_instruction(lang)
    )
    user_prompt = (
        f"The user is revisiting a past win from {days_ago} days ago: \"{win_text}\". "
        f"Write a short {style} response that helps them appreciate progress and stay motivated."
    )
    return await _create_completion(system_prompt, user_prompt, max_tokens=140)


async def ask_weekly_narrative(tone: str, wins: list[str], lang: str) -> str:
    style = _choose_style(tone)
    system_prompt = (
        "You are a friendly summary writer for a weekly reflection message. "
        + _language_instruction(lang)
    )
    wins_text = "\n".join(f"- {text}" for text in wins)
    user_prompt = (
        f"A user recorded these wins this week:\n{wins_text}\n\n"
        f"Write a concise weekly digest in a {style} tone. Celebrate progress, mention the number of wins, and encourage the user for next week."
    )
    return await _create_completion(system_prompt, user_prompt, max_tokens=220)
