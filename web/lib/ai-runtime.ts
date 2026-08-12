import { env } from "cloudflare:workers";
import { getSupabaseUser } from "@/lib/supabase-server";

export type AiProvider = "grok" | "gemini";

// SHA-256 of the owner's normalized email. The address itself stays out of source control.
const CHRONICLE_OWNER_EMAIL_HASH = "ecdf6739ded457daf80ccc8f482fef05da6ddf92a9a22878b915f32b3207c089";

type RuntimeSecrets = {
  XAI_API_KEY?: string;
  GEMINI_API_KEY?: string;
  ADMIN_API_KEY?: string;
  ADMIN_EMAIL?: string;
};

export type AiConfiguration = {
  provider: AiProvider;
  grokModel: string;
  geminiModel: string;
};

export type AiUsageRecord = {
  provider: AiProvider;
  model: string;
  profileId: string;
  feature: string;
  inputTokens: number;
  outputTokens: number;
  reasoningTokens: number;
  totalTokens: number;
  estimatedCostUsd: number;
  latencyMs: number;
  status: "success" | "error";
  errorCode?: string;
};

export function getAiDatabase() {
  if (!env.DB) throw new Error("Chronicle database is unavailable.");
  return env.DB;
}

export function getRuntimeSecrets() {
  return env as typeof env & RuntimeSecrets;
}

export async function ensureAiSchema(db: D1Database) {
  await db.batch([
    db.prepare(`CREATE TABLE IF NOT EXISTS ai_settings (
      id INTEGER PRIMARY KEY,
      provider TEXT NOT NULL DEFAULT 'gemini',
      grok_model TEXT NOT NULL DEFAULT 'grok-4.5',
      gemini_model TEXT NOT NULL DEFAULT 'gemini-3.6-flash',
      updated_at TEXT NOT NULL
    )`),
    db.prepare(`CREATE TABLE IF NOT EXISTS ai_usage (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      provider TEXT NOT NULL,
      model TEXT NOT NULL,
      profile_id TEXT NOT NULL,
      feature TEXT NOT NULL DEFAULT 'reflection',
      input_tokens INTEGER NOT NULL DEFAULT 0,
      output_tokens INTEGER NOT NULL DEFAULT 0,
      reasoning_tokens INTEGER NOT NULL DEFAULT 0,
      total_tokens INTEGER NOT NULL DEFAULT 0,
      estimated_cost_usd REAL NOT NULL DEFAULT 0,
      latency_ms INTEGER NOT NULL DEFAULT 0,
      status TEXT NOT NULL DEFAULT 'success',
      error_code TEXT,
      created_at TEXT NOT NULL
    )`),
    db.prepare("CREATE INDEX IF NOT EXISTS idx_ai_usage_created_at ON ai_usage(created_at DESC)"),
    db.prepare("CREATE INDEX IF NOT EXISTS idx_ai_usage_provider_created_at ON ai_usage(provider, created_at DESC)"),
    db.prepare("CREATE INDEX IF NOT EXISTS idx_ai_usage_profile_created_at ON ai_usage(profile_id, created_at DESC)"),
  ]);
  await db.prepare(`INSERT OR IGNORE INTO ai_settings
    (id, provider, grok_model, gemini_model, updated_at) VALUES (1, 'gemini', 'grok-4.5', 'gemini-3.6-flash', ?)`)
    .bind(new Date().toISOString()).run();
}

export async function readAiConfiguration(db: D1Database): Promise<AiConfiguration> {
  await ensureAiSchema(db);
  const row = await db.prepare(`SELECT provider, grok_model AS grokModel,
    gemini_model AS geminiModel FROM ai_settings WHERE id = 1`).first<Record<string, unknown>>();
  return {
    provider: row?.provider === "grok" ? "grok" : "gemini",
    grokModel: String(row?.grokModel || "grok-4.5"),
    geminiModel: String(row?.geminiModel || "gemini-3.6-flash"),
  };
}

export function estimateCost(provider: AiProvider, model: string, inputTokens: number, outputTokens: number) {
  const rates = provider === "grok"
    ? (model.startsWith("grok-4.5") ? { input: 2, output: 6 } : { input: 0, output: 0 })
    : (model.startsWith("gemini-3.6-flash") ? { input: 1.5, output: 7.5 } : { input: 0, output: 0 });
  return Number((((inputTokens * rates.input) + (outputTokens * rates.output)) / 1_000_000).toFixed(8));
}

export async function recordAiUsage(db: D1Database, usage: AiUsageRecord) {
  await db.prepare(`INSERT INTO ai_usage
    (provider, model, profile_id, feature, input_tokens, output_tokens, reasoning_tokens,
     total_tokens, estimated_cost_usd, latency_ms, status, error_code, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`)
    .bind(usage.provider, usage.model, usage.profileId, usage.feature, usage.inputTokens,
      usage.outputTokens, usage.reasoningTokens, usage.totalTokens, usage.estimatedCostUsd,
      usage.latencyMs, usage.status, usage.errorCode || null, new Date().toISOString()).run();
}

export function profileIdFromRequest(request: Request) {
  const cookie = request.headers.get("cookie") || "";
  const match = cookie.match(/(?:^|;\s*)chronicle_profile=([a-zA-Z0-9-]+)/);
  return match?.[1] || "anonymous";
}

export async function secureEqual(left: string, right: string) {
  const encoder = new TextEncoder();
  const [a, b] = await Promise.all([
    crypto.subtle.digest("SHA-256", encoder.encode(left)),
    crypto.subtle.digest("SHA-256", encoder.encode(right)),
  ]);
  const aa = new Uint8Array(a);
  const bb = new Uint8Array(b);
  let difference = 0;
  for (let index = 0; index < aa.length; index += 1) difference |= aa[index] ^ bb[index];
  return difference === 0;
}

async function sha256Hex(value: string) {
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(value));
  return Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, "0")).join("");
}

async function matchesOwner(email?: string) {
  const normalized = email?.trim().toLowerCase();
  if (!normalized) return false;
  const configuredEmail = getRuntimeSecrets().ADMIN_EMAIL?.trim().toLowerCase();
  if (configuredEmail && await secureEqual(configuredEmail, normalized)) return true;
  return secureEqual(await sha256Hex(normalized), CHRONICLE_OWNER_EMAIL_HASH);
}

export async function requireAdmin(request: Request) {
  const supabaseUser = await getSupabaseUser(request);
  if (await matchesOwner(supabaseUser?.email)) return true;
  if (await matchesOwner(request.headers.get("oai-authenticated-user-email") || undefined)) return true;
  const configured = getRuntimeSecrets().ADMIN_API_KEY;
  const supplied = request.headers.get("x-admin-key") || "";
  return Boolean(configured && supplied && await secureEqual(configured, supplied));
}
