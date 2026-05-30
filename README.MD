# Chronicle Bot 🏆

Telegram bot that saves your wins, tracks your goals, and reflects your progress back to you with AI.

---

## Features

- **Win recording** — just write what went well, AI reacts to the specific thing you did
- **Goals** — create goals, link wins to them, get AI progress analysis
- **Reflect** — AI analysis of your last 30 days: patterns, strengths, what's next
- **Time Machine** — revisit random past wins with AI reflection
- **Stats** — this week, this month, all time, period comparison
- **Reminders** — morning check-in, evening check-in, weekly digest with AI narrative
- **Tones** — Friend, Coach, or Mirror — changes how the AI talks to you
- **Languages** — English and Russian

---

## Stack

- Python 3.12
- [aiogram 3.x](https://docs.aiogram.dev/) — Telegram bot framework
- [SQLAlchemy 2.0](https://docs.sqlalchemy.org/) + asyncpg — async ORM
- PostgreSQL — database
- [Alembic](https://alembic.sqlalchemy.org/) — database migrations
- [APScheduler](https://apscheduler.readthedocs.io/) — reminders
- [Groq API](https://console.groq.com/) (llama-3.3-70b-versatile) — AI responses

---

## Project structure

```
chronicle/
├── main.py               # Entry point, middleware, error handler, health server
├── config.py             # Settings from environment variables
├── ai.py                 # Groq API calls
├── scheduler.py          # APScheduler — reminders and weekly digests
├── keyboards.py          # Inline keyboard builders
├── locales.py            # All user-facing strings (en + ru)
├── ratelimit.py          # In-memory rate limiter
├── utils.py              # edit_or_answer / edit_stored helpers (one-message UI)
├── db/
│   ├── models.py         # SQLAlchemy models
│   └── engine.py         # Async engine and session
├── handlers/
│   ├── start.py          # /start, onboarding (language → tone → timezone)
│   ├── wins.py           # Recording wins, linking to goals
│   ├── goals.py          # Goals — create, view, complete, abandon
│   ├── stats.py          # Stats and period comparison
│   ├── reflect.py        # 30-day AI reflection
│   ├── then.py           # Time machine
│   └── reminders.py      # Reminders and settings
├── alembic/              # Database migrations
└── requirements.txt
```

---

## Local setup

**1. Clone and install**

```bash
git clone https://github.com/Hackcatimka/ChronicleBot.git
cd ChronicleBot
pip install -r requirements.txt
```

**2. Create `.env`**

```env
BOT_TOKEN=your_telegram_bot_token
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/chronicle
GROQ_API_KEY=your_groq_api_key
SENTRY_DSN=           # optional
```

**3. Run migrations and start**

```bash
python main.py
```

Migrations run automatically on startup.

---

## Deploy on Railway

1. Push to GitHub
2. Railway → New Project → Deploy from GitHub
3. Add PostgreSQL plugin
4. Set environment variables: `BOT_TOKEN`, `GROQ_API_KEY`
5. Railway redeploys automatically on every push

---

## Database schema

| Table | Purpose |
|---|---|
| `users` | Telegram user, tone, language, UTC offset |
| `wins` | Recorded wins with AI-classified tag |
| `goals` | User goals with deadline, category, status |
| `win_goals` | Many-to-many: wins linked to goals |
| `reminders` | Scheduled reminders per user |

---

## Environment variables

| Variable | Description |
|---|---|
| `BOT_TOKEN` | Telegram bot token from BotFather |
| `DATABASE_URL` | PostgreSQL connection string |
| `GROQ_API_KEY` | Groq API key (free at console.groq.com) |
| `SENTRY_DSN` | Optional — Sentry error tracking |

---

## License

MIT
