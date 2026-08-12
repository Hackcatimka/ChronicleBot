import { env } from "cloudflare:workers";
import { CHRONICLE_SUPABASE_PUBLISHABLE_KEY, CHRONICLE_SUPABASE_URL } from "@/lib/supabase-config";

type SupabaseRuntime = {
  SUPABASE_URL?: string;
  SUPABASE_PUBLISHABLE_KEY?: string;
  NEXT_PUBLIC_SUPABASE_URL?: string;
  NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY?: string;
};

export type ChronicleAuthUser = { id: string; email?: string };

function configuration() {
  const runtime = env as typeof env & SupabaseRuntime;
  return {
    url: runtime.SUPABASE_URL || runtime.NEXT_PUBLIC_SUPABASE_URL || CHRONICLE_SUPABASE_URL,
    key: runtime.SUPABASE_PUBLISHABLE_KEY || runtime.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY || CHRONICLE_SUPABASE_PUBLISHABLE_KEY,
  };
}

export function supabaseServerConfigured() {
  const config = configuration();
  return Boolean(config.url && config.key);
}

export async function getSupabaseUser(request: Request): Promise<ChronicleAuthUser | null> {
  const config = configuration();
  const authorization = request.headers.get("authorization") || "";
  if (!config.url || !config.key || !authorization.startsWith("Bearer ")) return null;
  const response = await fetch(`${config.url}/auth/v1/user`, {
    headers: { apikey: config.key, Authorization: authorization },
  });
  if (!response.ok) return null;
  const user = await response.json() as { id?: string; email?: string };
  return user.id ? { id: user.id, email: user.email } : null;
}

export class AuthenticationRequiredError extends Error {
  constructor() { super("Authentication required"); this.name = "AuthenticationRequiredError"; }
}

export async function resolveProfileId(request: Request, fallback: () => string) {
  const user = await getSupabaseUser(request);
  if (user) return user.id;
  if (supabaseServerConfigured()) throw new AuthenticationRequiredError();
  return fallback();
}
