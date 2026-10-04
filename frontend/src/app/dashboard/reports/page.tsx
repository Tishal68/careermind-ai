'use client';

import React, { useState, useEffect } from 'react';
import { Card, Button, NexScoreGauge } from '@/components/UIComponents';
import { fetchApi } from '@/lib/api';
import { FileCheck2, Printer, Download, CheckCircle2, AlertTriangle, Sparkles, Compass } from 'lucide-react';

export default function ReportsPage() {
  const [reports, setReports] = useState<any[]>([]);
  const [selectedReport, setSelectedReport] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchApi<any[]>('/analysis/reports')
      .then(data => {
        setReports(data);
        if (data.length > 0) setSelectedReport(data[0]);
      })
      .catch(() => {})
      .finally(() => setIsLoading(false));
  }, []);

  const handlePrint = () => {
    window.print();
  };

  if (isLoading) {
    return (
      <div className="min-h-[80vh] flex items-center justify-center p-6">
        <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!selectedReport) {
    return (
      <div className="max-w-4xl mx-auto px-6 py-20 text-center space-y-4">
        <Card className="p-12 border-emerald-500/20 bg-[#0b1320]">
          <FileCheck2 className="w-12 h-12 text-emerald-400 mx-auto mb-3" />
          <h2 className="text-xl font-bold text-white">No Career Reports Found</h2>
          <p className="text-xs text-slate-400 max-w-sm mx-auto">
            Upload your resume on the Workspace Dashboard to automatically generate executive career reports.
          </p>
        </Card>
      </div>
    );
  }

  const gap = selectedReport.gap_analysis || {};
  const analysis = selectedReport.analysis_data || {};
  const nexScoreData = selectedReport.nex_score_breakdown || { nex_score: selectedReport.nex_score || 78.5 };

  return (
    <div className="max-w-6xl mx-auto px-6 py-10 space-y-8">
      {/* Report Header & Controls */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-6 border-b border-white/10 print:hidden">
        <div>
          <span className="text-xs font-bold text-emerald-400 uppercase tracking-widest flex items-center gap-2">
            <Compass className="w-4 h-4" /> Executive Consulting Report
          </span>
          <h1 className="text-2xl font-extrabold text-white mt-1">
            Career Readiness Summary: <span className="text-emerald-400">{selectedReport.job_role}</span>
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">Report Date: {new Date(selectedReport.created_at).toLocaleDateString()}</p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" size="sm" onClick={handlePrint} leftIcon={<Printer className="w-3.5 h-3.5" />}>
            Print / Export PDF
          </Button>
        </div>
      </div>

      {/* Printable Report Document */}
      <div className="space-y-8 bg-[#0b1320] p-8 rounded-2xl border border-white/10 print:bg-white print:text-black print:p-0 print:border-0">
        {/* Document Header */}
        <div className="flex justify-between items-start border-b border-white/10 pb-6 print:border-gray-200">
          <div>
            <h2 className="text-xl font-bold text-white print:text-gray-900">NexPath Executive Assessment</h2>
            <p className="text-xs text-slate-400 print:text-gray-600">Candidate Target Role: {selectedReport.job_role} ({selectedReport.experience_level})</p>
          </div>
          <div className="text-right">
            <span className="text-2xl font-extrabold text-emerald-400 print:text-emerald-700">{Math.round(selectedReport.nex_score || 78.5)}</span>
            <span className="text-[10px] block font-bold text-slate-400 uppercase">NexScore™ Rating</span>
          </div>
        </div>

        {/* Executive Summary */}
        <div className="space-y-3">
          <h3 className="text-sm font-bold text-white print:text-gray-900 uppercase tracking-wider">1. Executive Overview</h3>
          <p className="text-xs text-slate-300 print:text-gray-700 leading-relaxed">
            {gap.reasoning || `The candidate exhibits a competitive foundation for the ${selectedReport.job_role} role with high technical aptitude. Enhancing hands-on production deployment experience will maximize hiring conversion.`}
          </p>
        </div>

        {/* Quantitative Scores Grid */}
        <div className="grid grid-cols-3 gap-4 pt-2">
          <div className="p-4 rounded-xl bg-slate-900 border border-white/10 print:bg-gray-50 print:border-gray-200 text-center">
            <span className="text-[10px] font-bold text-slate-400 print:text-gray-600 uppercase">ATS Compatibility</span>
            <span className="text-xl font-extrabold text-emerald-400 print:text-emerald-700 block mt-1">{selectedReport.ats_score}%</span>
          </div>
          <div className="p-4 rounded-xl bg-slate-900 border border-white/10 print:bg-gray-50 print:border-gray-200 text-center">
            <span className="text-[10px] font-bold text-slate-400 print:text-gray-600 uppercase">Resume Quality</span>
            <span className="text-xl font-extrabold text-indigo-400 print:text-indigo-700 block mt-1">{selectedReport.resume_score}%</span>
          </div>
          <div className="p-4 rounded-xl bg-slate-900 border border-white/10 print:bg-gray-50 print:border-gray-200 text-center">
            <span className="text-[10px] font-bold text-slate-400 print:text-gray-600 uppercase">Role Readiness</span>
            <span className="text-xl font-extrabold text-orange-400 print:text-orange-700 block mt-1">{selectedReport.readiness_score}%</span>
          </div>
        </div>

        {/* Strengths & Missing Skill Gaps */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
          <div className="space-y-3">
            <h4 className="text-xs font-bold text-emerald-400 print:text-emerald-700 uppercase tracking-wider">Validated Technical Strengths</h4>
            <ul className="space-y-2 text-xs text-slate-300 print:text-gray-700">
              {(analysis.strengths || ["Strong programming foundation"]).map((s: string, idx: number) => (
                <li key={idx} className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                  <span>{s}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="space-y-3">
            <h4 className="text-xs font-bold text-orange-400 print:text-orange-700 uppercase tracking-wider">Identified Skill Gaps</h4>
            <ul className="space-y-2 text-xs text-slate-300 print:text-gray-700">
              {(gap.missing_skills || ["Docker", "AWS Deployment"]).map((m: string, idx: number) => (
                <li key={idx} className="flex items-start gap-2">
                  <AlertTriangle className="w-4 h-4 text-orange-400 shrink-0 mt-0.5" />
                  <span>{m}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
