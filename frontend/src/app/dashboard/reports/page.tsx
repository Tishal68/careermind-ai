'use client';
import { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { fetchApi } from '@/lib/api';
import { GapBreakdown } from '@/components/FeatureComponents';

export default function ReportsPage() {
  const [items, setItems] = useState<any[]>([]);
  const [before, setBefore] = useState<number | null>(null);
  const [report, setReport] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [listLoading, setListLoading] = useState(true);
  const [listError, setListError] = useState('');
  const [selected, setSelected] = useState<number | null>(null);
  const listing = useRef<AbortController | null>(null);
  const [error, setError] = useState('');
  const active = useRef<AbortController | null>(null);
  async function select(id: number) {
    active.current?.abort(); const controller = new AbortController(); active.current = controller;
    setSelected(id); setReport(null); setLoading(true); setError('');
    try { const data = await fetchApi(`/analysis/reports/${id}`, {signal: controller.signal}); if (!controller.signal.aborted) setReport(data); }
    catch (err: any) { if (!controller.signal.aborted) setError(err.message); }
    finally { if (!controller.signal.aborted) setLoading(false); }
  }
  async function load(cursor?: number) {
    listing.current?.abort(); const controller = new AbortController(); listing.current = controller;
    setListLoading(true); setListError('');
    try {
      const page = await fetchApi<any>(`/analysis/report-summaries?limit=20${cursor ? `&before=${cursor}` : ''}`, {signal: controller.signal});
      if (controller.signal.aborted) return;
      setItems(previous => cursor ? [...previous, ...page.items] : page.items); setBefore(page.next_before);
      if (!cursor && page.items.length) await select(page.items[0].id);
    } catch (err: any) { if (!controller.signal.aborted) setListError(err.message); }
    finally { if (!controller.signal.aborted) setListLoading(false); }
  }
  useEffect(() => { load(); return () => { active.current?.abort(); listing.current?.abort(); }; }, []);
  return <div className="max-w-6xl mx-auto p-4 sm:p-8 space-y-6">
    <header><h1 className="text-3xl font-bold">Your role reports</h1><p className="text-slate-400 mt-2">Review the evidence for each role. ATS, resume quality and hiring readiness are not assessed.</p></header>
    {listError && <p role="alert" className="text-rose-300">{listError} <button onClick={() => load(before || undefined)} className="underline">Retry report list</button></p>}
    {error && <p role="alert" className="text-rose-300">{error} <button onClick={() => selected && select(selected)} className="underline">Retry report</button></p>}
    <div className="grid lg:grid-cols-[260px_1fr] gap-6">
      <nav aria-label="Saved reports" className="space-y-3 print:hidden">{items.map(item => <button key={item.id} onClick={() => select(item.id)} aria-current={selected === item.id ? 'true' : undefined} className={`block text-left w-full p-4 rounded-xl border ${selected === item.id ? 'border-emerald-400 bg-emerald-900/20' : 'border-white/10'}`}><span className="block font-semibold">{item.job_role}</span><span className="text-xs text-slate-400">{item.experience_level} · {new Date(item.created_at).toLocaleDateString()}</span></button>)}{before && <button disabled={listLoading} onClick={() => load(before)} className="underline text-emerald-300">Load older reports</button>}</nav>
      <section className="min-w-0" aria-live="polite" aria-busy={loading}>{loading || (listLoading && !report) ? <p role="status">Loading report…</p> : report ? <><button onClick={() => window.print()} className="mb-4 underline text-emerald-300 print:hidden">Print report</button><Link href={`/dashboard/roadmap?report=${report.id}`} className="inline-block ml-4 mb-4 underline text-emerald-300 print:hidden">Open action plan</Link><GapBreakdown report={report} /></> : error || listError ? <p>Saved reports are temporarily unavailable. Use Retry to reconnect.</p> : <p>No reports yet. <Link href="/dashboard" className="underline text-emerald-300">Research a role</Link> to create one.</p>}</section>
    </div>
  </div>;
}
