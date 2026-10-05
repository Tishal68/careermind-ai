"use client";

import { useEffect, useState } from 'react';
import { Card } from '@/components/UIComponents';
import { Uploader, GapBreakdown, JOB_ROLES } from '@/components/FeatureComponents';
import { fetchApi } from '@/lib/api';
import { Target, FileText, ArrowRight } from 'lucide-react';

export default function GapAnalysisPage() {
  const [resumes, setResumes] = useState<any[]>([]);
  const [resumeId, setResumeId] = useState('');
  const [role, setRole] = useState(JOB_ROLES[0]);
  const [report, setReport] = useState<any>(null);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    Promise.all([fetchApi<any[]>('/resume/my-resumes'), fetchApi<any[]>('/analysis/reports')])
      .then(([files, reports]) => {
        setResumes(files);
        const latest = reports[0];
        if (latest && files.some(f => f.id === latest.resume_id)) {
          setResumeId(String(latest.resume_id)); setRole(latest.job_role); setReport(latest);
        } else if (files.length) setResumeId(String(files[0].id));
      })
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  async function analyze() {
    setBusy(true); setError(''); setReport(null);
    try {
      setReport(await fetchApi('/analysis/analyze', {
        method: 'POST',
        body: JSON.stringify({ resume_id: Number(resumeId), field: 'Technology', job_role: role, experience_level: 'Unspecified' }),
      }));
    } catch (err: any) { setError(err.message || 'Could not analyze your resume.'); }
    finally { setBusy(false); }
  }

  return <div className="max-w-6xl mx-auto px-4 sm:px-8 py-10 space-y-8">
    <header className="space-y-3">
      <p className="text-emerald-400 text-xs uppercase tracking-widest font-bold">CareerMind AI / Your next step</p>
      <h1 className="text-3xl sm:text-4xl font-bold text-white">Find your fit. Build your skills.</h1>
      <p className="text-slate-400 max-w-2xl">Choose a job role and upload your resume. See which skills match, what to learn next, and talk through your plan with your career coach.</p>
    </header>
    {error && <p role="alert" className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-4 text-rose-300">{error}</p>}
    <div className="grid lg:grid-cols-[340px_1fr] gap-8 items-start">
      <div className="space-y-5">
        <Card glass className="space-y-4">
          <label htmlFor="target-role" className="flex items-center gap-2 font-bold text-white"><Target className="w-5 h-5 text-emerald-400" />1. Choose your target role</label>
          <select id="target-role" value={role} disabled={busy || loading} onChange={e => { setRole(e.target.value); setReport(null); }} className="w-full rounded-xl bg-slate-900 border border-slate-700 p-3 text-white">
            {JOB_ROLES.map(r => <option key={r}>{r}</option>)}
          </select>
        </Card>
        <Card glass className="space-y-4">
          <h2 className="flex items-center gap-2 font-bold text-white"><FileText className="w-5 h-5 text-emerald-400" />2. Add your resume</h2>
          <p className="text-xs text-slate-400">PDF or DOCX, up to 5 MB. Use a document with selectable text.</p>
          <Uploader onSuccess={file => { setResumes(prev => [file, ...prev]); setResumeId(String(file.id)); setReport(null); setError(''); }} />
          {resumes.length > 0 && <div>
            <label htmlFor="resume-select" className="block text-xs text-slate-400 mb-2">Or use a saved resume</label>
            <select id="resume-select" value={resumeId} disabled={busy} onChange={e => { setResumeId(e.target.value); setReport(null); }} className="w-full rounded-xl bg-slate-900 border border-slate-700 p-3 text-white text-sm">
              {resumes.map(file => <option key={file.id} value={file.id}>{file.file_name}</option>)}
            </select>
          </div>}
        </Card>
        <button onClick={analyze} disabled={!resumeId || busy || loading} className="w-full flex items-center justify-center gap-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 disabled:cursor-not-allowed py-3 text-white font-semibold">
          {busy ? 'Checking your skills…' : '3. Check role match'}<ArrowRight className="w-4 h-4" />
        </button>
      </div>
      <section aria-live="polite">
        {report ? <GapBreakdown report={report} /> : <Card glass className="text-center py-20 space-y-4 border-dashed">
          <Target className="w-12 h-12 text-emerald-400 mx-auto" />
          <h2 className="text-xl font-semibold text-white">{loading ? 'Loading your workspace…' : 'A clear path to your next role'}</h2>
          <p className="text-sm text-slate-400 max-w-sm mx-auto">Your skills match, gaps, and learning steps will appear here after you analyze your resume.</p>
        </Card>}
      </section>
    </div>
  </div>;
}
