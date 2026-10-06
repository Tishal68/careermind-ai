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
  const [location, setLocation] = useState('');
  const [level, setLevel] = useState('Junior');
  const [remote, setRemote] = useState(false);
  const [company, setCompany] = useState('');
  const [jobUrl, setJobUrl] = useState('');
  const [description, setDescription] = useState('');
  const [searchMarket, setSearchMarket] = useState(true);
  const [jobId, setJobId] = useState<number | null>(null);
  const [progress, setProgress] = useState('');

  useEffect(() => {
    Promise.all([fetchApi<any[]>('/resume/my-resumes'), fetchApi<any[]>('/analysis/reports')])
      .then(([files, reports]) => {
        setResumes(files);
        const latest = reports[0];
        if (latest && files.some(f => f.id === latest.resume_id)) {
          setResumeId(String(latest.resume_id)); setRole(latest.job_role); setReport(latest);
          const preferences = latest.analysis_data?.research?.preferences;
          if (preferences) {
            setLocation(preferences.location); setLevel(preferences.experience_level);
            setRemote(preferences.remote); setCompany(preferences.company || '');
            setJobUrl(preferences.job_url || ''); setSearchMarket(preferences.search_market);
          }
        } else if (files.length) setResumeId(String(files[0].id));
        const pending = Number(localStorage.getItem('careermind_research_job'));
        if (pending) { setJobId(pending); setBusy(true); }
      })
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!jobId) return;
    let stopped = false;
    let timer: ReturnType<typeof setTimeout>;
    let failures = 0;
    async function poll() {
      try {
        const state = await fetchApi<any>(`/analysis/research/${jobId}`);
        if (stopped) return;
        failures = 0;
        if (state.status === 'completed' || state.status === 'failed') {
          localStorage.removeItem('careermind_research_job');
          setJobId(null); setBusy(false); setProgress('');
          if (state.report) setReport(state.report);
          else setError(state.error || 'Research failed. Please retry.');
          return;
        }
        setProgress(state.status === 'pending' ? 'Preparing research…' : 'Reading job pages and comparing requirements with your resume. This may take a few minutes…');
      } catch (err: any) {
        if (stopped) return;
        failures++;
        if (err.status === 404 || failures >= 5) {
          if (err.status === 404) localStorage.removeItem('careermind_research_job');
          setError(`${err.message} Reload the page to check the research status.`);
          setBusy(false); return;
        }
      }
      if (!stopped) timer = setTimeout(poll, 4000);
    }
    poll();
    return () => { stopped = true; clearTimeout(timer); };
  }, [jobId]);

  async function analyze(refresh = false) {
    setBusy(true); setError(''); setProgress('Starting research…');
    try {
      const job = await fetchApi<any>('/analysis/research', {
        method: 'POST',
        body: JSON.stringify({ resume_id: Number(resumeId), job_role: role, location, experience_level: level,
          remote, company, job_url: jobUrl, job_description: description, search_market: searchMarket, refresh }),
      });
      localStorage.setItem('careermind_research_job', String(job.id));
      setJobId(job.id); setReport(null);
    } catch (err: any) { setError(err.message || 'Could not start research.'); setBusy(false); setProgress(''); }
  }

  return <div className="max-w-6xl mx-auto px-4 sm:px-8 py-10 space-y-8">
    <header className="space-y-3">
      <p className="text-emerald-400 text-xs uppercase tracking-widest font-bold">CareerMind AI / Your next step</p>
      <h1 className="text-3xl sm:text-4xl font-bold text-white">Find your fit. Build your skills.</h1>
      <p className="text-slate-400 max-w-2xl">Research any job role. Compare your resume with openings, discover common requirements, and build a plan for the company you want to join.</p>
    </header>
    {error && <p role="alert" className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-4 text-rose-300">{error}</p>}
    <div className="grid lg:grid-cols-[340px_1fr] gap-8 items-start">
      <fieldset disabled={busy || loading} className="space-y-5 min-w-0">
        <Card glass className="space-y-4">
          <label htmlFor="target-role" className="flex items-center gap-2 font-bold text-white"><Target className="w-5 h-5 text-emerald-400" />1. Choose your target role</label>
          <input id="target-role" list="role-suggestions" maxLength={100} value={role} onChange={e => { setRole(e.target.value); setReport(null); }} placeholder="e.g. Product Designer, Accountant" className="w-full rounded-xl bg-slate-900 border border-slate-700 p-3 text-white" />
          <datalist id="role-suggestions">{JOB_ROLES.map(r => <option key={r} value={r} />)}</datalist>
          <label className="block text-sm text-slate-300">Target location<input value={location} maxLength={150} onChange={e => setLocation(e.target.value)} placeholder="e.g. Bengaluru, India or Worldwide" className="mt-2 w-full rounded-xl bg-slate-900 border border-slate-700 p-3 text-white" /></label>
          <label className="block text-sm text-slate-300">Experience level<select value={level} onChange={e => setLevel(e.target.value)} className="mt-2 w-full rounded-xl bg-slate-900 border border-slate-700 p-3 text-white">{['Internship', 'Entry-level', 'Junior', 'Mid-Level', 'Senior', 'Lead', 'Any'].map(l => <option key={l}>{l}</option>)}</select></label>
          <label className="flex gap-2 text-sm text-slate-300"><input type="checkbox" checked={remote} onChange={e => setRemote(e.target.checked)} />Remote opportunities only</label>
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
        <Card glass className="space-y-4">
          <h2 className="font-semibold text-white">3. Applying to a specific company?</h2>
          <p className="text-xs text-slate-400">Optional: add its exact vacancy for a targeted comparison. Paste the description if the page requires a login.</p>
          <label className="block text-sm text-slate-300">Company<input value={company} maxLength={150} onChange={e => setCompany(e.target.value)} className="mt-2 w-full rounded-xl bg-slate-900 border border-slate-700 p-3" /></label>
          <label className="block text-sm text-slate-300">Job URL<input type="url" value={jobUrl} maxLength={2000} onChange={e => setJobUrl(e.target.value)} placeholder="https://company.com/careers/job" className="mt-2 w-full rounded-xl bg-slate-900 border border-slate-700 p-3" /></label>
          <label className="block text-sm text-slate-300">Job description<textarea rows={5} value={description} maxLength={16000} onChange={e => setDescription(e.target.value)} placeholder="Paste the full requirements here…" className="mt-2 w-full rounded-xl bg-slate-900 border border-slate-700 p-3" /></label>
          <label className="flex gap-2 text-sm text-slate-300"><input type="checkbox" checked={searchMarket} onChange={e => setSearchMarket(e.target.checked)} />Also research current market openings</label>
          <p className="text-xs text-slate-500">Your resume and job descriptions are analyzed by the configured Ollama model. Search uses only your role, level, and location preferences.</p>
        </Card>
        <button onClick={() => analyze()} disabled={!resumeId || !role.trim() || !location.trim() || (!searchMarket && !jobUrl.trim() && description.trim().length < 80) || busy || loading} className="w-full flex items-center justify-center gap-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 disabled:cursor-not-allowed py-3 text-white font-semibold">
          {busy ? 'Researching…' : 'Research my role match'}<ArrowRight className="w-4 h-4" />
        </button>
        {report?.analysis_data?.research && searchMarket && <button onClick={() => analyze(true)} disabled={busy || !location.trim() || !role.trim()} className="w-full text-sm text-emerald-300 underline">Refresh research with these preferences</button>}
      </fieldset>
      <section aria-live="polite">
        {busy && <Card glass className="mb-5"><p role="status" className="text-emerald-300">{progress || 'Resuming research…'}</p><p className="text-xs text-slate-400 mt-2">You can reload this page; it will check the saved task.</p></Card>}
        {report ? <GapBreakdown report={report} /> : <Card glass className="text-center py-20 space-y-4 border-dashed">
          <Target className="w-12 h-12 text-emerald-400 mx-auto" />
          <h2 className="text-xl font-semibold text-white">{loading ? 'Loading your workspace…' : 'A clear path to your next role'}</h2>
          <p className="text-sm text-slate-400 max-w-sm mx-auto">Your skills match, gaps, and learning steps will appear here after you analyze your resume.</p>
        </Card>}
      </section>
    </div>
  </div>;
}
