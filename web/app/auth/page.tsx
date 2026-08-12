"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { supabase, supabaseConfigured } from "@/lib/supabase-client";
import "./auth.css";

type Mode = "login" | "register" | "forgot";

export default function AuthPage() {
  const [mode, setMode] = useState<Mode>("login");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setLoading(true); setError(""); setMessage("");
    const form = new FormData(event.currentTarget);
    const email = String(form.get("email") || "").trim();
    const password = String(form.get("password") || "");
    const name = String(form.get("name") || "").trim();
    try {
      if (!supabase) throw new Error("Supabase ещё не подключён к Chronicle.");
      if (mode === "forgot") {
        const { error: resetError } = await supabase.auth.resetPasswordForEmail(email, { redirectTo: `${window.location.origin}/auth/update-password` });
        if (resetError) throw resetError;
        setMessage("Письмо для восстановления отправлено. Проверьте входящие и папку «Спам».");
      } else if (mode === "register") {
        const { data, error: signUpError } = await supabase.auth.signUp({ email, password, options: { data: { display_name: name }, emailRedirectTo: `${window.location.origin}/auth/callback` } });
        if (signUpError) throw signUpError;
        if (data.session) window.location.assign("/app");
        else setMessage("Аккаунт создан. Подтвердите адрес по ссылке из письма.");
      } else {
        const { error: loginError } = await supabase.auth.signInWithPassword({ email, password });
        if (loginError) throw loginError;
        const returnTo = new URLSearchParams(window.location.search).get("returnTo");
        window.location.assign(returnTo?.startsWith("/") ? returnTo : "/app");
      }
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Не удалось выполнить запрос."); }
    finally { setLoading(false); }
  }

  return <main className="auth-shell"><section className="auth-story"><Link href="/" className="auth-logo" aria-label="Chronicle"><span /></Link><div><small>A PRIVATE PLACE TO NOTICE YOUR LIFE</small><h1>{mode === "register" ? "Начните свою хронику." : mode === "forgot" ? "Вернитесь к своей истории." : "Ваши моменты ждут."}</h1><p>Личный дневник, цели и бережные размышления остаются связаны с вашим аккаунтом на любом устройстве.</p></div><blockquote>“We do not remember days. We remember moments.”</blockquote></section><section className="auth-panel"><div className="auth-card"><small>CHRONICLE ACCOUNT</small><h2>{mode === "login" ? "Войти" : mode === "register" ? "Создать аккаунт" : "Восстановить пароль"}</h2><p>{mode === "login" ? "Продолжите с того места, где остановились." : mode === "register" ? "Ваш дневник будет доступен только после входа." : "Мы отправим безопасную ссылку на вашу почту."}</p>{!supabaseConfigured && <div className="auth-warning">Подключение Supabase ещё не завершено. Экран готов, но регистрация включится после выбора проекта.</div>}<form onSubmit={submit}>{mode === "register" && <label>Имя<input name="name" autoComplete="name" minLength={2} maxLength={40} required placeholder="Как к вам обращаться" /></label>}<label>Электронная почта<input name="email" type="email" autoComplete="email" required placeholder="you@example.com" /></label>{mode !== "forgot" && <label>Пароль<input name="password" type="password" autoComplete={mode === "register" ? "new-password" : "current-password"} minLength={8} required placeholder="Минимум 8 символов" /></label>}{error && <div className="auth-error">{error}</div>}{message && <div className="auth-success">{message}</div>}<button className="auth-submit" disabled={loading || !supabaseConfigured}>{loading ? "Подождите…" : mode === "login" ? "Войти в Chronicle" : mode === "register" ? "Создать аккаунт" : "Отправить ссылку"}</button></form><div className="auth-switch">{mode === "login" ? <><button onClick={() => setMode("forgot")}>Забыли пароль?</button><span>Нет аккаунта? <button onClick={() => setMode("register")}>Зарегистрироваться</button></span></> : <button onClick={() => { setMode("login"); setMessage(""); setError(""); }}>← Вернуться ко входу</button>}</div></div></section></main>;
}
