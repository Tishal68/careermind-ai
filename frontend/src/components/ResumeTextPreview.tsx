"use client";
import { useAccountResource } from '@/hooks/useAccountResource';

export default function ResumeTextPreview({resumeId}: {resumeId: number}) {
  const source = useAccountResource<{text: string}>(`/resume/session/${resumeId}/text`);
  return <section aria-label="Extracted resume text" className="space-y-3">
    <p className="text-sm text-slate-400">Check that your experience, education and skills were read correctly. Formatting may differ from the original. If important text is missing, upload a text-based PDF or DOCX.</p>
    {source.loading && <p role="status">Loading extracted text…</p>}
    {source.error && <p role="alert" className="text-rose-300">Could not load extracted text. <button onClick={source.reload} className="underline">Retry extracted text</button></p>}
    {source.data && (source.data.text ? <pre tabIndex={0} aria-label="Resume text content" className="max-h-96 overflow-y-auto whitespace-pre-wrap break-words rounded-xl bg-slate-950 p-4 text-sm text-slate-200 font-sans">{source.data.text}</pre> : <p>No extracted text is available for this saved resume. Please upload it again.</p>)}
  </section>;
}
