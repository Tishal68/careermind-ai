'use client';

import React, { useState } from 'react';
import { Card, Button } from '@/components/UIComponents';
import { InterviewArena } from '@/components/FeatureComponents';
import JobRoleInput from '@/components/JobRoleInput';
import { useAuth } from '@/context/AuthContext';
import { useAccountResource } from '@/hooks/useAccountResource';
import { fetchApi } from '@/lib/api';
import { BrainCircuit, Sparkles, Zap } from 'lucide-react';

export default function InterviewPage() {
  const { user } = useAuth();
  const saved = useAccountResource<any[]>('/interview/sessions');
  const [version, setVersion] = useState(0);
  const [resuming, setResuming] = useState(false);
  const [session, setSession] = useState<any>(null);
  const [interviewType, setInterviewType] = useState('Mixed');
  const [targetRole, setTargetRole] = useState(user?.target_job_role || '');
  const [error, setError] = useState('');
  const [isStarting, setIsStarting] = useState(false);

  const resumeSession = async (id: number) => {
    setResuming(true); setError('');
    try { const restored = await fetchApi<any>(`/interview/sessions/${id}`); setSession(restored); setVersion(value => value+1); }
    catch (err: any) { setError(err.message || 'Could not restore this interview.'); }
    finally { setResuming(false); }
  };
  const handleStartSession = async () => {
    if (targetRole.trim().length < 2) { setError('Enter a job title of 2 to 100 characters.'); return; }
    setIsStarting(true);
    setError('');
    try {
      const data = await fetchApi<any>('/interview/start', {
        method: 'POST',
        body: JSON.stringify({ interview_type: interviewType, target_role: targetRole.trim() }),
      });
      setSession(data); saved.reload();
    } catch (err: any) {
      setError(err.message || 'The interview provider is unavailable. Please retry.');
    } finally {
      setIsStarting(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-6 py-10 space-y-8">
      <div><h1 className="text-3xl font-extrabold text-white flex items-center gap-3"><BrainCircuit className="w-8 h-8 text-emerald-400" />Interview practice</h1><p className="text-slate-400 text-sm mt-1">Practice Technical, HR, Behavioral, and Mixed interview scenarios.</p></div>
      {error && <p role="alert" className="text-rose-300">{error}</p>}
      {!session && <section aria-label="Saved interviews" className="space-y-3">
        <h2 className="text-lg font-bold">Resume or review an interview</h2>
        {saved.loading && <p role="status">Loading saved interviews…</p>}
        {saved.error && <p role="alert">Could not load interviews. <button onClick={saved.reload} className="underline">Retry saved interviews</button></p>}
        {saved.data?.map(item => <button key={item.id} disabled={resuming || isStarting} onClick={() => resumeSession(item.id)} className="block text-emerald-300 underline">{item.completed ? 'Review' : 'Resume'} {item.target_role} · {new Date(item.created_at).toLocaleDateString()} · #{item.id}</button>)}
        {saved.data?.length === 0 && <p className="text-sm text-slate-400">No saved interviews yet. Start one below.</p>}
        <p className="text-xs text-slate-400">The 20 most recent sessions are shown. Evaluated answers and feedback are saved; unsent drafts are not.</p>
      </section>}
      {!session ? (
        <Card glass className="max-w-2xl mx-auto p-8 space-y-6">
          <div className="text-center"><Zap className="w-6 h-6 text-emerald-400 mx-auto mb-2" /><h2 className="text-xl font-bold text-white">Choose your practice session</h2></div>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              {['Technical', 'HR', 'Behavioral', 'Mixed'].map(type => (
                <button key={type} type="button" onClick={() => setInterviewType(type)} className={`p-3 rounded-xl text-xs font-bold border ${interviewType === type ? 'bg-indigo-600 border-indigo-500 text-white' : 'bg-slate-900 border-slate-800 text-slate-400'}`}>{type}</button>
              ))}
            </div>
            <label htmlFor="interview-role" className="block text-sm text-slate-300">Target job role</label>
            <JobRoleInput id="interview-role" value={targetRole} onChange={setTargetRole} />
            <Button onClick={handleStartSession} disabled={resuming} isLoading={isStarting} className="w-full" rightIcon={<Sparkles className="w-4 h-4" />}>Start interview</Button>
          </div>
        </Card>
      ) : <div className="space-y-4"><button onClick={() => setSession(null)} className="text-emerald-300 underline">Start a new interview</button><button disabled={resuming} onClick={() => resumeSession(session.id)} className="ml-4 text-emerald-300 underline">Reload saved interview</button><InterviewArena key={`${session.id}-${version}`} session={session} /></div>}
    </div>
  );
}
