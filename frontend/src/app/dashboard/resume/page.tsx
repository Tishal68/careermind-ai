'use client';

import React, { useState, useEffect } from 'react';
import { useAccountResource } from '@/hooks/useAccountResource';
import { Card } from '@/components/UIComponents';
import { Uploader, ParsedPreview } from '@/components/FeatureComponents';
import { fetchApi } from '@/lib/api';
import Link from 'next/link';
import { FileCheck, Sparkles } from 'lucide-react';

export default function ResumePage() {
  const saved = useAccountResource<any[]>('/resume/my-resumes');
  const resumes = saved.data || [];
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const parsedResume = resumes.find(file => file.id === selectedId) || resumes[0] || null;
  const [error, setError] = useState('');
  const [deleting, setDeleting] = useState<number | null>(null);
  async function remove(id: number) {
    if (!window.confirm('Delete this resume and its associated reports and conversations?')) return;
    setDeleting(id); setError('');
    try {
      await fetchApi(`/resume/session/${id}`, { method: 'DELETE' });
      saved.update(files => (files || []).filter(file => file.id !== id));
      if (selectedId === id) setSelectedId(null);
    } catch (err: any) { setError(err.message); }
    finally { setDeleting(null); }
  }
  return (
    <div className="max-w-6xl mx-auto px-6 py-10 space-y-8">
      <div>
        <h1 className="text-3xl font-extrabold text-white flex items-center gap-3"><FileCheck className="w-8 h-8 text-indigo-400" />My resumes</h1>
        <p className="text-slate-400 text-sm mt-1">Upload a PDF or DOCX to extract recognized skills. Return to Role match to compare them with a job role.</p>
      </div>
      {error && <p role="alert" className="text-rose-300">{error}</p>}
      {saved.error && <p role="alert" className="text-rose-300">Could not refresh saved resumes. {saved.data ? 'Your last loaded resumes are still shown.' : 'Your saved resumes are unavailable right now.'} <button onClick={saved.reload} className="underline">Retry saved resumes</button></p>}
      <button onClick={saved.reload} disabled={saved.loading} className="text-sm underline text-emerald-300 disabled:opacity-50">Refresh saved resumes</button>
      {saved.loading && <p role="status">Loading saved resumes…</p>}
      {!!resumes.length && <section aria-label="Saved resumes" className="space-y-2">
        {resumes.map(file => <div key={file.id} className="flex items-center gap-3 rounded-xl border border-white/10 p-3">
          <button onClick={() => setSelectedId(file.id)} className="text-left flex-1 min-w-0 break-all text-emerald-300">{file.file_name}</button>
          <button disabled={deleting !== null} onClick={() => remove(file.id)} aria-label={`Delete ${file.file_name}`} className="text-sm text-rose-300 disabled:opacity-40">{deleting === file.id ? 'Deleting…' : 'Delete'}</button>
        </div>)}
        <Link href="/dashboard" className="inline-block text-sm text-emerald-300 underline">Compare a saved resume with a role</Link>
      </section>}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-1">
          <Card glass className="sticky top-24"><h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2"><Sparkles className="w-5 h-5 text-indigo-400" />Upload Resume</h2><Uploader onSuccess={(data) => { setSelectedId(data.id); saved.update(files => [data, ...(files || [])]); setError(''); }} /></Card>
        </div>
        <div className="lg:col-span-2">
          {parsedResume ? <ParsedPreview data={parsedResume} /> : saved.loading || saved.error ? <Card glass><p>{saved.loading ? "Loading your resume preview…" : "Resume preview is unavailable until saved resumes load. You can retry or upload a new document."}</p></Card> : <Card glass className="text-center py-16 border-dashed"><FileCheck className="w-12 h-12 text-slate-600 mx-auto mb-3" /><p className="text-slate-300 font-medium">No Resume Parsed Yet</p><p className="text-xs text-slate-500 max-w-sm mx-auto mt-1">Upload your PDF or DOCX file to preview recognized skills.</p></Card>}
        </div>
      </div>
    </div>
  );
}
