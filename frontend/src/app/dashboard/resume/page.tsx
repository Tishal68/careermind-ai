'use client';

import React, { useState } from 'react';
import { useAccountResource } from '@/hooks/useAccountResource';
import { Card } from '@/components/UIComponents';
import { Uploader, ParsedPreview } from '@/components/FeatureComponents';
import { fetchApi } from '@/lib/api';
import Link from 'next/link';
import { FileCheck, Sparkles } from 'lucide-react';

export default function ResumePage() {
  const saved = useAccountResource<any[]>('/resume/my-resumes');
  const resumes = saved.data || [];
  const [query, setQuery] = useState('');
  const [sort, setSort] = useState('newest');
  const visibleResumes = resumes.filter(file => file.file_name.toLowerCase().includes(query.trim().toLowerCase())).slice().sort((a, b) =>
    sort === 'name' ? a.file_name.localeCompare(b.file_name) : sort === 'oldest' ? a.id - b.id : b.id - a.id);
  const atLimit = resumes.length >= 20;
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const parsedResume = resumes.find(file => file.id === selectedId) || resumes[0] || null;
  const [error, setError] = useState('');
  const [deleting, setDeleting] = useState<number | null>(null);
  const [downloading, setDownloading] = useState<number | null>(null);
  async function download(file: any) {
    setDownloading(file.id); setError('');
    try {
      const blob = await fetchApi<Blob>(`/resume/session/${file.id}/file`, {}, 'blob');
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url; link.download = file.file_name;
      document.body.appendChild(link); link.click(); link.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (err: any) { setError(err.message || 'Could not download your resume.'); }
    finally { setDownloading(null); }
  }
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
        <p className="text-slate-400 text-sm mt-1">Upload a PDF or DOCX and check the extracted text. Role match compares your resume evidence with job requirements.</p>
      </div>
      {error && <p role="alert" className="text-rose-300">{error}</p>}
      {saved.error && <p role="alert" className="text-rose-300">Could not refresh saved resumes. {saved.data ? 'Your last loaded resumes are still shown.' : 'Your saved resumes are unavailable right now.'} <button onClick={saved.reload} className="underline">Retry saved resumes</button></p>}
      <button onClick={saved.reload} disabled={saved.loading} className="text-sm underline text-emerald-300 disabled:opacity-50">Refresh saved resumes</button>
      {saved.loading && <p role="status">Loading saved resumes…</p>}
      {!!resumes.length && <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-5 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div><h2 className="font-semibold text-white">Your resume library</h2><p className="text-sm text-slate-400">{resumes.length} of 20 resumes saved · PDF or DOCX, up to 5 MB each</p></div>
          <Link href="/dashboard" className="text-sm text-emerald-300 underline">Compare with a role</Link>
        </div>
        <div className="flex flex-col sm:flex-row gap-3">
          <input aria-label="Search saved resumes" type="search" value={query} onChange={event => setQuery(event.target.value)} placeholder="Find a resume by filename" className="min-w-0 flex-1 rounded-lg border border-white/15 bg-slate-950 px-3 py-2 text-white focus-visible:outline focus-visible:outline-emerald-400" />
          <select aria-label="Sort saved resumes" value={sort} onChange={event => setSort(event.target.value)} className="rounded-lg border border-white/15 bg-slate-950 px-3 py-2 text-white"><option value="newest">Newest first</option><option value="oldest">Oldest first</option><option value="name">Name A–Z</option></select>
        </div>
      </div>}
      {!!resumes.length && <section aria-label="Saved resumes" className="space-y-2">
        {!visibleResumes.length && <p role="status" className="text-sm text-slate-400">No filenames match your search. <button onClick={() => setQuery('')} className="underline text-emerald-300">Clear search</button></p>}
        {visibleResumes.map(file => <div key={file.id} className={`flex flex-wrap items-center gap-3 rounded-xl border p-3 transition-colors ${parsedResume?.id === file.id ? 'border-emerald-400/50 bg-emerald-400/5' : 'border-white/10 hover:bg-white/5'}`}>
          <button onClick={() => setSelectedId(file.id)} aria-pressed={parsedResume?.id === file.id} className="text-left flex-1 min-w-[120px] break-all text-emerald-300 focus-visible:outline focus-visible:outline-emerald-400">{file.file_name}<span className="block text-xs text-slate-400 mt-1">{parsedResume?.id === file.id ? 'Selected preview' : 'View preview'}</span></button>
          <button disabled={downloading !== null} onClick={() => download(file)} aria-label={`Download ${file.file_name}`} className="text-sm text-emerald-300 disabled:opacity-40">{downloading === file.id ? 'Downloading…' : 'Download'}</button>
          <button disabled={deleting !== null} onClick={() => remove(file.id)} aria-label={`Delete ${file.file_name}`} className="text-sm text-rose-300 disabled:opacity-40">{deleting === file.id ? 'Deleting…' : 'Delete'}</button>
        </div>)}
        <Link href="/dashboard" className="inline-block text-sm text-emerald-300 underline">Compare a saved resume with a role</Link>
      </section>}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-1">
          <Card glass className="sticky top-24"><h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2"><Sparkles className="w-5 h-5 text-indigo-400" />Upload Resume</h2>{atLimit ? <p role="status" className="text-sm text-amber-200">Your library is full. Delete a resume you no longer need to upload another. Download a copy first if you want to keep it.</p> : <Uploader onSuccess={(data) => { setSelectedId(data.id); setQuery(''); saved.update(files => [data, ...(files || [])]); setError(''); }} />}</Card>
        </div>
        <div className="lg:col-span-2">
          {parsedResume ? <ParsedPreview key={parsedResume.id} data={parsedResume} /> : saved.loading || saved.error ? <Card glass><p>{saved.loading ? "Loading your resume preview…" : "Resume preview is unavailable until saved resumes load. You can retry or upload a new document."}</p></Card> : <Card glass className="text-center py-16 border-dashed"><FileCheck className="w-12 h-12 text-slate-600 mx-auto mb-3" /><p className="text-slate-300 font-medium">No Resume Parsed Yet</p><p className="text-xs text-slate-500 max-w-sm mx-auto mt-1">Upload your PDF or DOCX file to preview recognized skills.</p></Card>}
        </div>
      </div>
    </div>
  );
}
