"use client";

import { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { fetchApi } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';

type Task = { id: string; task_name: string; is_completed: boolean };
type Plan = { report_id: number; job_role: string; experience_level: string; created: boolean; revision: number; note: string;
  milestones: { title: string; focus_topic: string; tasks: Task[] }[];
  projects: { id: string; title: string; description: string; required_skills: string[] }[] };
type Summary = { id: number; job_role: string; experience_level: string; created_at: string };

export default function ActionPlanWorkspace() {
  const { user } = useAuth();
  const [reports, setReports] = useState<Summary[]>([]);
  const [before, setBefore] = useState<number | null>(null);
  const [selected, setSelected] = useState<number | null>(null);
  const [plan, setPlan] = useState<Plan | null>(null);
  const [loading, setLoading] = useState(true);
  const [listBusy, setListBusy] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [listError, setListError] = useState('');
  const [notice, setNotice] = useState('');
  const active = useRef<AbortController | null>(null);
  const listRequest = useRef<AbortController | null>(null);

  async function select(id: number) {
    active.current?.abort(); const controller = new AbortController(); active.current = controller;
    setSelected(id); setPlan(null); setError(''); setNotice(''); setSaving(false); setLoading(true);
    const url = new URL(window.location.href); url.searchParams.set('report', String(id)); window.history.replaceState(null, '', url);
    try { const result = await fetchApi<Plan>(`/analysis/reports/${id}/action-plan`, { signal: controller.signal }); if (!controller.signal.aborted) setPlan(result); }
    catch (err: any) { if (!controller.signal.aborted) setError(err.message); }
    finally { if (!controller.signal.aborted) setLoading(false); }
  }

  async function loadReports(cursor?: number) {
    listRequest.current?.abort(); const controller = new AbortController(); listRequest.current = controller;
    setListBusy(true); setListError('');
    try {
      const page = await fetchApi<{items: Summary[]; next_before: number | null}>(`/analysis/report-summaries?limit=20${cursor ? `&before=${cursor}` : ''}`, {signal: controller.signal});
      if (controller.signal.aborted) return;
      setReports(items => cursor ? [...items, ...page.items] : page.items); setBefore(page.next_before);
      if (!cursor) {
        const query = new URL(window.location.href).searchParams.get('report');
        const requested = query === null ? null : Number(query);
        if (requested !== null && (!Number.isSafeInteger(requested) || requested <= 0)) { setError('Choose a valid saved report.'); setLoading(false); }
        else if (requested || page.items.length) await select(requested || page.items[0].id);
        else setLoading(false);
      }
    } catch (err: any) { if (!controller.signal.aborted) { setListError(err.message); setLoading(false); } }
    finally { if (!controller.signal.aborted) setListBusy(false); }
  }

  useEffect(() => {
    setReports([]); setPlan(null); setSelected(null); setLoading(true); loadReports();
    return () => { active.current?.abort(); listRequest.current?.abort(); };
  }, [user?.id]);

  async function save(task?: Task) {
    if (!plan || saving) return;
    const current = plan;
    active.current?.abort(); const controller = new AbortController(); active.current = controller;
    setSaving(true); setError(''); setNotice('');
    try {
      const result = await fetchApi<Plan>(`/analysis/reports/${current.report_id}/action-plan${task ? `/tasks/${encodeURIComponent(task.id)}` : ''}`, {
        method: task ? 'PATCH' : 'POST', signal: controller.signal,
        ...(task ? {body: JSON.stringify({revision: current.revision, is_completed: !task.is_completed})} : {}),
      });
      if (!controller.signal.aborted) { setPlan(result); setNotice(task ? 'Progress saved.' : 'Your action plan is saved.'); }
    } catch (err: any) { if (!controller.signal.aborted) setError(err.message); }
    finally { if (!controller.signal.aborted) setSaving(false); }
  }

  const tasks = plan?.milestones.flatMap(m => m.tasks) || [];
  const completed = tasks.filter(t => t.is_completed).length;
  return <div className="max-w-6xl mx-auto p-4 sm:p-8 space-y-6">
    <header><p className="text-sm text-emerald-300 mb-2">From evidence to action</p><h1 className="text-3xl font-bold">Your action plan</h1><p className="text-slate-400 mt-2">Choose a saved report, work through its priorities, and record your progress.</p></header>
    {listError && <p role="alert" className="text-rose-300">{listError} <button className="underline" onClick={() => loadReports(before || undefined)}>Retry report list</button></p>}
    <div className="grid lg:grid-cols-[250px_1fr] gap-6">
      <nav aria-label="Choose a report" className="space-y-3">
        {reports.map(item => <button key={item.id} onClick={() => select(item.id)} aria-current={selected === item.id ? 'true' : undefined} className={`block text-left w-full p-4 rounded-xl border ${selected === item.id ? 'border-emerald-400 bg-emerald-900/20' : 'border-white/10'}`}><span className="block font-semibold">{item.job_role}</span><span className="text-xs text-slate-400">{item.experience_level} · {new Date(item.created_at).toLocaleDateString()}</span></button>)}
        {before && <button disabled={listBusy} onClick={() => loadReports(before)} className="underline text-emerald-300">Load older reports</button>}
        {listBusy && <p role="status">Loading reports…</p>}
      </nav>
      <section className="min-w-0 space-y-6" aria-busy={loading || saving}>
        {error && <div role="alert" className="rounded-xl border border-rose-400/30 p-4 text-rose-200">{error} {selected && <button className="underline" onClick={() => select(selected)}>Reload plan</button>}</div>}
        {notice && <p role="status" className="text-emerald-300">{notice}</p>}
        {loading ? <p role="status">Loading your plan…</p> : plan ? <>
          <div><h2 className="text-xl font-semibold break-words">{plan.job_role}</h2><p className="text-sm text-slate-400 mt-2">{plan.experience_level} · Report #{plan.report_id}</p><p className="text-sm text-slate-400 mt-3">{plan.note}</p></div>
          {!plan.created ? <button disabled={saving} onClick={() => save()} className="rounded-xl bg-emerald-600 px-5 py-3 font-semibold disabled:opacity-50">{saving ? 'Creating plan…' : 'Create action plan'}</button> : <>
            {tasks.length > 0 ? <p className="text-sm">{completed} of {tasks.length} actions completed{saving ? ' · Saving…' : ''}</p> : <p className="rounded-xl border border-white/10 p-5">This report has no supported action priorities. It may have no gaps or too little market evidence. Compare a specific job description to get a more focused plan.</p>}
            {plan.milestones.map((milestone, index) => <fieldset key={index} disabled={saving} className="rounded-2xl border border-white/10 p-5 space-y-4"><legend className="px-2 font-semibold break-words">{index + 1}. {milestone.title}</legend>{milestone.tasks.map(task => <label key={task.id} className="flex items-start gap-3 cursor-pointer text-sm leading-relaxed"><input type="checkbox" checked={task.is_completed} onChange={() => save(task)} className="mt-1 h-5 w-5 shrink-0 accent-emerald-500" /><span className={task.is_completed ? 'text-slate-400 line-through' : ''}>{task.task_name}</span></label>)}</fieldset>)}
            {plan.projects.length > 0 && <section className="space-y-4"><h2 className="text-xl font-semibold">Practice projects</h2><p className="text-sm text-slate-400">Suggested exercises based on skill evidence gaps in this report. Adapt the scope to your current level and available time.</p>{plan.projects.map(project => <article key={project.id} className="border-l-2 border-emerald-500 pl-4 py-2"><h3 className="font-semibold">{project.title}</h3><p className="text-sm text-slate-400 mt-2">{project.description}</p></article>)}</section>}
          </>}
          <Link href="/dashboard/coach" className="inline-block text-emerald-300 underline">Open career coach</Link><p className="text-xs text-slate-400">The coach uses your latest report; check its context before discussing an older plan.</p>
        </> : !error && !listError && !listBusy ? <p>No reports yet. <Link href="/dashboard" className="underline text-emerald-300">Compare your resume with a role</Link> first.</p> : null}
      </section>
    </div>
  </div>;
}
