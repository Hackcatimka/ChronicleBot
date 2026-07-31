# Chronicle Bot

A Telegram bot for saving meaningful moments, tracking personal goals and reviewing progress with AI-assisted reflections.

I built Chronicle Bot as a complete Telegram product rather than a collection of separate commands: it includes onboarding, persistent data, scheduled reminders, analytics and an administration area.

## Features

- save moments and organize them by life-area tags;
- create goals and connect recorded moments to them;
- search, edit and delete previous entries;
- view weekly, monthly and all-time statistics;
- receive AI-assisted progress summaries and 30-day reflections;
- revisit older entries through a “Time Machine” flow;
- configure reminders, language and conversation tone;
- use the bot in English or Russian;
- review usage and retention information in a restricted admin area.

## Tech stack

- Python 3.12
- aiogram 3
- SQLAlchemy with asyncpg
- PostgreSQL
- Alembic
- APScheduler
- Groq API through an OpenAI-compatible client
- Sentry integration

## Project structure

```text
handlers/   Telegram commands and user flows
db/         database models and async session setup
alembic/    database migrations
tests/      automated tests
ai.py       AI provider integration
scheduler.py reminders and weekly digests
main.py     application entry point
```

## Run locally

```bash
git clone https://github.com/Hackcatimka/ChronicleBot.git
cd ChronicleBot
python -m venv .venv
pip install -r requirements.txt
cp .env.example .env
```

Configure the local environment:

```env
BOT_TOKEN=your_telegram_bot_token
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/chronicle
GROQ_API_KEY=your_groq_api_key
```

Start the bot:

```bash
python main.py
```

Database migrations run automatically during startup.

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

## Status

Active portfolio project. Planned improvements include broader integration testing, a clearer deployment guide and a short product demonstration.

## Privacy

The bot stores user-generated journal entries. A real deployment should use a protected database, restricted logs, documented retention rules and a clear privacy notice.

