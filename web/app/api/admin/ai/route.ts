import { getAiDatabase, getRuntimeSecrets, readAiConfiguration, requireAdmin } from "@/lib/ai-runtime";

export const dynamic = "force-dynamic";

function modelName(value: unknown, fallback: string) {
  const result = typeof value === "string" ? value.trim() : "";
  return /^[a-zA-Z0-9._:-]{3,100}$/.test(result) ? result : fallback;
}

function periodWindow(request: Request) {
  const period = new URL(request.url).searchParams.get("period");
  if (period === "today") return { period, modifier: "start of day" };
  if (period === "year") return { period, modifier: "-365 days" };
  if (period === "month") return { period, modifier: "-30 days" };
  return { period: "week", modifier: "-7 days" };
}

async function ensureProfileActivityColumns(db: D1Database) {
  const columns = await db.prepare("PRAGMA table_info(chronicle_profiles)").all<{ name: string }>();
  const names = new Set(columns.results.map((column) => column.name));
  if (!names.has("created_at")) await db.prepare("ALTER TABLE chronicle_profiles ADD COLUMN created_at TEXT NOT NULL DEFAULT ''").run();
  if (!names.has("last_active_at")) await db.prepare("ALTER TABLE chronicle_profiles ADD COLUMN last_active_at TEXT NOT NULL DEFAULT ''").run();
  const now = new Date().toISOString();
  await db.prepare("UPDATE chronicle_profiles SET created_at = ? WHERE created_at = ''").bind(now).run();
  await db.prepare("UPDATE chronicle_profiles SET last_active_at = created_at WHERE last_active_at = ''").run();
}

export async function GET(request: Request) {
  if (!await requireAdmin(request)) return Response.json({ error: "Unauthorized" }, { status: 401 });
  const db = getAiDatabase();
  await ensureProfileActivityColumns(db);
  const configuration = await readAiConfiguration(db);
  const { period, modifier } = periodWindow(request);
  const [summary, providers, daily, recent, productSummary, languages, areas, goalStatuses, reminders, engagement, momentTrend, registrationTrend, retention, churn] = await Promise.all([
    db.prepare(`SELECT COUNT(*) AS requests,
      SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) AS successes,
      SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) AS errors,
      COALESCE(SUM(input_tokens), 0) AS inputTokens,
      COALESCE(SUM(output_tokens), 0) AS outputTokens,
      COALESCE(SUM(reasoning_tokens), 0) AS reasoningTokens,
      COALESCE(SUM(total_tokens), 0) AS totalTokens,
      COALESCE(SUM(estimated_cost_usd), 0) AS estimatedCostUsd,
      COALESCE(AVG(latency_ms), 0) AS averageLatencyMs
      FROM ai_usage WHERE created_at >= datetime('now', '-30 days')`).first(),
    db.prepare(`SELECT provider, COUNT(*) AS requests,
      COALESCE(SUM(total_tokens), 0) AS totalTokens,
      COALESCE(SUM(estimated_cost_usd), 0) AS estimatedCostUsd,
      COALESCE(AVG(latency_ms), 0) AS averageLatencyMs
      FROM ai_usage WHERE created_at >= datetime('now', '-30 days') GROUP BY provider ORDER BY provider`).all(),
    db.prepare(`SELECT substr(created_at, 1, 10) AS day, COUNT(*) AS requests,
      COALESCE(SUM(total_tokens), 0) AS totalTokens,
      COALESCE(SUM(estimated_cost_usd), 0) AS estimatedCostUsd
      FROM ai_usage WHERE created_at >= datetime('now', '-13 days')
      GROUP BY substr(created_at, 1, 10) ORDER BY day`).all(),
    db.prepare(`SELECT id, provider, model, feature, input_tokens AS inputTokens,
      output_tokens AS outputTokens, reasoning_tokens AS reasoningTokens,
      total_tokens AS totalTokens, estimated_cost_usd AS estimatedCostUsd,
      latency_ms AS latencyMs, status, error_code AS errorCode, created_at AS createdAt
      FROM ai_usage ORDER BY created_at DESC LIMIT 30`).all(),
    db.prepare(`SELECT
      (SELECT COUNT(*) FROM chronicle_profiles) AS totalUsers,
      (SELECT COUNT(*) FROM chronicle_profiles WHERE created_at >= datetime('now', ?)) AS newUsers,
      (SELECT COUNT(DISTINCT profile_id) FROM moments WHERE created_at >= datetime('now', ?)) AS activeUsers,
      (SELECT COUNT(*) FROM chronicle_profiles p WHERE NOT EXISTS (SELECT 1 FROM moments m WHERE m.profile_id = p.id)) AS usersWithoutMoments,
      (SELECT COUNT(*) FROM moments) AS totalMoments,
      (SELECT COUNT(*) FROM moments WHERE created_at >= datetime('now', ?)) AS periodMoments,
      (SELECT COUNT(*) FROM goals WHERE created_at >= datetime('now', ?)) AS periodGoals,
      (SELECT COUNT(*) FROM chronicle_profiles WHERE reminders_enabled = 1) AS usersWithReminders`)
      .bind(modifier, modifier, modifier, modifier).first(),
    db.prepare("SELECT language, COUNT(*) AS count FROM chronicle_profiles GROUP BY language ORDER BY count DESC").all(),
    db.prepare(`SELECT category, COUNT(*) AS count FROM moments WHERE created_at >= datetime('now', ?)
      GROUP BY category ORDER BY count DESC`).bind(modifier).all(),
    db.prepare("SELECT status, COUNT(*) AS count FROM goals GROUP BY status ORDER BY count DESC").all(),
    db.prepare("SELECT reminder_frequency AS frequency, COUNT(*) AS count FROM chronicle_profiles WHERE reminders_enabled = 1 GROUP BY reminder_frequency").all(),
    db.prepare(`SELECT bucket, COUNT(*) AS users FROM (
      SELECT profile_id, CASE WHEN COUNT(*) = 1 THEN '1' WHEN COUNT(*) <= 5 THEN '2–5'
        WHEN COUNT(*) <= 15 THEN '6–15' ELSE '16+' END AS bucket
      FROM moments WHERE created_at >= datetime('now', ?) GROUP BY profile_id
    ) GROUP BY bucket`).bind(modifier).all(),
    db.prepare(`SELECT substr(created_at, 1, 10) AS day, COUNT(*) AS count FROM moments
      WHERE created_at >= datetime('now', '-6 days') GROUP BY substr(created_at, 1, 10) ORDER BY day`).all(),
    db.prepare(`SELECT substr(created_at, 1, 10) AS day, COUNT(*) AS count FROM chronicle_profiles
      WHERE created_at >= datetime('now', '-6 days') GROUP BY substr(created_at, 1, 10) ORDER BY day`).all(),
    db.prepare(`SELECT
      SUM(CASE WHEN created_at < datetime('now', '-1 day') AND EXISTS (SELECT 1 FROM moments m WHERE m.profile_id = chronicle_profiles.id AND m.created_at >= datetime(chronicle_profiles.created_at, '+1 day')) THEN 1 ELSE 0 END) AS day1Retained,
      SUM(CASE WHEN created_at < datetime('now', '-1 day') THEN 1 ELSE 0 END) AS day1Eligible,
      SUM(CASE WHEN created_at < datetime('now', '-7 days') AND EXISTS (SELECT 1 FROM moments m WHERE m.profile_id = chronicle_profiles.id AND m.created_at >= datetime(chronicle_profiles.created_at, '+7 days')) THEN 1 ELSE 0 END) AS day7Retained,
      SUM(CASE WHEN created_at < datetime('now', '-7 days') THEN 1 ELSE 0 END) AS day7Eligible,
      SUM(CASE WHEN created_at < datetime('now', '-30 days') AND EXISTS (SELECT 1 FROM moments m WHERE m.profile_id = chronicle_profiles.id AND m.created_at >= datetime(chronicle_profiles.created_at, '+30 days')) THEN 1 ELSE 0 END) AS day30Retained,
      SUM(CASE WHEN created_at < datetime('now', '-30 days') THEN 1 ELSE 0 END) AS day30Eligible
      FROM chronicle_profiles`).first(),
    db.prepare(`SELECT
      SUM(CASE WHEN created_at < datetime('now', '-7 days') AND last_active_at < datetime('now', '-7 days') THEN 1 ELSE 0 END) AS silent7,
      SUM(CASE WHEN created_at < datetime('now', '-14 days') AND last_active_at < datetime('now', '-14 days') THEN 1 ELSE 0 END) AS silent14,
      SUM(CASE WHEN created_at < datetime('now', '-30 days') AND last_active_at < datetime('now', '-30 days') THEN 1 ELSE 0 END) AS silent30
      FROM chronicle_profiles`).first(),
  ]);
  const secrets = getRuntimeSecrets();
  return Response.json({
    configuration,
    connected: { grok: Boolean(secrets.XAI_API_KEY), gemini: Boolean(secrets.GEMINI_API_KEY) },
    summary: summary || {}, providers: providers.results, daily: daily.results, recent: recent.results,
    product: {
      period, summary: productSummary || {}, languages: languages.results, areas: areas.results,
      goalStatuses: goalStatuses.results, reminders: reminders.results, engagement: engagement.results,
      momentTrend: momentTrend.results, registrationTrend: registrationTrend.results,
      retention: retention || {}, churn: churn || {},
    },
  });
}

export async function POST(request: Request) {
  if (!await requireAdmin(request)) return Response.json({ error: "Unauthorized" }, { status: 401 });
  const payload = await request.json() as Record<string, unknown>;
  const db = getAiDatabase();
  const current = await readAiConfiguration(db);
  const provider = payload.provider === "grok" ? "grok" : payload.provider === "gemini" ? "gemini" : current.provider;
  const grokModel = modelName(payload.grokModel, current.grokModel);
  const geminiModel = modelName(payload.geminiModel, current.geminiModel);
  await db.prepare(`UPDATE ai_settings SET provider = ?, grok_model = ?, gemini_model = ?, updated_at = ? WHERE id = 1`)
    .bind(provider, grokModel, geminiModel, new Date().toISOString()).run();
  return Response.json({ configuration: { provider, grokModel, geminiModel } });
}
