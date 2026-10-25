"use client";

import { useEffect, useRef, useState } from 'react';
import { useAccountResource } from '@/hooks/useAccountResource';
import { Card } from '@/components/UIComponents';
import { Uploader, GapBreakdown } from '@/components/FeatureComponents';
import JobRoleInput from '@/components/JobRoleInput';
import { useAuth } from '@/context/AuthContext';
import { fetchApi } from '@/lib/api';
import { Target, FileText, ArrowRight, Check, ListChecks, Search, Sparkles } from 'lucide-react';

export default function GapAnalysisPage() {
  const { user } = useAuth();
  const saved = useAccountResource<any[]>('/resume/my-resumes');
  const recent = useAccountResource<any[]>('/analysis/reports?limit=1');
  const resumes = saved.data || [];
  const restored = useRef(false);
  const edited = useRef(false);
  const [resumeId, setResumeId] = useState('');
  const [role, setRole] = useState(user?.target_job_role || '');
  const [report, setReport] = useState<any>(null);
  const [busy, setBusy] = useState(false);
  const loading = saved.loading && saved.data === null;
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
  const submission = useRef<{body: string; key: string} | null>(null);

  useEffect(() => {
    if (!saved.data) return;
    setResumeId(previous => saved.data!.some(file => String(file.id) === previous) ? previous
      : String(saved.data!.find(file => file.id === recent.data?.[0]?.resume_id)?.id || saved.data![0]?.id || ''));
  }, [saved.data, recent.data]);

  useEffect(() => {
    if (!recent.data || restored.current) return;
    restored.current = true;
    const latest = recent.data[0];
    if (latest && !edited.current) {
      setReport(latest); setRole(latest.job_role);
      if (latest.resume_id) setResumeId(String(latest.resume_id));
      const preferences = latest.analysis_data?.research?.preferences;
      if (preferences) {
        setLocation(preferences.location); setLevel(preferences.experience_level);
        setRemote(preferences.remote); setCompany(preferences.company || '');
        setJobUrl(preferences.job_url || ''); setSearchMarket(preferences.search_market);
      }
    }
  }, [recent.data]);

  useEffect(() => {
    const pending = Number(localStorage.getItem('careermind_research_job'));
    if (pending) { restored.current = true; setJobId(pending); setBusy(true); }
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
          submission.current = null;
          setJobId(null); setBusy(false); setProgress('');
          if (state.report) setReport(state.report);
          else setError(state.error || 'Research failed. Please retry.');
          return;
        }
        setProgress(state.status === 'pending' ? 'Queued for research. Your task will start when a worker is available…' : 'Reading job pages and comparing requirements with your resume. This may take a few minutes…');
      } catch (err: any) {
        if (stopped) return;
        failures++;
        if (err.status === 404 || failures >= 5) {
          if (err.status === 404) localStorage.removeItem('careermind_research_job');
          setError(`${err.message} Reload the page to check the research status.`);
          setJobId(null); setBusy(false); setProgress(''); return;
        }
      }
      if (!stopped) timer = setTimeout(poll, 4000);
    }
    poll();
    return () => { stopped = true; clearTimeout(timer); };
  }, [jobId]);

  async function analyze(refresh = false) {
    if (busy || loading) return;
    const validation = !resumeId ? 'Upload or select a resume first.'
      : role.trim().length < 2 ? 'Enter your target role (at least 2 characters).'
      : location.trim().length === 1 ? 'Enter a location with at least 2 characters, or leave it blank for Worldwide.'
      : description.trim() && description.trim().length < 80 ? 'Paste the full job description (at least 80 characters).'
      : !searchMarket && !jobUrl.trim() && !description.trim() ? 'Add a job URL or description, or enable market research.' : '';
    if (validation) { setError(validation); return; }
    restored.current = true;
    setBusy(true); setError(''); setProgress('Starting research… The server may need up to 90 seconds to wake on the first request.');
    try {
      const body = JSON.stringify({ resume_id: Number(resumeId), job_role: role.trim(), location: location.trim() || 'Worldwide', experience_level: level,
        remote, company, job_url: jobUrl, job_description: description, search_market: searchMarket, refresh });
      if (submission.current?.body !== body) submission.current = {body, key: crypto.randomUUID()};
      const job = await fetchApi<any>('/analysis/research', {
        method: 'POST', headers: {'Idempotency-Key': submission.current!.key}, body,
      });
      localStorage.setItem('careermind_research_job', String(job.id));
      setJobId(job.id); setReport(null);
    } catch (err: any) { setError(err.message || 'Could not start research.'); setBusy(false); setProgress(''); }
  }

  return <div className="max-w-6xl mx-auto px-4 sm:px-8 py-10 space-y-8">
    <header className="space-y-3 pb-2">
      <p className="text-emerald-400 text-xs uppercase tracking-widest font-bold">CareerMind AI / Your next step</p>
      <h1 className="text-3xl sm:text-4xl xl:text-5xl font-semibold tracking-tight text-white">Find your fit. Build your skills.</h1>
      <p className="text-slate-400 max-w-2xl">Research any job role. Compare your resume with openings, discover common requirements, and build a plan for the company you want to join.</p>
    </header>
    {saved.error && <p role="alert" className="rounded-xl border border-rose-500/30 p-4 text-rose-300">Saved resumes could not be loaded. {saved.data ? 'Your last loaded resumes are still shown.' : 'Retry to access them; you do not need to upload them again.'} <button onClick={saved.reload} className="underline">Retry saved resumes</button></p>}
    {recent.error && <p role="alert" className="rounded-xl border border-rose-500/30 p-4 text-rose-300">Your saved report could not be loaded. You can still use a resume to research a role. <button onClick={recent.reload} className="underline">Retry saved report</button></p>}
    <div className="grid xl:grid-cols-[380px_1fr] gap-6 items-start">
      <fieldset onChange={() => { edited.current = true; }} disabled={busy} className="space-y-5 min-w-0">
        <Card glass className="space-y-4">
          <label htmlFor="target-role" className="flex items-center gap-2 font-bold text-white"><Target className="w-5 h-5 text-emerald-400" />1. Choose your target role</label>
          <JobRoleInput id="target-role" value={role} onChange={value => { edited.current = true; setRole(value); setReport(null); }} />
          <details className="text-xs text-slate-400"><summary className="py-2 text-slate-300">Specialized or regulated profession?</summary><p className="mt-2 leading-relaxed">Paste the actual job description and choose the relevant location. Results compare evidence; they do not verify professional licenses or eligibility.</p></details>
          <label className="block text-sm text-slate-300">Target location (optional)<input value={location} maxLength={150} onChange={e => setLocation(e.target.value)} placeholder="Worldwide, or enter a city / country" className="mt-2 w-full rounded-xl bg-slate-900 border border-slate-700 p-3 text-white" /></label>
          <label className="block text-sm text-slate-300">Experience level<select value={level} onChange={e => setLevel(e.target.value)} className="mt-2 w-full rounded-xl bg-slate-900 border border-slate-700 p-3 text-white">{['Internship', 'Entry-level', 'Junior', 'Mid-Level', 'Senior', 'Lead', 'Any'].map(l => <option key={l}>{l}</option>)}</select></label>
          <label className="flex gap-2 text-sm text-slate-300"><input type="checkbox" checked={remote} onChange={e => setRemote(e.target.checked)} />Remote opportunities only</label>
        </Card>
        <Card glass className="space-y-4">
          <h2 className="flex items-center gap-2 font-bold text-white"><FileText className="w-5 h-5 text-emerald-400" />2. Add your resume</h2>
          <p className="text-xs text-slate-400">PDF or DOCX, up to 5 MB. Use a document with selectable text.</p>
          <Uploader onSuccess={file => { edited.current = true; saved.update(prev => [file, ...(prev || [])]); setResumeId(String(file.id)); setReport(null); setError(''); }} />
          {loading && <p role="status" className="text-sm text-slate-400">Loading saved resumes… You can still choose a role or upload a new resume.</p>}
          {resumes.length > 0 && <div>
            <label htmlFor="resume-select" className="block text-xs text-slate-400 mb-2">Or use a saved resume</label>
            <select id="resume-select" value={resumeId} disabled={busy} onChange={e => { setResumeId(e.target.value); setReport(null); }} className="w-full rounded-xl bg-slate-900 border border-slate-700 p-3 text-white text-sm">
              {resumes.map(file => <option key={file.id} value={file.id}>{file.file_name}</option>)}
            </select>
          </div>}
        </Card>
        <Card glass className="space-y-4">
          <details className="space-y-4">
          <summary className="font-semibold text-white py-2">Tailor to a company <span className="text-xs text-slate-400 font-normal">· Optional</span></summary>
          <p className="text-xs text-slate-400">Optional: add its exact vacancy for a targeted comparison. Paste the description if the page requires a login.</p>
          <label className="block text-sm text-slate-300">Company<input value={company} maxLength={150} onChange={e => setCompany(e.target.value)} className="mt-2 w-full rounded-xl bg-slate-900 border border-slate-700 p-3" /></label>
          <label className="block text-sm text-slate-300">Job URL<input type="url" value={jobUrl} maxLength={2000} onChange={e => setJobUrl(e.target.value)} placeholder="https://company.com/careers/job" className="mt-2 w-full rounded-xl bg-slate-900 border border-slate-700 p-3" /></label>
          <label className="block text-sm text-slate-300">Job description<textarea rows={5} value={description} maxLength={16000} onChange={e => setDescription(e.target.value)} placeholder="Paste the full requirements here…" className="mt-2 w-full rounded-xl bg-slate-900 border border-slate-700 p-3" /></label>
          </details>
          <label className="flex gap-2 text-sm text-slate-300"><input type="checkbox" checked={searchMarket} onChange={e => setSearchMarket(e.target.checked)} />Also research current market openings</label>
          <p className="text-xs text-slate-500">Your resume and job descriptions are analyzed by the configured Ollama model. Search uses only your role, level, and location preferences.</p>
        </Card>
        <p className="text-xs text-slate-400">{resumeId ? "Ready to research. A blank location searches Worldwide." : "Upload or select a resume to research your role match."}</p>
        {error && <p role="alert" className="text-sm text-rose-300">{error}</p>}
        <button onClick={() => analyze()} disabled={busy || loading} className="w-full flex items-center justify-center gap-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 disabled:cursor-not-allowed py-3 text-white font-semibold">
          {busy ? 'Researching…' : 'Research my role match'}<ArrowRight className="w-4 h-4" />
        </button>
        {report?.analysis_data?.research && searchMarket && <button onClick={() => analyze(true)} disabled={busy || loading} className="w-full text-sm text-emerald-300 underline">Refresh research with these preferences</button>}
      </fieldset>
      <section aria-live="polite" className="xl:sticky xl:top-24 min-w-0">
        {busy && <Card glass className="mb-5"><p role="status" className="text-emerald-300">{progress || 'Resuming research…'}</p><p className="text-xs text-slate-400 mt-2">You can reload this page; it will check the saved task.</p></Card>}
        {report ? <GapBreakdown report={report} /> : <Card glass className="overflow-hidden !p-0">
          <div className="bg-gradient-to-br from-emerald-400/10 to-transparent p-6 sm:p-8 border-b border-white/5">
            <span className="inline-flex items-center gap-2 text-xs font-medium text-emerald-300"><Sparkles size={14} />Your career, with direction</span>
            <div className="mt-7 mb-5 grid place-items-center rounded-2xl bg-emerald-300/10 border border-emerald-300/20 w-14 h-14"><Target className="w-7 h-7 text-emerald-300" /></div>
            <h2 className="text-2xl font-semibold tracking-tight text-white">{loading || recent.loading ? 'Loading your workspace…' : recent.error ? 'Saved report temporarily unavailable' : 'A clear path to your next role'}</h2>
            <p className="text-sm leading-relaxed text-slate-400 max-w-md mt-3">Start with a role and your resume. We’ll help you understand where your experience fits and what to work on next.</p>
          </div>
          <div className="p-6 sm:p-8 space-y-6">
            {[[Search, 'Best-fit openings', 'Explore opportunities backed by current job sources.'], [Target, 'Typical role requirements', 'See which requirements your resume supports—and what is not yet evidenced.'], [ListChecks, 'Your next steps', 'Turn your findings into a focused learning plan.']].map(([Icon, title, text]: any) => <div key={title} className="flex gap-4"><span className="shrink-0 rounded-xl bg-white/5 p-2.5 h-fit"><Icon size={18} className="text-slate-300" /></span><div><h3 className="text-sm font-semibold text-slate-200">{title}</h3><p className="text-sm text-slate-400 leading-relaxed mt-1">{text}</p></div></div>)}
            <div className="pt-5 border-t border-white/10 flex flex-wrap gap-3 text-xs">
              <span className={role.trim().length >= 2 ? 'text-emerald-300' : 'text-slate-400'}>{role.trim().length >= 2 && <Check size={13} className="inline mr-1" />}1. {role.trim().length >= 2 ? 'Role selected' : 'Choose a role'}</span>
              <span className={resumeId ? 'text-emerald-300' : 'text-slate-400'}>{resumeId && <Check size={13} className="inline mr-1" />}2. {resumeId ? 'Resume ready' : 'Add your resume'}</span>
              <span className="text-slate-400">3. Research your match</span>
            </div>
          </div>
        </Card>}
      </section>
    </div>
  </div>;
}
