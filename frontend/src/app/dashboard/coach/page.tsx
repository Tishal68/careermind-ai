"use client";

import { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { fetchApi } from '@/lib/api';
import { Bot, Send, Trash2 } from 'lucide-react';

export default function CareerCoachPage() {
  const [messages, setMessages] = useState<any[]>([]);
  const [context, setContext] = useState<any>(null);
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const bottom = useRef<HTMLDivElement>(null);

  useEffect(() => {
    Promise.all([fetchApi<any>('/chat/history'), fetchApi<any>('/chat/context')])
      .then(([history, ctx]) => { setMessages(history.messages); setContext(ctx); })
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, []);
  useEffect(() => { bottom.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' }); }, [messages, busy]);

  async function send(text = input) {
    const query = text.trim();
    if (!query || busy || !context) return;
    setBusy(true); setError('');
    try {
      const reply = await fetchApi<any>('/chat/message', { method: 'POST', body: JSON.stringify({content: query}) });
      setMessages(prev => [...prev, {role: 'user', content: query}, reply]);
      setInput('');
    } catch (err: any) { setError(err.message || 'The coach could not reply. Please try again.'); }
    finally { setBusy(false); }
  }
  async function clear() {
    setBusy(true); setError('');
    try { await fetchApi('/chat/clear', {method: 'DELETE'}); setMessages([]); }
    catch (err: any) { setError(err.message); }
    finally { setBusy(false); }
  }

  return <div className="max-w-6xl mx-auto px-4 sm:px-8 py-10 space-y-6">
    <header><p className="text-xs uppercase tracking-widest text-emerald-400 font-bold">Powered by Ollama</p><h1 className="text-3xl font-bold text-white mt-3">Your career coach</h1><p className="text-slate-400 mt-2">Focused help with your resume, role fit, learning plan, projects, and interviews.</p></header>
    <div className="grid lg:grid-cols-[1fr_280px] gap-6 items-start">
      <section className="rounded-2xl border border-white/10 bg-slate-900/50 overflow-hidden">
        <div className="flex items-center justify-between p-4 border-b border-white/10"><span className="flex items-center gap-2 text-sm"><Bot className="w-5 h-5 text-emerald-400" />Career conversation</span><button aria-label="Clear conversation" onClick={clear} disabled={busy || !messages.length} className="p-2 text-slate-400 hover:text-white disabled:opacity-30"><Trash2 className="w-4 h-4" /></button></div>
        <div className="h-[460px] overflow-y-auto p-4 sm:p-6 space-y-5" aria-live="polite" aria-busy={busy}>
          {!messages.length && <div className="text-slate-300 text-sm leading-relaxed p-4 rounded-xl bg-slate-800/50">{loading ? 'Loading your conversation…' : context ? `Your ${context.job_role} analysis is ready. Ask me which skill to learn first, how to build a relevant project, or how to improve your resume.` : 'Start by analyzing a resume and selecting a role. Your coach will use that result to give you relevant guidance.'}</div>}
          {messages.map((message, index) => <div key={message.id || index} className={`rounded-xl p-4 text-sm max-w-[92%] ${message.role === 'user' ? 'ml-auto bg-emerald-900/50 border border-emerald-500/20' : 'bg-slate-800/60'}`}><p className="text-xs font-bold text-emerald-400 mb-2">{message.role === 'user' ? 'You' : 'Career coach'}</p><p className="whitespace-pre-wrap leading-relaxed break-words">{message.content}</p></div>)}
          {busy && <p className="text-emerald-400 text-sm">Working on your request…</p>}<div ref={bottom} />
        </div>
        <div className="border-t border-white/10 p-4 space-y-3">
          {error && <p role="alert" className="text-rose-300 text-sm">{error}</p>}
          {context && <div className="flex flex-wrap gap-2">{['What should I learn first?', 'Suggest a portfolio project', 'Help me improve my resume'].map(question => <button key={question} disabled={busy} onClick={() => send(question)} className="text-xs rounded-lg border border-white/10 px-3 py-2 text-slate-300 hover:border-emerald-500/50 disabled:opacity-40">{question}</button>)}</div>}
          <form onSubmit={e => {e.preventDefault(); send();}} className="flex gap-2">
            <label htmlFor="career-question" className="sr-only">Career question</label>
            <textarea id="career-question" rows={2} maxLength={2000} value={input} disabled={busy || !context} onChange={e => setInput(e.target.value)} placeholder="Ask about your next career step…" className="flex-1 min-w-0 bg-slate-950 border border-slate-700 rounded-xl p-3 text-sm text-white focus:outline-none focus:border-emerald-500 disabled:opacity-40" />
            <button aria-label="Send message" type="submit" disabled={busy || !context || !input.trim()} className="rounded-xl bg-emerald-600 p-4 disabled:opacity-30 hover:bg-emerald-500"><Send className="w-5 h-5" /></button>
          </form>
        </div>
      </section>
      <aside className="rounded-2xl border border-white/10 p-5 space-y-5">
        <h2 className="font-bold text-white">Your coaching context</h2>
        {context ? <><p className="text-lg font-semibold text-emerald-300">{context.job_role}</p><p className="text-xs text-slate-400 break-words">{context.file_name}</p><div><p className="text-3xl font-bold">{context.match_percent ?? '—'}{context.match_percent != null ? '%' : ''}</p><p className="text-xs text-slate-400 mt-1">Core skills found in your resume</p></div><div><h3 className="text-sm font-semibold mb-2">Skills to develop</h3><ul className="space-y-2 text-sm text-slate-400">{context.missing_skills.length ? context.missing_skills.map((skill: string) => <li key={skill}>{skill}</li>) : <li>All listed core skills were found. Focus on demonstrating depth and experience.</li>}</ul></div></> : <p className="text-sm text-slate-400">No resume analysis yet.</p>}
        <Link href="/dashboard" className="block text-sm text-emerald-400 underline">{context ? 'Analyze another role or resume' : 'Start your resume analysis'}</Link>
        <p className="text-xs text-slate-500">Each analysis has its own conversation. AI suggestions should be checked against your experience and goals.</p>
      </aside>
    </div>
  </div>;
}
