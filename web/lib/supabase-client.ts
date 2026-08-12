"use client";

import { createClient } from "@supabase/supabase-js";
import { CHRONICLE_SUPABASE_PUBLISHABLE_KEY, CHRONICLE_SUPABASE_URL } from "@/lib/supabase-config";

const url = process.env.NEXT_PUBLIC_SUPABASE_URL || CHRONICLE_SUPABASE_URL;
const publishableKey = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY || CHRONICLE_SUPABASE_PUBLISHABLE_KEY;

export const supabaseConfigured = Boolean(url && publishableKey);
export const supabase = supabaseConfigured
  ? createClient(url, publishableKey, { auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: true } })
  : null;

export async function authenticatedHeaders() {
  if (!supabase) return {} as Record<string, string>;
  const { data } = await supabase.auth.getSession();
  return data.session?.access_token ? { Authorization: `Bearer ${data.session.access_token}` } : {};
}
