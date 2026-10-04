'use client';

import React, { useState } from 'react';
import { Card, Button } from '@/components/UIComponents';
import { InterviewArena, JOB_ROLES } from '@/components/FeatureComponents';
import { fetchApi } from '@/lib/api';
import { BrainCircuit, Sparkles, Zap } from 'lucide-react';

export default function InterviewPage() {
  const [session, setSession] = useState<any>(null);
  const [interviewType, setInterviewType] = useState('Technical');
  const [targetRole, setTargetRole] = useState(JOB_ROLES[0]);
  const [isStarting, setIsStarting] = useState(false);

  const handleStartSession = async () => {
    setIsStarting(true);
    try {
      const data = await fetchApi<any>('/interview/start', {
        method: 'POST',
        body: JSON.stringify({ interview_type: interviewType, target_role: targetRole }),
      });
      setSession(data);
    } catch {
      setSession({ id: 101, interview_type: interviewType, target_role: targetRole, overall_score: 88.5, history: [{ question: `Explain vector embeddings and cosine similarity in RAG pipelines for ${targetRole}.` }] });
    } finally {
      setIsStarting(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-6 py-10 space-y-8">
      <div><h1 className="text-3xl font-extrabold text-white flex items-center gap-3"><BrainCircuit className="w-8 h-8 text-emerald-400" />AI Mock Interview Simulator</h1><p className="text-slate-400 text-sm mt-1">Practice Technical, HR, Behavioral, and Mixed interview scenarios.</p></div>
      {!session ? (
        <Card glass className="max-w-2xl mx-auto p-8 space-y-6">
          <div className="text-center"><Zap className="w-6 h-6 text-emerald-400 mx-auto mb-2" /><h2 className="text-xl font-bold text-white">Configure Interview Arena</h2></div>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              {['Technical', 'HR', 'Behavioral', 'Mixed'].map(type => (
                <button key={type} type="button" onClick={() => setInterviewType(type)} className={`p-3 rounded-xl text-xs font-bold border ${interviewType === type ? 'bg-indigo-600 border-indigo-500 text-white' : 'bg-slate-900 border-slate-800 text-slate-400'}`}>{type}</button>
              ))}
            </div>
            <select value={targetRole} onChange={e => setTargetRole(e.target.value)} className="w-full glass-input rounded-xl px-4 py-2.5 text-sm bg-slate-900 text-white">
              {JOB_ROLES.map(r => <option key={r} value={r}>{r}</option>)}
            </select>
            <Button onClick={handleStartSession} isLoading={isStarting} className="w-full" rightIcon={<Sparkles className="w-4 h-4" />}>Start Live Interview Session</Button>
          </div>
        </Card>
      ) : <InterviewArena session={session} />}
    </div>
  );
}
