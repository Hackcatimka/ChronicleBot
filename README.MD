# Leap Bot 🏆

Telegram bot that remembers your wins and shows you how far you've come.

---

## What it does

- Saves your wins as you write them — no forms, just text
- Shows progress over time: this week vs last month, day 1 vs today
- Pulls up random memories from the past so you see your own growth
- Responds in your tone — friend, coach, or mirror
- Sends morning/evening check-ins and weekly digests
- Links wins to goals and tracks them

---

## Stack

- Python 3.11+
- [aiogram 3.7](https://docs.aiogram.dev/) — Telegram bot framework
- [SQLAlchemy 2.0](https://docs.sqlalchemy.org/) + asyncpg — async ORM
- PostgreSQL — database
- [APScheduler](https://apscheduler.readthedocs.io/) — reminders
- [Groq API](https://console.groq.com/) (llama3-70b) — AI responses

---

## Project structure

```
leap_bot/
├── main.py               # Entry point, middleware, router registration
├── config.py             # Settings from .env
├── ai.py                 # Groq API calls (praise, reflect, weekly digest)
├── scheduler.py          # APScheduler — reminders and digests
├── keyboards.py          # Shared inline keyboards
├── db/
│   ├── models.py         # SQLAlchemy models
│   └── engine.py         # Async engine and session
├── handlers/
│   ├── start.py          # /start, onboarding, tone selection
│   ├── wins.py           # Recording wins, linking to goals
│   ├── stats.py          # Stats, period comparison
│   ├── then.py           # Time machine — random past wins
│   ├── goals.py          # Goals — create, view, complete, abandon
│   └── reminders.py      # Reminders and settings
├── requirements.txt
├── Procfile              # For Railway deployment
└── .env.example
```

---

## Local setup

**1. Clone and install dependencies**

```bash
git clone https://github.com/your/leap-bot.git
cd leap-bot
pip install -r requirements.txt
```

**2. Create `.env` from example**

```bash
cp .env.example .env
```

Fill in the values:

```env
BOT_TOKEN=your_telegram_bot_token
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/leap_bot
GROQ_API_KEY=your_groq_api_key
```

- `BOT_TOKEN` — get from [@BotFather](https://t.me/BotFather)
- `DATABASE_URL` — local or remote PostgreSQL
- `GROQ_API_KEY` — get from [console.groq.com](https://console.groq.com/) (free)

**3. Create the database**

```bash
createdb leap_bot
```

Tables are created automatically on first run via `init_db()`.

**4. Run**

```bash
python main.py
```

---

## Deploy on Railway (free)

1. Push code to GitHub
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Add PostgreSQL plugin — Railway sets `DATABASE_URL` automatically
4. Add environment variables: `BOT_TOKEN`, `GROQ_API_KEY`
5. Make sure `Procfile` exists in the root:

```
worker: python main.py
```

Railway redeploys automatically on every push.

---

## Database schema

| Table | Purpose |
|---|---|
| `users` | Telegram user, tone preference |
| `wins` | Recorded wins with raw and processed text |
| `goals` | User goals with deadline and status |
| `win_goals` | Many-to-many: wins linked to goals |
| `skill_progress` | Aggregated skill growth per user |
| `reminders` | Scheduled reminders per user |
| `digests` | Stored weekly narratives |
| `feedback` | User ratings on bot responses |

---

## Bot tones

| Tone | Style |
|---|---|
| Friend | Warm, casual, short — celebrates every win |
| Coach | Direct, specific — ends with one question |
| Mirror | Facts only, no emotion — just what happened |

Tone is selected during onboarding and can be changed in Settings.

---

## Environment variables

| Variable | Description |
|---|---|
| `BOT_TOKEN` | Telegram bot token from BotFather |
| `DATABASE_URL` | PostgreSQL connection string (asyncpg) |
| `GROQ_API_KEY` | Groq API key for AI responses |

---

## License

MIT