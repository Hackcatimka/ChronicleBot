"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { authenticatedHeaders } from "@/lib/supabase-client";
import "./journal.css";

type Moment = { id:number; title:string; content:string; category:string; mood:string; isFavorite:boolean; createdAt:string };
type Goal = { id:number; title:string; description:string; category:string; completedSteps:number; targetSteps:number; status:string };
type JournalData = { moments:Moment[]; goals:Goal[]; settings:{ displayName:string; language:"ru"|"en" } };

export default function JournalPage() {
  const [data, setData] = useState<JournalData | null>(null); const [error, setError] = useState("");
  useEffect(() => { const load = async () => { const response = await fetch("/api/chronicle", { headers: await authenticatedHeaders(), cache:"no-store" }); if (response.status === 401) { window.location.assign(`/auth?returnTo=${encodeURIComponent("/journal")}`); return; } if (!response.ok) { setError("Не удалось подготовить дневник."); return; } setData(await response.json() as JournalData); }; void load(); }, []);
  const areas = useMemo(() => { const map = new Map<string,number>(); for (const moment of data?.moments || []) map.set(moment.category,(map.get(moment.category)||0)+1); return [...map.entries()].sort((a,b)=>b[1]-a[1]); }, [data]);
  const maxArea = Math.max(1,...areas.map(([,count])=>count));
  if (!data) return <main className="journal-loading"><div>C</div><h1>{error || "Собираем ваш дневник…"}</h1>{error && <Link href="/app">Вернуться в Chronicle</Link>}</main>;
  const locale = data.settings.language === "ru" ? "ru-RU" : "en-US";
  return <main className="journal-shell"><div className="journal-toolbar"><Link href="/app">← Chronicle</Link><span>В режиме печати панели не будет</span><button onClick={() => window.print()}>Сохранить как PDF</button></div><article className="journal-book">
    <section className="journal-cover"><div className="journal-brand"><span>C</span><strong>chronicle</strong></div><div><small>PERSONAL JOURNAL</small><h1>{data.settings.displayName}</h1><p>Моменты, цели и направления, из которых складывается ваша история.</p></div><footer><span>{new Date().toLocaleDateString(locale,{month:"long",year:"numeric"})}</span><b>{data.moments.length} моментов</b></footer></section>
    <section className="journal-overview"><header><small>YOUR STORY IN NUMBERS</small><h2>Карта этого периода</h2></header><div className="journal-summary"><article><strong>{data.moments.length}</strong><span>сохранено моментов</span></article><article><strong>{data.moments.filter((m)=>m.isFavorite).length}</strong><span>особенно важных</span></article><article><strong>{data.goals.filter((g)=>g.status==="completed").length}</strong><span>завершено целей</span></article></div><div className="journal-areas">{areas.map(([area,count])=><div key={area}><span>{area}</span><i><b style={{width:`${count/maxArea*100}%`}}/></i><strong>{count}</strong></div>)}{!areas.length&&<p>Первое направление появится после сохранения момента.</p>}</div></section>
    {data.moments.map((moment,index)=><section className="journal-entry" key={moment.id}><aside><strong>{String(index+1).padStart(2,"0")}</strong><span>{new Date(moment.createdAt).toLocaleDateString(locale,{day:"numeric",month:"long",year:"numeric"})}</span></aside><article><small>{moment.category} · {moment.mood}</small><h2>{moment.title}</h2><p>{moment.content}</p>{moment.isFavorite&&<blockquote>✦ Сохранено в избранном</blockquote>}</article></section>)}
    <section className="journal-goals"><header><small>INTENTIONAL PROGRESS</small><h2>Цели</h2></header>{data.goals.map((goal)=><article key={goal.id}><div><small>{goal.category} · {goal.status}</small><h3>{goal.title}</h3><p>{goal.description}</p></div><strong>{Math.round(goal.completedSteps/Math.max(1,goal.targetSteps)*100)}%</strong></article>)}{!data.goals.length&&<p>Цели появятся здесь, когда вы зададите первое направление.</p>}</section>
    <footer className="journal-end"><div className="journal-brand"><span>C</span><strong>chronicle</strong></div><p>Keep the moments. Notice who you become.</p></footer>
  </article></main>;
}
