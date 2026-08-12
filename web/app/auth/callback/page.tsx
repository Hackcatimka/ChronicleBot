"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { supabase } from "@/lib/supabase-client";
import "../auth.css";

export default function AuthCallbackPage() {
  const [error, setError] = useState(() => supabase ? "" : "Supabase ещё не подключён.");
  useEffect(() => {
    if (!supabase) return;
    const finish = async () => {
      const { data, error: sessionError } = await supabase.auth.getSession();
      if (sessionError) { setError(sessionError.message); return; }
      if (data.session) window.location.replace("/app");
      else setError("Ссылка недействительна или уже использована.");
    };
    const timer = window.setTimeout(() => void finish(), 450);
    return () => window.clearTimeout(timer);
  }, []);
  return <main className="auth-status"><div className="auth-status-mark">C</div>{error ? <><h1>Не удалось подтвердить вход</h1><p>{error}</p><Link href="/auth">Вернуться ко входу</Link></> : <><h1>Подтверждаем аккаунт…</h1><p>Через несколько секунд откроется ваш Chronicle.</p><span className="auth-spinner" /></>}</main>;
}
