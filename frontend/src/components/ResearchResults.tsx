'use client';

import { Card } from '@/components/UIComponents';

function SourceLink({ url, children }: { url?: string; children: React.ReactNode }) {
  return url?.startsWith('https://') ? <a href={url} target="_blank" rel="noopener noreferrer" className="text-emerald-300 underline break-all">{children}</a> : <span>{children}</span>;
}

function Opening({ job }: { job: any }) {
  return <Card glass className="space-y-4">
    <div className="flex gap-4 justify-between items-start">
      <div><h3 className="font-semibold text-white"><SourceLink url={job.url}>{job.title}</SourceLink></h3><p className="text-sm text-slate-400 mt-1">{job.company} · {job.location}</p></div>
      <div className="text-right shrink-0"><p className="text-2xl font-bold text-emerald-300">{job.coverage}%</p><p className="text-xs text-slate-400">Requirement coverage</p></div>
    </div>
    <p className="text-xs text-slate-400">{job.user_provided ? 'User-provided description (linked page not fetched)' : 'Source retrieved'} · {new Date(job.retrieved_at).toLocaleString()}<br />{job.availability}</p>
    {job.comparison_reason && <p className="text-sm text-slate-300">{job.comparison_reason}</p>}
    {!job.comparable && <p className="text-sm text-amber-300">Role, location, or experience alignment could not be fully confirmed. Check the requirements before applying.</p>}
    {!!job.required_gaps?.length && <p className="text-sm text-amber-300">Required items to verify or demonstrate: {job.required_gaps.join(', ')}</p>}
    {job.validation_note && <p className="text-xs text-amber-300">{job.validation_note}</p>}
    <details className="rounded-lg border border-white/10 p-3">
      <summary className="cursor-pointer text-sm text-emerald-300">View requirements and resume evidence</summary>
      <ul className="space-y-4 mt-4">{job.requirements.map((r: any, index: number) => <li key={index} className="text-sm border-t border-white/10 pt-3">
        <p className="font-semibold text-white">{r.name} <span className="text-xs text-slate-400">· {r.importance} · {r.kind}</span></p>
        <p className="mt-1 text-slate-400">Job: “{r.source_quote}”</p>
        <p className={`mt-2 ${r.resume_status === 'evidenced' ? 'text-emerald-300' : 'text-amber-300'}`}>{r.resume_status === 'evidenced' ? 'Evidence found' : r.resume_status === 'partial' ? 'Partial evidence' : 'Not evidenced in resume'}{r.resume_quote ? `: “${r.resume_quote}”` : ''}</p>
      </li>)}</ul>
    </details>
  </Card>;
}

export default function ResearchResults({ report }: { report: any }) {
  const research = report.analysis_data.research;
  const gap = report.gap_analysis || {};
  return <div className="space-y-6">
    <Card glass className="space-y-3 border-emerald-500/30">
      <h2 className="text-xl font-bold text-white">Your {report.job_role} research</h2>
      <p className="text-sm text-slate-300">{research.preferences.location} · {report.experience_level}{research.preferences.remote ? ' · Remote' : ''}</p>
      <p className="text-xs text-slate-400">Analyzed {new Date(research.researched_at).toLocaleString()} · {research.sample_size} comparable postings</p>
      <p className="text-sm text-slate-400">Coverage reflects evidence in your resume. It does not predict hiring or prove proficiency.</p>
      {research.warnings?.map((warning: string, i: number) => <p key={i} className="text-sm text-amber-200">{warning}</p>)}
    </Card>
    {research.company_match && <section className="space-y-3"><h2 className="text-xl font-semibold text-white">Company-specific match</h2><Opening job={research.company_match} /></section>}
    <section className="space-y-3">
      <h2 className="text-xl font-semibold text-white">Best-fit openings</h2>
      <p className="text-sm text-slate-400">Ranked within the retrieved sample. Check the employer’s page for current availability.</p>
      {research.best_fit_openings.length ? research.best_fit_openings.map((job: any, i: number) => <Opening key={job.url || i} job={job} />) : <Card glass><p className="text-sm text-slate-400">No comparable market openings in this report. Enable live research or broaden your preferences.</p></Card>}
    </section>
    <Card glass className="space-y-4">
      <h2 className="text-xl font-semibold text-white">Typical requirements in this sample</h2>
      <p className="text-sm text-slate-400">Frequency counts each requirement once per comparable posting. This is a small researched sample, not a market-wide average.</p>
      {research.sample_status === 'insufficient_evidence' ? <p className="text-amber-200 text-sm">At least three comparable postings are needed. There is not enough evidence for this summary yet.</p> : <ul className="space-y-4">{research.typical_requirements.map((r: any) => <li key={r.key}>
        <div className="flex gap-3 justify-between text-sm"><span className="text-white">{r.name}</span><span className="text-slate-300 shrink-0">{r.posting_count}/{research.sample_size} · {r.frequency_percent}%</span></div>
        <div className="h-1.5 bg-slate-800 rounded-full mt-2"><div className="h-full bg-emerald-500 rounded-full" style={{width: `${r.frequency_percent}%`}} /></div>
        <p className="text-xs text-slate-400 mt-2">Required in {r.required_count} postings · {r.resume_status === 'evidenced' ? 'Resume evidence found' : 'Review resume evidence'}</p>
        <div className="text-xs flex flex-wrap gap-3 mt-1">{r.source_urls.map((url: string, i: number) => <SourceLink key={url} url={url}>Source {i + 1}</SourceLink>)}</div>
      </li>)}</ul>}
    </Card>
    <Card glass className="space-y-4"><h2 className="text-xl font-semibold text-white">Your improvement priorities</h2><p className="text-sm text-slate-400">{research.company_match ? 'Prioritized against the company description.' : 'Prioritized by required status and frequency across comparable postings.'} Missing evidence may mean your resume needs updating.</p><ol className="list-decimal list-inside space-y-3 text-sm text-slate-300">{gap.learning_steps?.map((step: string, i: number) => <li key={i}>{step}</li>)}</ol><a href="/dashboard/coach" className="inline-block text-emerald-300 underline">Build a learning plan with your career coach</a></Card>
    <details className="text-sm text-slate-400"><summary className="cursor-pointer">How this comparison works</summary><p className="mt-3">{research.method}</p>{research.excluded_comparisons?.map((item: any, i: number) => <p className="mt-3" key={i}><SourceLink url={item.url}>{item.title}</SourceLink>: excluded from the comparable sample. {item.reason}</p>)}</details>
  </div>;
}
