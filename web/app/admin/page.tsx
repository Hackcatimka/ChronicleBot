"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { authenticatedHeaders } from "@/lib/supabase-client";
import "./admin.css";

type Provider = "grok" | "gemini";
type Period = "today" | "week" | "month" | "year";
type Row = Record<string, number | string | null>;
type Dashboard = {
  configuration: { provider: Provider; grokModel: string; geminiModel: string };
  connected: Record<Provider, boolean>;
  summary: Record<string, number>;
  daily: Row[];
  recent: Row[];
  product: {
    period: Period; summary: Record<string, number>; languages: Row[]; areas: Row[];
    goalStatuses: Row[]; reminders: Row[]; engagement: Row[]; momentTrend: Row[];
    registrationTrend: Row[]; retention: Record<string, number>; churn: Record<string, number>;
  };
};

const emptyDashboard: Dashboard = {
  configuration: { provider: "gemini", grokModel: "grok-4.5", geminiModel: "gemini-3.6-flash" },
  connected: { grok: false, gemini: false }, summary: {}, daily: [], recent: [],
  product: { period: "week", summary: {}, languages: [], areas: [], goalStatuses: [], reminders: [], engagement: [], momentTrend: [], registrationTrend: [], retention: {}, churn: {} },
};

function number(value: unknown) { return Number(value || 0); }
function formatNumber(value: unknown) { return new Intl.NumberFormat("ru-RU").format(number(value)); }
function money(value: unknown) { return `$${number(value).toFixed(number(value) < 0.01 ? 4 : 2)}`; }
function percent(part: unknown, total: unknown) { return number(total) ? Math.round(number(part) / number(total) * 100) : 0; }

export default function AdminAiPage() {
  const [dashboard, setDashboard] = useState<Dashboard>(emptyDashboard);
  const [period, setPeriod] = useState<Period>("week");
  const [loading, setLoading] = useState(true);
  const [accessResolved, setAccessResolved] = useState(false);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  const load = useCallback(async (selectedPeriod: Period) => {
    setLoading(true); setError("");
    try {
      const response = await fetch(`/api/admin/ai?period=${selectedPeriod}`, { headers: await authenticatedHeaders() });
      if (response.status === 401) { window.location.assign(`/auth?returnTo=${encodeURIComponent("/admin")}`); return; }
      if (!response.ok) { setAccessResolved(true); throw new Error("Не удалось загрузить статистику."); }
      setDashboard(await response.json() as Dashboard);
      setAccessResolved(true);
    } catch (reason) { setAccessResolved(true); setError(reason instanceof Error ? reason.message : "Не удалось открыть панель."); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => {
    // Initial server metrics load for the selected reporting window.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void load(period);
  }, [load, period]);

  async function saveConfiguration(configuration: Dashboard["configuration"]) {
    setSaving(true); setError("");
    try {
      const response = await fetch("/api/admin/ai", { method: "POST", headers: { "Content-Type": "application/json", ...await authenticatedHeaders() }, body: JSON.stringify(configuration) });
      if (!response.ok) throw new Error("Не удалось сохранить настройки AI.");
      setDashboard((current) => ({ ...current, configuration }));
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Ошибка сохранения."); }
    finally { setSaving(false); }
  }

  const aiChartMax = useMemo(() => Math.max(1, ...dashboard.daily.map((item) => number(item.totalTokens))), [dashboard.daily]);
  const activityChartMax = useMemo(() => Math.max(1, ...dashboard.product.momentTrend.map((item) => number(item.count))), [dashboard.product.momentTrend]);
  const product = dashboard.product;
  const p = product.summary;
  const periodLabels: Record<Period, string> = { today: "Сегодня", week: "7 дней", month: "30 дней", year: "Год" };

  if (!accessResolved) return <main className="admin-auth-gate" aria-busy="true" aria-label="Проверяем доступ к админ-панели"><div className="admin-gate-orbit"><span>C</span><i /></div><small>CHRONICLE CONTROL ROOM</small><h1>Проверяем доступ…</h1><p>Панель откроется только для владельца Chronicle.</p></main>;

  return <main className="admin-shell">
    <header><Link href="/app" className="admin-wordmark"><span /><b>chronicle</b><small>CONTROL ROOM</small></Link><div><span>{loading ? "Обновляем данные…" : `Период: ${periodLabels[period]}`}</span><Link href="/app">В приложение →</Link></div></header>
    <section className="admin-heading"><div><small>PRODUCT OPERATIONS</small><h1>Пульс Chronicle</h1><p>Пользователи, моменты, удержание и расход AI в одном месте.</p></div><button onClick={() => void load(period)} disabled={loading}>{loading ? "Обновляем…" : "Обновить"}</button></section>
    <nav className="admin-periods" aria-label="Период статистики">{(Object.keys(periodLabels) as Period[]).map((item) => <button key={item} className={period === item ? "active" : ""} onClick={() => setPeriod(item)}>{periodLabels[item]}</button>)}</nav>
    {error && <p className="admin-error admin-banner">{error}</p>}

    <section className="admin-metrics admin-product-metrics">
      <article><small>ПОЛЬЗОВАТЕЛИ</small><strong>{formatNumber(p.totalUsers)}</strong><span>+{formatNumber(p.newUsers)} за период</span></article>
      <article><small>АКТИВНЫЕ</small><strong>{formatNumber(p.activeUsers)}</strong><span>{formatNumber(p.usersWithoutMoments)} ещё без моментов</span></article>
      <article><small>МОМЕНТЫ</small><strong>{formatNumber(p.periodMoments)}</strong><span>{formatNumber(p.totalMoments)} за всё время</span></article>
      <article><small>СРЕДНЕЕ НА АКТИВНОГО</small><strong>{number(p.activeUsers) ? (number(p.periodMoments) / number(p.activeUsers)).toFixed(1) : "0"}</strong><span>{formatNumber(p.periodGoals)} новых целей</span></article>
      <article><small>НАПОМИНАНИЯ</small><strong>{formatNumber(p.usersWithReminders)}</strong><span>пользователей включили</span></article>
    </section>

    <section className="admin-product-grid">
      <article className="admin-chart-card"><div className="admin-card-title"><div><small>ACTIVITY</small><h2>Моменты за 7 дней</h2></div></div><div className="admin-chart admin-product-chart">{product.momentTrend.length ? product.momentTrend.map((item) => <div key={String(item.day)}><i style={{ height: `${Math.max(5, number(item.count) / activityChartMax * 100)}%` }} /><small>{String(item.day).slice(5)}</small><b>{formatNumber(item.count)}</b></div>) : <p>Моментов пока нет.</p>}</div></article>
      <article className="admin-breakdown-card"><div className="admin-card-title"><div><small>LIFE AREAS</small><h2>Популярные сферы</h2></div></div><div className="admin-breakdown">{product.areas.slice(0, 6).map((item) => <div key={String(item.category)}><span>{String(item.category)}</span><i><b style={{ width: `${percent(item.count, p.periodMoments)}%` }} /></i><strong>{formatNumber(item.count)}</strong></div>)}{!product.areas.length && <p>Данных за период пока нет.</p>}</div></article>
      <article className="admin-retention-card"><div className="admin-card-title"><div><small>RETENTION</small><h2>Возвращаемость</h2></div></div>{([1, 7, 30] as const).map((day) => <div key={day}><span>Day {day}</span><strong>{percent(product.retention[`day${day}Retained`], product.retention[`day${day}Eligible`])}%</strong><small>{formatNumber(product.retention[`day${day}Retained`])} / {formatNumber(product.retention[`day${day}Eligible`])}</small></div>)}</article>
      <article className="admin-retention-card"><div className="admin-card-title"><div><small>SILENCE</small><h2>Неактивные</h2></div></div>{([7, 14, 30] as const).map((day) => <div key={day}><span>Молчат {day} дней</span><strong>{formatNumber(product.churn[`silent${day}`])}</strong><small>пользователей</small></div>)}</article>
    </section>

    <section className="admin-section-divider"><small>AI OPERATIONS</small><h2>Модели и токены</h2></section>
    <section className="admin-metrics">
      <article><small>ВСЕГО ТОКЕНОВ</small><strong>{formatNumber(dashboard.summary.totalTokens)}</strong><span>{formatNumber(dashboard.summary.inputTokens)} вход · {formatNumber(dashboard.summary.outputTokens)} выход</span></article>
      <article><small>ЗАПРОСОВ</small><strong>{formatNumber(dashboard.summary.requests)}</strong><span>{formatNumber(dashboard.summary.successes)} успешно · {formatNumber(dashboard.summary.errors)} ошибок</span></article>
      <article><small>РАСЧЁТНАЯ СТОИМОСТЬ</small><strong>{money(dashboard.summary.estimatedCostUsd)}</strong><span>по тарифам моделей</span></article>
      <article><small>СРЕДНЯЯ ЗАДЕРЖКА</small><strong>{Math.round(number(dashboard.summary.averageLatencyMs))} мс</strong><span>от запроса до ответа</span></article>
    </section>

    <section className="admin-grid"><article className="admin-provider-card"><div className="admin-card-title"><div><small>ACTIVE ENGINE</small><h2>Провайдер и модель</h2></div><span className={saving ? "saving" : ""}>{saving ? "Сохраняем" : "Готово"}</span></div><div className="admin-provider-switch">{(["gemini", "grok"] as Provider[]).map((provider) => <button key={provider} className={dashboard.configuration.provider === provider ? "active" : ""} onClick={() => void saveConfiguration({ ...dashboard.configuration, provider })}><i/><b>{provider === "gemini" ? "Gemini" : "Grok"}</b><small>{dashboard.connected[provider] ? "API подключён" : "Нет API-ключа"}</small></button>)}</div><label>Модель Grok<input value={dashboard.configuration.grokModel} onChange={(event) => setDashboard((current) => ({ ...current, configuration: { ...current.configuration, grokModel: event.target.value } }))} onBlur={() => void saveConfiguration(dashboard.configuration)} /></label><label>Модель Gemini<input value={dashboard.configuration.geminiModel} onChange={(event) => setDashboard((current) => ({ ...current, configuration: { ...current.configuration, geminiModel: event.target.value } }))} onBlur={() => void saveConfiguration(dashboard.configuration)} /></label></article>
      <article className="admin-chart-card"><div className="admin-card-title"><div><small>14 DAY WINDOW</small><h2>Динамика токенов</h2></div></div><div className="admin-chart">{dashboard.daily.length ? dashboard.daily.map((item) => <div key={String(item.day)} title={`${item.day}: ${formatNumber(item.totalTokens)} токенов`}><i style={{ height: `${Math.max(5, number(item.totalTokens) / aiChartMax * 100)}%` }}/><small>{String(item.day).slice(5)}</small></div>) : <p>Данные появятся после первого AI-размышления.</p>}</div></article></section>

    <section className="admin-table-card"><div className="admin-card-title"><div><small>REQUEST LOG</small><h2>Последние AI-обращения</h2></div><span>Тексты записей не сохраняются</span></div><div className="admin-table"><table><thead><tr><th>Время</th><th>Провайдер</th><th>Модель</th><th>Функция</th><th>Вход</th><th>Выход</th><th>Всего</th><th>Стоимость</th><th>Статус</th></tr></thead><tbody>{dashboard.recent.map((item) => <tr key={String(item.id)}><td>{new Date(String(item.createdAt)).toLocaleString("ru-RU", { day:"2-digit", month:"short", hour:"2-digit", minute:"2-digit" })}</td><td><b>{String(item.provider)}</b></td><td>{String(item.model)}</td><td>{String(item.feature)}</td><td>{formatNumber(item.inputTokens)}</td><td>{formatNumber(item.outputTokens)}</td><td>{formatNumber(item.totalTokens)}</td><td>{money(item.estimatedCostUsd)}</td><td><span className={`admin-status ${item.status}`}>{item.status === "success" ? "успешно" : "ошибка"}</span></td></tr>)}{!dashboard.recent.length && <tr><td colSpan={9}>Запросов пока не было.</td></tr>}</tbody></table></div></section>
  </main>;
}
