import { env } from "cloudflare:workers";

export const dynamic = "force-dynamic";

type ChronicleAction =
  | "createMoment" | "updateMoment" | "deleteMoment" | "toggleFavorite"
  | "createGoal" | "updateGoal" | "deleteGoal"
  | "updateSettings" | "completeOnboarding" | "deleteAll" | "deleteAccount" | "seedDemo";

type Payload = {
  action?: ChronicleAction;
  id?: number;
  title?: string;
  content?: string;
  category?: string;
  mood?: string;
  favorite?: boolean;
  goalIds?: number[];
  description?: string;
  targetSteps?: number;
  completedSteps?: number;
  deadline?: string | null;
  status?: string;
  displayName?: string;
  language?: string;
  tone?: string;
  timezone?: string;
  remindersEnabled?: boolean;
  reminderTime?: string;
  reminderFrequency?: string;
  selectedAreas?: string[];
  goalTitle?: string;
  goalCategory?: string;
  goalSteps?: number;
  momentTitle?: string;
  momentContent?: string;
  momentCategory?: string;
  momentMood?: string;
};

function getDatabase() {
  if (!env.DB) throw new Error("Chronicle database is unavailable.");
  return env.DB;
}

async function ensureGoalColumns(db: D1Database) {
  const columns = await db.prepare("PRAGMA table_info(goals)").all<{ name: string }>();
  const names = new Set(columns.results.map((column) => column.name));
  const additions = [
    ["category", "ALTER TABLE goals ADD COLUMN category TEXT NOT NULL DEFAULT 'Growth'"],
    ["deadline", "ALTER TABLE goals ADD COLUMN deadline TEXT"],
    ["status", "ALTER TABLE goals ADD COLUMN status TEXT NOT NULL DEFAULT 'active'"],
    ["completed_at", "ALTER TABLE goals ADD COLUMN completed_at TEXT"],
  ] as const;
  for (const [name, statement] of additions) {
    if (!names.has(name)) await db.prepare(statement).run();
  }
}

async function ensureSettingsColumns(db: D1Database) {
  const columns = await db.prepare("PRAGMA table_info(chronicle_settings)").all<{ name: string }>();
  const names = new Set(columns.results.map((column) => column.name));
  if (!names.has("onboarding_complete")) await db.prepare("ALTER TABLE chronicle_settings ADD COLUMN onboarding_complete INTEGER NOT NULL DEFAULT 0").run();
  if (!names.has("selected_areas")) await db.prepare(`ALTER TABLE chronicle_settings ADD COLUMN selected_areas TEXT NOT NULL DEFAULT '["Growth","Work","Relationships","Health","Creativity","Rest"]'`).run();
}

async function ensureSchema() {
  const db = getDatabase();
  await db.batch([
    db.prepare(`CREATE TABLE IF NOT EXISTS moments (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      title TEXT NOT NULL,
      content TEXT NOT NULL,
      category TEXT NOT NULL DEFAULT 'Growth',
      mood TEXT NOT NULL DEFAULT 'Proud',
      is_favorite INTEGER NOT NULL DEFAULT 0,
      created_at TEXT NOT NULL
    )`),
    db.prepare(`CREATE TABLE IF NOT EXISTS goals (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      title TEXT NOT NULL,
      description TEXT NOT NULL DEFAULT '',
      target_steps INTEGER NOT NULL DEFAULT 10,
      completed_steps INTEGER NOT NULL DEFAULT 0,
      category TEXT NOT NULL DEFAULT 'Growth',
      deadline TEXT,
      status TEXT NOT NULL DEFAULT 'active',
      completed_at TEXT,
      created_at TEXT NOT NULL
    )`),
  ]);
  await ensureGoalColumns(db);
  await db.batch([
    db.prepare(`CREATE TABLE IF NOT EXISTS moment_goals (
      moment_id INTEGER NOT NULL REFERENCES moments(id) ON DELETE CASCADE,
      goal_id INTEGER NOT NULL REFERENCES goals(id) ON DELETE CASCADE
    )`),
    db.prepare(`CREATE TABLE IF NOT EXISTS chronicle_settings (
      id INTEGER PRIMARY KEY,
      display_name TEXT NOT NULL DEFAULT 'Alex',
      language TEXT NOT NULL DEFAULT 'en',
      tone TEXT NOT NULL DEFAULT 'thoughtful',
      timezone TEXT NOT NULL DEFAULT 'Europe/Moscow',
      reminders_enabled INTEGER NOT NULL DEFAULT 0,
      reminder_time TEXT NOT NULL DEFAULT '20:00',
      reminder_frequency TEXT NOT NULL DEFAULT 'daily',
      onboarding_complete INTEGER NOT NULL DEFAULT 0,
      selected_areas TEXT NOT NULL DEFAULT '["Growth","Work","Relationships","Health","Creativity","Rest"]'
    )`),
    db.prepare("CREATE INDEX IF NOT EXISTS idx_moments_created_at ON moments(created_at DESC)"),
    db.prepare("CREATE INDEX IF NOT EXISTS idx_moments_category_created_at ON moments(category, created_at DESC)"),
    db.prepare("CREATE UNIQUE INDEX IF NOT EXISTS idx_moment_goals_pair ON moment_goals(moment_id, goal_id)"),
    db.prepare("CREATE INDEX IF NOT EXISTS idx_moment_goals_goal_id ON moment_goals(goal_id)"),
    db.prepare("INSERT OR IGNORE INTO chronicle_settings (id) VALUES (1)"),
  ]);
  await ensureSettingsColumns(db);
  await db.prepare(`UPDATE chronicle_settings SET onboarding_complete = 1
    WHERE id = 1 AND onboarding_complete = 0
    AND (EXISTS (SELECT 1 FROM moments LIMIT 1) OR EXISTS (SELECT 1 FROM goals LIMIT 1))`).run();
  await db.prepare("PRAGMA optimize").run();
  return db;
}

function text(value: unknown, fallback = "") {
  return typeof value === "string" ? value.trim() : fallback;
}

function integer(value: unknown, fallback: number, minimum = 0) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? Math.max(minimum, Math.round(parsed)) : fallback;
}

function allowed(value: unknown, values: string[], fallback: string) {
  const result = text(value, fallback);
  return values.includes(result) ? result : fallback;
}

function selectedAreas(value: unknown) {
  const supported = ["Growth", "Work", "Relationships", "Health", "Creativity", "Rest"];
  if (!Array.isArray(value)) return supported;
  const result = [...new Set(value.map((item) => text(item)).filter((item) => supported.includes(item)))];
  return result.length ? result : supported;
}

async function replaceMomentGoals(db: D1Database, momentId: number, goalIds: number[] = []) {
  await db.prepare("DELETE FROM moment_goals WHERE moment_id = ?").bind(momentId).run();
  const uniqueIds = [...new Set(goalIds.map((id) => integer(id, 0, 1)).filter(Boolean))];
  if (uniqueIds.length) {
    await db.batch(uniqueIds.map((goalId) => db.prepare(
      "INSERT OR IGNORE INTO moment_goals (moment_id, goal_id) VALUES (?, ?)",
    ).bind(momentId, goalId)));
  }
}

async function readChronicle() {
  const db = await ensureSchema();
  const [moments, goals, links, settings] = await Promise.all([
    db.prepare(`SELECT id, title, content, category, mood,
      is_favorite AS isFavorite, created_at AS createdAt
      FROM moments ORDER BY created_at DESC, id DESC`).all(),
    db.prepare(`SELECT id, title, description, target_steps AS targetSteps,
      completed_steps AS completedSteps, category, deadline, status,
      completed_at AS completedAt, created_at AS createdAt
      FROM goals ORDER BY CASE status WHEN 'active' THEN 0 WHEN 'completed' THEN 1 ELSE 2 END, created_at DESC, id DESC`).all(),
    db.prepare("SELECT moment_id AS momentId, goal_id AS goalId FROM moment_goals").all(),
    db.prepare(`SELECT display_name AS displayName, language, tone, timezone,
      reminders_enabled AS remindersEnabled, reminder_time AS reminderTime,
      reminder_frequency AS reminderFrequency, onboarding_complete AS onboardingComplete,
      selected_areas AS selectedAreas FROM chronicle_settings WHERE id = 1`).first(),
  ]);
  const goalsByMoment = new Map<number, number[]>();
  for (const link of links.results) {
    const momentId = Number(link.momentId);
    goalsByMoment.set(momentId, [...(goalsByMoment.get(momentId) || []), Number(link.goalId)]);
  }
  return {
    moments: moments.results.map((row) => ({
      ...row,
      isFavorite: Boolean(row.isFavorite),
      goalIds: goalsByMoment.get(Number(row.id)) || [],
    })),
    goals: goals.results,
    settings: {
      displayName: settings?.displayName || "Alex",
      language: settings?.language || "en",
      tone: settings?.tone || "thoughtful",
      timezone: settings?.timezone || "Europe/Moscow",
      remindersEnabled: Boolean(settings?.remindersEnabled),
      reminderTime: settings?.reminderTime || "20:00",
      reminderFrequency: settings?.reminderFrequency || "daily",
      onboardingComplete: Boolean(settings?.onboardingComplete),
      selectedAreas: (() => {
        try { return selectedAreas(JSON.parse(String(settings?.selectedAreas || "[]"))); }
        catch { return selectedAreas([]); }
      })(),
    },
  };
}

export async function GET() {
  try {
    return Response.json(await readChronicle());
  } catch (error) {
    return Response.json({ error: error instanceof Error ? error.message : "Unable to load Chronicle." }, { status: 500 });
  }
}

export async function POST(request: Request) {
  try {
    const payload = (await request.json()) as Payload;
    const db = await ensureSchema();
    const now = new Date().toISOString();

    switch (payload.action) {
      case "createMoment": {
        const title = text(payload.title);
        const content = text(payload.content);
        if (!title || !content) return Response.json({ error: "Title and details are required." }, { status: 400 });
        const result = await db.prepare(`INSERT INTO moments
          (title, content, category, mood, is_favorite, created_at) VALUES (?, ?, ?, ?, 0, ?)`) 
          .bind(title, content, text(payload.category, "Growth"), text(payload.mood, "Proud"), now).run();
        await replaceMomentGoals(db, Number(result.meta.last_row_id), payload.goalIds);
        break;
      }
      case "updateMoment": {
        const id = integer(payload.id, 0, 1);
        const title = text(payload.title);
        const content = text(payload.content);
        if (!id || !title || !content) return Response.json({ error: "A valid moment is required." }, { status: 400 });
        await db.prepare("UPDATE moments SET title = ?, content = ?, category = ?, mood = ? WHERE id = ?")
          .bind(title, content, text(payload.category, "Growth"), text(payload.mood, "Proud"), id).run();
        await replaceMomentGoals(db, id, payload.goalIds);
        break;
      }
      case "deleteMoment":
        await db.prepare("DELETE FROM moments WHERE id = ?").bind(integer(payload.id, 0, 1)).run();
        break;
      case "toggleFavorite":
        await db.prepare("UPDATE moments SET is_favorite = ? WHERE id = ?")
          .bind(payload.favorite ? 1 : 0, integer(payload.id, 0, 1)).run();
        break;
      case "createGoal": {
        const title = text(payload.title);
        if (!title) return Response.json({ error: "Goal title is required." }, { status: 400 });
        await db.prepare(`INSERT INTO goals
          (title, description, target_steps, completed_steps, category, deadline, status, completed_at, created_at)
          VALUES (?, ?, ?, 0, ?, ?, 'active', NULL, ?)`) 
          .bind(title, text(payload.description), integer(payload.targetSteps, 10, 1), text(payload.category, "Growth"), text(payload.deadline) || null, now).run();
        break;
      }
      case "updateGoal": {
        const id = integer(payload.id, 0, 1);
        const target = integer(payload.targetSteps, 10, 1);
        const completed = Math.min(integer(payload.completedSteps, 0), target);
        const status = allowed(payload.status, ["active", "completed", "abandoned"], "active");
        await db.prepare(`UPDATE goals SET title = ?, description = ?, target_steps = ?, completed_steps = ?,
          category = ?, deadline = ?, status = ?, completed_at = ? WHERE id = ?`)
          .bind(text(payload.title, "Untitled goal"), text(payload.description), target, completed,
            text(payload.category, "Growth"), text(payload.deadline) || null, status,
            status === "completed" ? now : null, id).run();
        break;
      }
      case "deleteGoal":
        await db.prepare("DELETE FROM goals WHERE id = ?").bind(integer(payload.id, 0, 1)).run();
        break;
      case "updateSettings":
        await db.prepare(`UPDATE chronicle_settings SET display_name = ?, language = ?, tone = ?, timezone = ?,
          reminders_enabled = ?, reminder_time = ?, reminder_frequency = ? WHERE id = 1`)
          .bind(text(payload.displayName, "Alex"), allowed(payload.language, ["en", "ru"], "en"),
            allowed(payload.tone, ["gentle", "thoughtful", "direct"], "thoughtful"), text(payload.timezone, "Europe/Moscow"),
            payload.remindersEnabled ? 1 : 0, text(payload.reminderTime, "20:00"),
            allowed(payload.reminderFrequency, ["daily", "weekdays", "weekly"], "daily")).run();
        break;
      case "completeOnboarding": {
        const displayName = text(payload.displayName);
        const goalTitle = text(payload.goalTitle);
        const momentTitle = text(payload.momentTitle);
        const momentContent = text(payload.momentContent);
        const areas = selectedAreas(payload.selectedAreas);
        if (!displayName || !goalTitle || !momentTitle || !momentContent || areas.length < 3) {
          return Response.json({ error: "Complete every onboarding step and choose at least three life areas." }, { status: 400 });
        }
        const language = allowed(payload.language, ["en", "ru"], "en");
        await db.prepare(`UPDATE chronicle_settings SET display_name = ?, language = ?, selected_areas = ?, onboarding_complete = 1 WHERE id = 1`)
          .bind(displayName, language, JSON.stringify(areas)).run();
        const goalResult = await db.prepare(`INSERT INTO goals
          (title, description, target_steps, completed_steps, category, deadline, status, completed_at, created_at)
          VALUES (?, '', ?, 0, ?, NULL, 'active', NULL, ?)`)
          .bind(goalTitle, integer(payload.goalSteps, 10, 1), allowed(payload.goalCategory, areas, areas[0]), now).run();
        const momentResult = await db.prepare(`INSERT INTO moments
          (title, content, category, mood, is_favorite, created_at) VALUES (?, ?, ?, ?, 0, ?)`)
          .bind(momentTitle, momentContent, allowed(payload.momentCategory, areas, areas[0]),
            allowed(payload.momentMood, ["Proud", "Grateful", "Calm", "Excited", "Brave", "Thoughtful"], "Proud"), now).run();
        const goalId = Number(goalResult.meta.last_row_id);
        const momentId = Number(momentResult.meta.last_row_id);
        if (goalId && momentId) await db.prepare("INSERT OR IGNORE INTO moment_goals (moment_id, goal_id) VALUES (?, ?)").bind(momentId, goalId).run();
        break;
      }
      case "deleteAll":
        await db.batch([
          db.prepare("DELETE FROM moment_goals"), db.prepare("DELETE FROM moments"), db.prepare("DELETE FROM goals"),
        ]);
        break;
      case "deleteAccount":
        await db.batch([
          db.prepare("DELETE FROM moment_goals"), db.prepare("DELETE FROM moments"), db.prepare("DELETE FROM goals"),
          db.prepare(`UPDATE chronicle_settings SET display_name = 'Alex', language = 'en', tone = 'thoughtful',
            timezone = 'Europe/Moscow', reminders_enabled = 0, reminder_time = '20:00', reminder_frequency = 'daily',
            onboarding_complete = 0, selected_areas = '["Growth","Work","Relationships","Health","Creativity","Rest"]' WHERE id = 1`),
        ]);
        break;
      case "seedDemo": {
        const count = await db.prepare("SELECT COUNT(*) AS total FROM moments").first<{ total: number }>();
        if (!count?.total) {
          const yesterday = new Date(Date.now() - 86_400_000).toISOString();
          const lastWeek = new Date(Date.now() - 5 * 86_400_000).toISOString();
          const lastMonth = new Date(Date.now() - 32 * 86_400_000).toISOString();
          const results = await db.batch([
            db.prepare(`INSERT INTO moments (title, content, category, mood, is_favorite, created_at) VALUES (?, ?, ?, ?, ?, ?)`).bind("Finished the first version of my project", "I chose forward motion over a perfect result. And it worked.", "Growth", "Proud", 1, now),
            db.prepare(`INSERT INTO moments (title, content, category, mood, is_favorite, created_at) VALUES (?, ?, ?, ?, ?, ?)`).bind("A warm evening with the people I love", "We left our phones in another room, talked for hours, and laughed a lot.", "Relationships", "Grateful", 0, yesterday),
            db.prepare(`INSERT INTO moments (title, content, category, mood, is_favorite, created_at) VALUES (?, ?, ?, ?, ?, ?)`).bind("Shared my work before it felt perfect", "Honest feedback showed me exactly what to improve next.", "Work", "Brave", 0, lastWeek),
            db.prepare(`INSERT INTO moments (title, content, category, mood, is_favorite, created_at) VALUES (?, ?, ?, ?, ?, ?)`).bind("Took a quiet morning for myself", "A slow walk helped me hear what I actually needed.", "Health", "Calm", 0, lastMonth),
          ]);
          const goalResult = await db.prepare(`INSERT INTO goals
            (title, description, target_steps, completed_steps, category, deadline, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 'active', ?)`).bind("Launch my own product", "Turn Chronicle into something people can use every day.", 25, 17, "Work", new Date(Date.now() + 30 * 86_400_000).toISOString().slice(0, 10), now).run();
          const goalId = Number(goalResult.meta.last_row_id);
          const linkedMomentId = Number(results[0].meta.last_row_id);
          if (goalId && linkedMomentId) await db.prepare("INSERT OR IGNORE INTO moment_goals (moment_id, goal_id) VALUES (?, ?)").bind(linkedMomentId, goalId).run();
        }
        break;
      }
      default:
        return Response.json({ error: "Unsupported action." }, { status: 400 });
    }
    return Response.json(await readChronicle());
  } catch (error) {
    return Response.json({ error: error instanceof Error ? error.message : "Unable to update Chronicle." }, { status: 500 });
  }
}
