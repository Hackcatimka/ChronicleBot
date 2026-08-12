import {
  estimateCost,
  getAiDatabase,
  getRuntimeSecrets,
  readAiConfiguration,
  recordAiUsage,
} from "@/lib/ai-runtime";
import { AuthenticationRequiredError, resolveProfileId } from "@/lib/supabase-server";

export const dynamic = "force-dynamic";

type ReflectionPayload = {
  language?: "en" | "ru";
  moments?: Array<{ title?: string; content?: string; category?: string; mood?: string }>;
  goals?: Array<{ title?: string; completedSteps?: number; targetSteps?: number; category?: string }>;
  period?: string;
};

type ProviderResult = {
  text: string;
  inputTokens: number;
  outputTokens: number;
  reasoningTokens: number;
  totalTokens: number;
};

type GrokResponse = {
  error?: { code?: string; message?: string };
  choices?: Array<{ message?: { content?: string } }>;
  usage?: {
    prompt_tokens?: number;
    completion_tokens?: number;
    total_tokens?: number;
    completion_tokens_details?: { reasoning_tokens?: number };
  };
};

type GeminiResponse = {
  error?: { status?: string; message?: string };
  candidates?: Array<{ content?: { parts?: Array<{ text?: string }> } }>;
  usageMetadata?: {
    promptTokenCount?: number;
    candidatesTokenCount?: number;
    thoughtsTokenCount?: number;
    totalTokenCount?: number;
  };
};

function clean(value: unknown, limit = 600) {
  return typeof value === "string" ? value.trim().slice(0, limit) : "";
}

function buildPrompt(payload: ReflectionPayload) {
  const moments = (payload.moments || []).slice(0, 20).map((moment, index) =>
    `${index + 1}. [${clean(moment.category, 40)} · ${clean(moment.mood, 40)}] ${clean(moment.title, 160)} — ${clean(moment.content)}`,
  ).join("\n");
  const goals = (payload.goals || []).slice(0, 10).map((goal, index) =>
    `${index + 1}. [${clean(goal.category, 40)}] ${clean(goal.title, 160)} — ${Number(goal.completedSteps || 0)}/${Math.max(1, Number(goal.targetSteps || 1))}`,
  ).join("\n");
  const language = payload.language === "ru" ? "Russian" : "English";
  return `Write one thoughtful personal-journal reflection in ${language}. Use only the supplied data. Notice a concrete pattern, acknowledge progress, and suggest one gentle next step. Do not diagnose, moralize, or invent facts. Keep it between 90 and 150 words.\n\nPeriod: ${clean(payload.period, 80) || "recent entries"}\n\nMoments:\n${moments || "No moments supplied."}\n\nGoals:\n${goals || "No goals supplied."}`;
}

async function callGrok(apiKey: string, model: string, prompt: string): Promise<ProviderResult> {
  const response = await fetch("https://api.x.ai/v1/chat/completions", {
    method: "POST",
    headers: { Authorization: `Bearer ${apiKey}`, "Content-Type": "application/json" },
    body: JSON.stringify({
      model,
      messages: [
        { role: "system", content: "You are Chronicle, a calm reflection assistant for a private journal." },
        { role: "user", content: prompt },
      ],
      max_tokens: 320,
    }),
  });
  const body = await response.json() as GrokResponse;
  if (!response.ok) throw new Error(String(body?.error?.code || body?.error?.message || `xai_${response.status}`));
  const usage = body.usage || {};
  return {
    text: String(body.choices?.[0]?.message?.content || "").trim(),
    inputTokens: Number(usage.prompt_tokens || 0),
    outputTokens: Number(usage.completion_tokens || 0),
    reasoningTokens: Number(usage.completion_tokens_details?.reasoning_tokens || 0),
    totalTokens: Number(usage.total_tokens || 0),
  };
}

async function callGemini(apiKey: string, model: string, prompt: string): Promise<ProviderResult> {
  const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${encodeURIComponent(model)}:generateContent`, {
    method: "POST",
    headers: { "x-goog-api-key": apiKey, "Content-Type": "application/json" },
    body: JSON.stringify({
      system_instruction: { parts: [{ text: "You are Chronicle, a calm reflection assistant for a private journal." }] },
      contents: [{ role: "user", parts: [{ text: prompt }] }],
      generationConfig: { maxOutputTokens: 320 },
    }),
  });
  const body = await response.json() as GeminiResponse;
  if (!response.ok) throw new Error(String(body?.error?.status || body?.error?.message || `gemini_${response.status}`));
  const usage = body.usageMetadata || {};
  return {
    text: (body.candidates?.[0]?.content?.parts || []).map((part: Record<string, unknown>) => String(part.text || "")).join("").trim(),
    inputTokens: Number(usage.promptTokenCount || 0),
    outputTokens: Number(usage.candidatesTokenCount || 0),
    reasoningTokens: Number(usage.thoughtsTokenCount || 0),
    totalTokens: Number(usage.totalTokenCount || 0),
  };
}

export async function POST(request: Request) {
  const startedAt = Date.now();
  const db = getAiDatabase();
  let profileId = "anonymous";
  try {
    profileId = await resolveProfileId(request, () => "anonymous");
  } catch (error) {
    if (error instanceof AuthenticationRequiredError) return Response.json({ error: "Authentication required." }, { status: 401 });
    throw error;
  }
  const configuration = await readAiConfiguration(db);
  const provider = configuration.provider;
  const model = provider === "grok" ? configuration.grokModel : configuration.geminiModel;
  try {
    const payload = await request.json() as ReflectionPayload;
    const prompt = buildPrompt(payload);
    const secrets = getRuntimeSecrets();
    const apiKey = provider === "grok" ? secrets.XAI_API_KEY : secrets.GEMINI_API_KEY;
    if (!apiKey) throw new Error(`${provider}_api_key_missing`);
    const result = provider === "grok"
      ? await callGrok(apiKey, model, prompt)
      : await callGemini(apiKey, model, prompt);
    if (!result.text) throw new Error(`${provider}_empty_response`);
    const estimatedCostUsd = estimateCost(provider, model, result.inputTokens, result.outputTokens);
    await recordAiUsage(db, {
      provider, model, profileId, feature: "reflection", ...result,
      estimatedCostUsd, latencyMs: Date.now() - startedAt, status: "success",
    });
    return Response.json({ reflection: result.text, provider, model, usage: { ...result, estimatedCostUsd } });
  } catch (error) {
    const errorCode = error instanceof Error ? error.message.slice(0, 160) : "unknown_error";
    await recordAiUsage(db, {
      provider, model, profileId, feature: "reflection", inputTokens: 0, outputTokens: 0,
      reasoningTokens: 0, totalTokens: 0, estimatedCostUsd: 0,
      latencyMs: Date.now() - startedAt, status: "error", errorCode,
    });
    const missingKey = errorCode.endsWith("_api_key_missing");
    return Response.json({ error: missingKey ? "The selected AI provider is not connected." : "AI reflection is temporarily unavailable." }, { status: missingKey ? 503 : 502 });
  }
}
