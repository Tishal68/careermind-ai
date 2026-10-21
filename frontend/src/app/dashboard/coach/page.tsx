"use client";

import { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { useAccountResource } from '@/hooks/useAccountResource';
import { fetchApi } from '@/lib/api';
import { Bot, Send, Trash2 } from 'lucide-react';

export default function CareerCoachPage() {
  const reports = useAccountResource<any>('/analysis/report-summaries?limit=20');
  const [selected, setSelected] = useState('');
  const [listError, setListError] = useState('');
  const [moreBusy, setMoreBusy] = useState(false);
  useEffect(() => { const id = new URLSearchParams(window.location.search).get('report'); if (id && /^\d+$/.test(id) && Number(id)>0) setSelected(id); }, []);
  useEffect(() => { if (reports.data?.items.length) setSelected(value => value || String(reports.data.items[0].id)); }, [reports.data]);
  async function more() {
    setMoreBusy(true); setListError('');
    try { const page = await fetchApi<any>(`/analysis/report-summaries?limit=20&before=${reports.data.next_before}`); reports.update(previous => ({items:[...previous.items,...page.items],next_before:page.next_before})); }
    catch (err: any) { setListError(err.message); } finally { setMoreBusy(false); }
  }
  return <>
    <div className="max-w-6xl mx-auto px-4 sm:px-8 pt-8 space-y-3">
      <label htmlFor="coach-report" className="block font-semibold">Choose the report for this conversation</label>
      <select id="coach-report" value={selected} onChange={e => { setSelected(e.target.value); window.history.replaceState(null, "", `/dashboard/coach?report=${e.target.value}`); }} className="w-full rounded-xl bg-slate-900 border border-slate-700 p-3">
        <option value="" disabled>Select a report</option>
        {selected && !reports.data?.items.some((item: any) => String(item.id)===selected) && <option value={selected}>Selected report #{selected}</option>}
        {reports.data?.items.map((item: any) => <option key={item.id} value={item.id}>#{item.id} · {item.job_role} · {new Date(item.created_at).toLocaleDateString()}</option>)}
      </select>
      {reports.loading && <p role="status">Loading reports…</p>}
      {reports.error && <p role="alert">Could not load reports. <button onClick={reports.reload} className="underline">Retry reports</button></p>}
      {listError && <p role="alert">{listError}</p>}
      {reports.data?.next_before && <button disabled={moreBusy} onClick={more} className="text-emerald-300 underline">Load older reports</button>}
      {reports.data?.items.length===0 && !selected && <Link href="/dashboard" className="underline">Analyze a resume to start coaching</Link>}
    </div>
    {selected && <CoachConversation key={selected} reportId={Number(selected)} />}
  </>;
}

function CoachConversation({reportId}: {reportId: number}) {
  const [attempt, setAttempt] = useState(0);
  const [before, setBefore] = useState<number | null>(null);
  const [messages, setMessages] = useState<any[]>([]);
  const [context, setContext] = useState<any>(null);
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const bottom = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true); setError('');
    Promise.all([fetchApi<any>(`/chat/history?report_id=${reportId}`, {signal:controller.signal}), fetchApi<any>(`/chat/context?report_id=${reportId}`, {signal:controller.signal})])
      .then(([history, ctx]) => { setMessages(history.messages); setBefore(history.next_before); setContext(ctx); })
      .catch(err => { if (!controller.signal.aborted) setError(err.message); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [reportId, attempt]);
  useEffect(() => { bottom.current?.scrollIntoView({ behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth', block: 'nearest' }); }, [messages, busy]);

  async function send(text = input) {
    const query = text.trim();
    if (!query || busy || !context) return;
    setBusy(true); setError('');
    try {
      const reply = await fetchApi<any>('/chat/message', { method: 'POST', body: JSON.stringify({content: query, report_id: reportId}) });
      setMessages(prev => [...prev, {role: 'user', content: query}, reply]);
      setInput('');
    } catch (err: any) { setError(err.message || 'The coach could not reply. Please try again.'); }
    finally { setBusy(false); }
  }
  async function older() {
    if (!before || busy) return;
    setBusy(true); setError('');
    try { const page = await fetchApi<any>(`/chat/history?report_id=${reportId}&before=${before}`); setMessages(prev => [...page.messages, ...prev]); setBefore(page.next_before); }
    catch (err: any) { setError(err.message); }
    finally { setBusy(false); }
  }
  async function clear() {
    setBusy(true); setError('');
    try { await fetchApi(`/chat/clear?report_id=${reportId}`, {method: 'DELETE'}); setMessages([]); setBefore(null); }
    catch (err: any) { setError(err.message); }
    finally { setBusy(false); }
  }

  return <div className="max-w-6xl mx-auto px-4 sm:px-8 py-10 space-y-6">
    <header><p className="text-xs uppercase tracking-widest text-emerald-400 font-bold">Powered by Ollama</p><h1 className="text-3xl font-bold text-white mt-3">Your career coach</h1><p className="text-slate-400 mt-2">Focused help with your resume, role fit, learning plan, projects, and interviews.</p></header>
    <div className="grid lg:grid-cols-[1fr_280px] gap-6 items-start">
      <section className="rounded-2xl border border-white/10 bg-slate-900/50 overflow-hidden">
        <div className="flex items-center justify-between p-4 border-b border-white/10"><span className="flex items-center gap-2 text-sm"><Bot className="w-5 h-5 text-emerald-400" />Career conversation</span><button aria-label="Clear conversation" onClick={clear} disabled={busy || !messages.length} className="p-2 text-slate-400 hover:text-white disabled:opacity-30"><Trash2 className="w-4 h-4" /></button></div>
        <div className="h-[460px] overflow-y-auto p-4 sm:p-6 space-y-5" aria-live="polite" aria-busy={busy}>
          {before && <button onClick={older} disabled={busy} className="text-sm text-emerald-300 underline">Load older messages</button>}
          {!messages.length && <div className="text-slate-300 text-sm leading-relaxed p-4 rounded-xl bg-slate-800/50">{loading ? 'Loading your conversation…' : error ? 'Your conversation could not be loaded. Retry below.' : context ? `Your ${context.job_role} analysis is ready. Ask me which skill to learn first, how to build a relevant project, or how to improve your resume.` : 'Start by analyzing a resume and selecting a role. Your coach will use that result to give you relevant guidance.'}</div>}
          {messages.map((message, index) => <div key={message.id || index} className={`rounded-xl p-4 text-sm max-w-[92%] ${message.role === 'user' ? 'ml-auto bg-emerald-900/50 border border-emerald-500/20' : 'bg-slate-800/60'}`}><p className="text-xs font-bold text-emerald-400 mb-2">{message.role === 'user' ? 'You' : 'Career coach'}</p><p className="whitespace-pre-wrap leading-relaxed break-words">{message.content}</p></div>)}
          {busy && <p className="text-emerald-400 text-sm">Working on your request…</p>}<div ref={bottom} />
        </div>
        <div className="border-t border-white/10 p-4 space-y-3">
          {error && <p role="alert" className="text-rose-300 text-sm">{error} {!context && <button onClick={() => setAttempt(value => value+1)} className="underline">Retry conversation</button>}</p>}
          {context && <div className="flex flex-wrap gap-2">{[context.research ? 'Which opening fits me best, and why?' : 'What should I learn first?', 'Suggest a portfolio project', 'Help me improve my resume'].map(question => <button key={question} disabled={busy} onClick={() => send(question)} className="text-xs rounded-lg border border-white/10 px-3 py-2 text-slate-300 hover:border-emerald-500/50 disabled:opacity-40">{question}</button>)}</div>}
          <form onSubmit={e => {e.preventDefault(); send();}} className="flex gap-2">
            <label htmlFor="career-question" className="sr-only">Career question</label>
            <textarea id="career-question" rows={2} maxLength={2000} value={input} disabled={busy || !context} onChange={e => setInput(e.target.value)} placeholder="Ask about your next career step…" className="flex-1 min-w-0 bg-slate-950 border border-slate-700 rounded-xl p-3 text-sm text-white focus:outline-none focus:border-emerald-500 disabled:opacity-40" />
            <button aria-label="Send message" type="submit" disabled={busy || !context || !input.trim()} className="rounded-xl bg-emerald-600 p-4 disabled:opacity-30 hover:bg-emerald-500"><Send className="w-5 h-5" /></button>
          </form>
        </div>
      </section>
      <aside className="rounded-2xl border border-white/10 p-5 space-y-5">
        <h2 className="font-bold text-white">Your coaching context</h2>
        {context ? <><p className="text-lg font-semibold text-emerald-300">{context.job_role}</p><p className="text-xs text-slate-400 break-words">{context.file_name}</p><div><p className="text-3xl font-bold">{context.match_percent ?? '—'}{context.match_percent != null ? '%' : ''}</p><p className="text-xs text-slate-400 mt-1">{context.research ? (context.match_percent == null ? 'See coverage for each opening in your report' : 'Company requirement coverage') : 'Core skills found in your resume'}</p></div><div><h3 className="text-sm font-semibold mb-2">Skills to develop</h3><ul className="space-y-2 text-sm text-slate-400">{context.missing_skills.length ? context.missing_skills.map((skill: string) => <li key={skill}>{skill}</li>) : <li>No skill gaps are listed in this report. Review its evidence and limitations before drawing conclusions.</li>}</ul></div></> : <p className="text-sm text-slate-400">No resume analysis yet.</p>}
        {context?.research && <div className="space-y-2 text-xs text-slate-400"><p>Research from {new Date(context.research.researched_at).toLocaleDateString()} · {context.research.sample_size} comparable postings.</p><p>Scores for individual openings and their evidence are in your report. Refresh research on the role-match page for new openings.</p>{[...(context.research.company_match ? [context.research.company_match] : []), ...context.research.best_fit_openings.slice(0, 3)].map((job: any, i: number) => job.url?.startsWith('https://') && <a key={i} href={job.url} target="_blank" rel="noopener noreferrer" className="block text-emerald-300 underline">{job.title}</a>)}</div>}
        <Link href="/dashboard" className="block text-sm text-emerald-400 underline">{context ? 'Analyze another role or resume' : 'Start your resume analysis'}</Link>
        <p className="text-xs text-slate-500">Each analysis has its own conversation. AI suggestions should be checked against your experience and goals.</p>
      </aside>
    </div>
  </div>;
}
