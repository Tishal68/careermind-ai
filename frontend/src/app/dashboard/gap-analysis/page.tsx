'use client';

import React, { useState, useEffect } from 'react';
import { Card } from '@/components/UIComponents';
import { RoleSelector, GapBreakdown, FIELDS, JOB_ROLES, EXPERIENCE_LEVELS } from '@/components/FeatureComponents';
import { fetchApi } from '@/lib/api';
import { Target, Sparkles } from 'lucide-react';

export default function GapAnalysisPage() {
  const [resumes, setResumes] = useState<any[]>([]);
  const [selectedResumeId, setSelectedResumeId] = useState<string>('');
  const [selectedField, setSelectedField] = useState<string>(FIELDS[0]);
  const [selectedRole, setSelectedRole] = useState<string>(JOB_ROLES[0]);
  const [selectedLevel, setSelectedLevel] = useState<string>(EXPERIENCE_LEVELS[2]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [report, setReport] = useState<any>(null);

  useEffect(() => {
    fetchApi<any[]>('/resume/my-resumes').then((data) => {
      setResumes(data);
      if (data.length > 0) setSelectedResumeId(data[0].id.toString());
    }).catch(() => {});
  }, []);

  const handleAnalyze = async () => {
    if (!selectedResumeId) return;
    setIsAnalyzing(true);
    try {
      const data = await fetchApi<any>('/analysis/analyze', {
        method: 'POST',
        body: JSON.stringify({ resume_id: parseInt(selectedResumeId), field: selectedField, job_role: selectedRole, experience_level: selectedLevel }),
      });
      setReport(data);
    } catch {
      alert('Analysis error');
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-6 py-10 space-y-8">
      <div><h1 className="text-3xl font-extrabold text-white flex items-center gap-3"><Target className="w-8 h-8 text-purple-400" />Skill Gap Analysis & Benchmark</h1><p className="text-slate-400 text-sm mt-1">Select a target job role to perform a Gemini-powered gap analysis.</p></div>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-1">
          <RoleSelector resumes={resumes} selectedResumeId={selectedResumeId} setSelectedResumeId={setSelectedResumeId} selectedField={selectedField} setSelectedField={setSelectedField} selectedRole={selectedRole} setSelectedRole={setSelectedRole} selectedLevel={selectedLevel} setSelectedLevel={setSelectedLevel} onAnalyze={handleAnalyze} isAnalyzing={isAnalyzing} />
        </div>
        <div className="lg:col-span-2">
          {report ? <GapBreakdown report={report} /> : <Card glass className="text-center py-20 border-dashed"><Sparkles className="w-12 h-12 text-slate-600 mx-auto mb-3" /><p className="text-slate-300 font-medium">Ready for Gap Analysis</p></Card>}
        </div>
      </div>
    </div>
  );
}
