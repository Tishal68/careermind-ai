'use client';

import React, { useState, useEffect } from 'react';
import { Button, Card, Input } from '@/components/UIComponents';
import { fetchApi } from '@/lib/api';
import dynamic from 'next/dynamic';
import ResumeTextPreview from '@/components/ResumeTextPreview';
const ResearchResults = dynamic(() => import('@/components/ResearchResults'), { loading: () => <p role="status" className="p-6 text-slate-400">Loading your results…</p> });
import {
  UploadCloud, FileText, CheckCircle2, AlertCircle, User, Mail, Phone, Code, GraduationCap, Briefcase, Award,
  Target, Sparkles, AlertTriangle, Lightbulb, CheckSquare, Square, Clock,
  FolderGit2, ArrowUpRight, Bot, Send, Trash2, BrainCircuit
} from 'lucide-react';

export const EXPERIENCE_LEVELS = ["Student", "Fresher", "Junior", "Mid-Level", "Senior"];

export const Uploader: React.FC<{ onSuccess: (data: any) => void }> = ({ onSuccess }) => {
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [success, setSuccess] = useState('');

  const validateAndSetFile = (selected: File) => {
    if (isUploading) return;
    setSuccess('');
    setError(null);
    setFile(null);
    if (!selected.name.toLowerCase().endsWith('.pdf') && !selected.name.toLowerCase().endsWith('.docx')) {
      setError('Invalid file format. Please upload a PDF or DOCX file.');
      return;
    }
    if (!selected.size || selected.size > 5 * 1024 * 1024) {
      setError('Choose a non-empty file no larger than 5 MB.');
      return;
    }
    setFile(selected);
  };

  const handleUpload = async () => {
    if (!file || isUploading) return;
    setIsUploading(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append('file', file);
      onSuccess(await fetchApi('/resume/upload', { method: 'POST', body: formData }));
      setSuccess(`${file.name} is ready to use.`);
      setFile(null);
    } catch (err: any) {
      setError(err.message || 'Error uploading file.');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="w-full space-y-4">
      <div
        onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
        onDragLeave={() => setIsDragOver(false)}
        onDrop={(e) => { e.preventDefault(); setIsDragOver(false); if (e.dataTransfer.files[0]) validateAndSetFile(e.dataTransfer.files[0]); }}
        className={`border-2 border-dashed rounded-2xl p-5 text-center transition-all cursor-pointer ${isDragOver ? 'border-indigo-500 bg-indigo-500/10' : 'border-slate-700/60 bg-slate-900/40'}`}
      >
        <input type="file" accept=".pdf,.docx" onChange={(e) => e.target.files?.[0] && validateAndSetFile(e.target.files[0])} className="sr-only peer" disabled={isUploading} id="resume-file-input" />
        <label htmlFor="resume-file-input" className="cursor-pointer block peer-focus-visible:outline peer-focus-visible:outline-emerald-400">
          <div className="p-4 rounded-full bg-indigo-600/10 border border-indigo-500/20 w-fit mx-auto text-indigo-400 mb-4"><UploadCloud className="w-6 h-6" /></div>
          {file ? <p className="text-sm font-semibold text-white break-all flex items-center justify-center gap-2"><FileText className="w-4 h-4 text-indigo-400" />{file.name}</p> : <p className="text-sm font-medium text-slate-200">Click to upload or drag & drop resume file (PDF/DOCX)</p>}
        </label>
      </div>
      {success && <p role="status" className="text-sm text-emerald-300 break-words">{success}</p>}
      {error && <div role="alert" className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs flex items-center gap-2"><AlertCircle className="w-4 h-4 shrink-0" /><span>{error}</span></div>}
      {file && <Button onClick={handleUpload} className="w-full" isLoading={isUploading} leftIcon={<CheckCircle2 className="w-4 h-4" />}>{isUploading ? 'Reading your resume…' : 'Use this resume'}</Button>}
    </div>
  );
};

export const ParsedPreview: React.FC<{ data: any }> = ({ data }) => {
  const [showText, setShowText] = useState(false);
  if (!data) return null;
  const parsed = data.parsed_data || {};
  const contact = parsed.contact || {};

  return (
    <div className="space-y-6">
      <Card glass className="space-y-4">
        <button type="button" aria-expanded={showText} aria-controls={`resume-text-${data.id}`} onClick={() => setShowText(value => !value)} className="text-emerald-300 underline">{showText ? 'Hide extracted resume text' : 'View extracted resume text'}</button>
        <div id={`resume-text-${data.id}`}>{showText && <ResumeTextPreview key={data.id} resumeId={data.id} />}</div>
      </Card>
      <Card glass className="border-indigo-500/20">
        <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-white/5">
          <div><h2 className="text-xl font-bold text-white flex items-center gap-2"><User className="w-5 h-5 text-indigo-400" />{contact.name || 'Candidate Profile'}</h2><p className="text-xs text-slate-400 mt-1">Uploaded File: {data.file_name}</p></div>
          <div className="flex flex-wrap gap-3 text-xs text-slate-300">
            {contact.email && <span className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 border border-slate-700"><Mail className="w-3.5 h-3.5 text-indigo-400" />{contact.email}</span>}
            {contact.phone && <span className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 border border-slate-700"><Phone className="w-3.5 h-3.5 text-indigo-400" />{contact.phone}</span>}
          </div>
        </div>
        <div className="pt-4 space-y-3">
          <p className="text-xs text-slate-400">This quick preview recognizes a limited technical vocabulary. It is not a complete skills assessment. Role research uses the extracted resume text, including non-technical experience.</p>
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5"><Code className="w-4 h-4 text-purple-400" />Recognized technical keywords ({parsed.technical_skills?.length || 0})</h3>
          <div className="flex flex-wrap gap-2">{parsed.technical_skills?.map((s: string, i: number) => <span key={i} className="px-3 py-1 rounded-lg text-xs font-medium bg-indigo-500/10 border border-indigo-500/30 text-indigo-300">{s}</span>)}</div>
        </div>
      </Card>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card glass><h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2"><Briefcase className="w-4 h-4 text-pink-400" />Experience</h3>{!parsed.experience?.length && <p className="text-xs text-slate-400">Not structured in this preview. This does not mean your resume has no experience.</p>}{parsed.experience?.map((e: any, i: number) => <div key={i} className="p-3 rounded-xl bg-slate-800/50 border border-slate-700/50 mb-2"><p className="text-sm font-semibold text-white">{e.title}</p><p className="text-xs text-indigo-400">{e.company} • {e.duration}</p></div>)}</Card>
        <Card glass><h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2"><GraduationCap className="w-4 h-4 text-cyan-400" />Education</h3>{!parsed.education?.length && <p className="text-xs text-slate-400">Not structured in this preview. Research checks the extracted resume text.</p>}{parsed.education?.map((ed: any, i: number) => <div key={i} className="p-3 rounded-xl bg-slate-800/50 border border-slate-700/50 mb-2"><p className="text-sm font-semibold text-white">{ed.degree}</p><p className="text-xs text-slate-400">{ed.institution}</p></div>)}</Card>
      </div>
    </div>
  );
};

export const GapBreakdown: React.FC<{ report: any }> = ({ report }) => {
  if (!report) return null;
  if (report.analysis_data?.research) return <ResearchResults report={report} />;
  const gap = report.gap_analysis || {};

  return (
    <div className="space-y-6">
      <Card glass className="border-emerald-500/30"><p className="text-xs font-semibold text-slate-400 uppercase">Skills match for {report.job_role}</p><p className="text-4xl font-extrabold text-emerald-400">{report.analysis_data?.match_percent ?? '—'}%</p><p className="text-lg font-semibold text-white mt-2">{report.analysis_data?.match_label}</p><p className="text-xs text-slate-400 mt-2">Skills mentioned in a resume do not prove proficiency. Missing skills may simply be absent from the document.</p></Card>
      {gap.reasoning && <Card glass className="border-indigo-500/20 bg-indigo-500/5"><div className="flex items-start gap-3"><Lightbulb className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" /><p className="text-xs text-slate-300 leading-relaxed">{gap.reasoning}</p></div></Card>}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card glass><h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2"><AlertTriangle className="w-4 h-4 text-rose-400" />Skills to learn or demonstrate</h3>{gap.missing_skills?.length === 0 && <p className="text-xs text-emerald-300">All listed core skills were found.</p>}<div className="flex flex-wrap gap-2">{gap.missing_skills?.map((s: string, i: number) => <span key={i} className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-rose-500/10 border border-rose-500/30 text-rose-300">+ {s}</span>)}</div></Card>
        <Card glass><h3 className="text-sm font-bold text-white mb-4">Skills found in resume</h3>{!report.analysis_data?.matched_skills?.length && <p className="text-xs text-slate-400">No core skills for this role were found in the resume.</p>}<div className="flex flex-wrap gap-2">{report.analysis_data?.matched_skills?.map((s: string) => <span key={s} className="px-3 py-1.5 rounded-lg text-xs bg-emerald-500/10 border border-emerald-500/30 text-emerald-300">{s}</span>)}</div></Card>
      </div>
      <Card glass><h3 className="text-sm font-bold text-white mb-4">How to upgrade yourself</h3><ol className="list-decimal list-inside space-y-3 text-sm text-slate-300">{gap.learning_steps?.map((step: string, i: number) => <li key={i}>{step}</li>)}</ol><a href="/dashboard/coach" className="inline-block mt-5 text-emerald-400 text-sm underline">Discuss your plan with the Ollama career coach</a></Card>
    </div>
  );
};

export const ProjectCard: React.FC<{ project: any }> = ({ project }) => (
  <Card glass glow className="flex flex-col justify-between h-full">
    <div className="space-y-4">
      <div className="flex justify-between gap-4"><div className="p-3 rounded-xl bg-indigo-600/10 text-indigo-400"><FolderGit2 className="w-6 h-6" /></div><span className="text-xs px-2.5 py-1 rounded-full bg-indigo-500/10 text-indigo-400">{project.difficulty}</span></div>
      <div><h3 className="text-lg font-bold text-white mb-1.5">{project.title}</h3><p className="text-xs text-slate-400">{project.description}</p></div>
      <div className="flex flex-wrap gap-1.5">{project.required_skills?.map((s: string, i: number) => <span key={i} className="text-xs px-2 py-0.5 rounded-md bg-slate-800 text-slate-300">{s}</span>)}</div>
    </div>
    <Button variant="outline" size="sm" className="w-full mt-6" rightIcon={<ArrowUpRight className="w-4 h-4" />}>Start Project Build</Button>
  </Card>
);

export const ChatWindow: React.FC = () => {
  const [messages, setMessages] = useState<any[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    fetchApi<any>('/chat/history').then(d => setMessages(d.messages?.length ? d.messages : [{ role: 'assistant', content: 'Hello! I am your AI Career Assistant. Ask me anything about career roadmaps, skill gaps, or interview prep!' }])).catch(() => {});
  }, []);

  const handleSend = async (txt?: string) => {
    const query = txt || input;
    if (!query.trim() || isLoading) return;
    setMessages(prev => [...prev, { role: 'user', content: query }]);
    if (!txt) setInput('');
    setIsLoading(true);
    try {
      const res = await fetchApi<any>('/chat/message', { method: 'POST', body: JSON.stringify({ content: query }) });
      setMessages(prev => [...prev, { role: 'assistant', content: res.content }]);
    } catch {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Error generating response.' }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card glass className="flex flex-col h-[75vh] p-0 border-indigo-500/20">
      <div className="px-6 py-4 border-b border-white/5 bg-slate-900/60 flex justify-between items-center"><h2 className="text-sm font-bold text-white flex items-center gap-2"><Bot className="w-5 h-5 text-indigo-400" />CareerMind RAG Assistant</h2></div>
      <div className="flex-1 p-6 overflow-y-auto space-y-4">{messages.map((m, i) => (
        <div key={i} className={`flex items-start gap-3 ${m.role === 'user' ? 'flex-row-reverse' : ''}`}>
          <div className={`p-2 rounded-xl ${m.role === 'user' ? 'bg-indigo-600 text-white' : 'bg-slate-800 text-indigo-400'}`}>{m.role === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}</div>
          <div className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm ${m.role === 'user' ? 'bg-indigo-600 text-white' : 'glass-card text-slate-200'}`}>{m.content}</div>
        </div>
      ))}</div>
      <div className="p-4 border-t border-white/5 bg-slate-900/60 flex items-center gap-3">
        <input type="text" placeholder="Ask AI Assistant..." value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === 'Enter' && handleSend()} className="flex-1 glass-input rounded-xl px-4 py-3 text-sm" />
        <Button onClick={() => handleSend()} isLoading={isLoading} rightIcon={<Send className="w-4 h-4" />}>Send</Button>
      </div>
    </Card>
  );
};

export const InterviewArena: React.FC<{ session: any }> = ({ session }) => {
  const [history, setHistory] = useState<any[]>(session.history || []);
  const activeIndex = history.length - 1;
  const lastAnswered = history.reduce((last: number, item: any, i: number) => item.answer != null ? i : last, -1);
  const restored = lastAnswered >= 0 ? history[lastAnswered] : null;
  const [questionIndex, setQuestionIndex] = useState(restored ? lastAnswered : activeIndex);
  const [question, setQuestion] = useState(restored?.question || history[activeIndex]?.question || '');
  const [answer, setAnswer] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [feedback, setFeedback] = useState<any>(restored ? {...restored.evaluation, user_answer: restored.answer,
    next_question: history[activeIndex]?.answer == null ? history[activeIndex]?.question : null} : null);
  const [evaluationError, setEvaluationError] = useState('');
  const [complete, setComplete] = useState(history.length > 0 && history[activeIndex].answer != null);

  const handleSubmit = async () => {
    if (!answer.trim() || isSubmitting || complete || feedback || !question) return;
    setIsSubmitting(true);
    setEvaluationError('');
    try {
      const data = await fetchApi<any>('/interview/evaluate', { method: 'POST', body: JSON.stringify({ session_id: session.id, question_index: questionIndex, question, user_answer: answer }) });
      setFeedback(data);
      setHistory(previous => {
        const next = previous.slice(0, questionIndex);
        next.push({question, answer, evaluation:data});
        if(data.next_question) next.push({question:data.next_question,answer:null,evaluation:null});
        return next;
      });
      if (!data.next_question) setComplete(true);
      setAnswer('');
    } catch (err: any) {
      setEvaluationError(err.message || 'Evaluation failed. Please retry.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {lastAnswered >= 0 && <details className="rounded-xl border border-white/10 p-4"><summary className="cursor-pointer text-emerald-300">Saved answers and feedback</summary>{history.filter((item: any) => item.answer != null).map((item: any, i: number) => <article key={i} className="mt-4 space-y-2 text-sm"><h3 className="font-semibold">{item.question}</h3><p className="whitespace-pre-wrap">{item.answer}</p><p>Practice feedback: {item.evaluation?.score ?? 'Unavailable'}</p><p className="whitespace-pre-wrap">{item.evaluation?.suggested_answer}</p></article>)}</details>}
      <Card glass className="space-y-6 border-purple-500/30">
        <div className="flex items-start gap-3"><BrainCircuit className="w-6 h-6 text-purple-400 shrink-0" /><p className="text-lg font-bold text-white">{question}</p></div>
        {evaluationError && <p role="alert" className="text-rose-300">{evaluationError}</p>}
        {!complete && !feedback && <textarea aria-label="Interview answer" disabled={isSubmitting} maxLength={10000} rows={5} placeholder="Type response..." value={answer} onChange={e => setAnswer(e.target.value)} className="w-full glass-input rounded-xl p-4 text-sm" />}
        {!complete && !feedback && <Button onClick={handleSubmit} isLoading={isSubmitting} disabled={!answer.trim()} className="w-full" rightIcon={<Send className="w-4 h-4" />}>Submit Answer & Evaluate</Button>}
        {complete && <p role="status" className="text-emerald-300">Interview complete. Review your feedback below.</p>}
      </Card>
      {feedback && (
        <Card glass className="space-y-4 border-indigo-500/30">
          <h3 className="text-lg font-bold text-white">Practice feedback: <span className="text-indigo-400">{feedback.score}%</span></h3>
          <p className="text-xs text-slate-400">AI practice feedback is guidance, not a hiring assessment.</p>
          <p className="text-sm text-slate-300"><strong>Your answer:</strong> {feedback.user_answer}</p>
          {!!feedback.strengths?.length && <div><h4 className="font-semibold text-emerald-300">Strengths</h4><ul className="list-disc pl-5 text-sm">{feedback.strengths.map((item: string, i: number) => <li key={i}>{item}</li>)}</ul></div>}
          {!!feedback.mistakes?.length && <div><h4 className="font-semibold text-amber-300">Ways to improve</h4><ul className="list-disc pl-5 text-sm">{feedback.mistakes.map((item: string, i: number) => <li key={i}>{item}</li>)}</ul></div>}
          <p className="text-sm text-slate-300"><strong>Answer-building template:</strong> {feedback.suggested_answer}</p>
          {!complete && feedback.next_question && <Button onClick={() => { setQuestion(feedback.next_question); setQuestionIndex(value => value+1); setFeedback(null); }}>Next question</Button>}
        </Card>
      )}
    </div>
  );
};
