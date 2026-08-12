"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { supabase } from "@/lib/supabase-client";
import "../auth.css";

export default function UpdatePasswordPage() {
  const [ready, setReady] = useState(false); const [error, setError] = useState(() => supabase ? "" : "Supabase ещё не подключён."); const [done, setDone] = useState(false);
  useEffect(() => { if (!supabase) return; void supabase.auth.getSession().then(({ data }) => setReady(Boolean(data.session))); }, []);
  async function submit(event: FormEvent<HTMLFormElement>) { event.preventDefault(); const password = String(new FormData(event.currentTarget).get("password") || ""); if (!supabase) return; const { error: updateError } = await supabase.auth.updateUser({ password }); if (updateError) setError(updateError.message); else setDone(true); }
  return <main className="auth-status"><div className="auth-status-mark">C</div><h1>{done ? "Пароль обновлён" : "Новый пароль"}</h1>{done ? <><p>Теперь можно войти в Chronicle с новым паролем.</p><Link href="/auth">Перейти ко входу</Link></> : ready ? <form className="auth-recovery-form" onSubmit={submit}><label>Новый пароль<input name="password" type="password" minLength={8} required autoFocus /></label>{error && <div className="auth-error">{error}</div>}<button className="auth-submit">Сохранить пароль</button></form> : <><p>{error || "Проверяем ссылку восстановления…"}</p><span className="auth-spinner" /></>}</main>;
}
