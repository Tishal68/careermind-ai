'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { fetchApi } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';
import { 
  Sparkles, CheckCircle2, AlertTriangle, ArrowRight, Target, Map, 
  FolderGit2, Bot, Bell, Calendar, ChevronDown, Award, TrendingUp,
  Clock, Send, Compass, ShieldCheck, Check, ChevronLeft, ChevronRight, FileText
} from 'lucide-react';

export default function WorkspaceDashboard() {
  const { user } = useAuth();
  const [pipelineData, setPipelineData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [chatInput, setChatInput] = useState('');
  const [proactiveMessages, setProactiveMessages] = useState<any[]>([
    { id: 1, icon: '🛡️', text: 'You haven\'t completed any project in the last 2 weeks. Want me to suggest one?' },
    { id: 2, icon: '🤖', text: 'Your AWS skills are missing. I added a learning path for you.' },
    { id: 3, icon: '⚙️', text: 'System Design is a high priority skill for your target role. Shall we start now?' },
    { id: 4, icon: '✅', text: 'Your NexScore improved by 8 points this week! Great consistency 🚀' }
  ]);

  const loadWorkspace = async () => {
    setIsLoading(true);
    try {
      const reports = await fetchApi<any[]>('/analysis/reports');
      const resumes = await fetchApi<any[]>('/resume/my-resumes');
      
      if (resumes.length > 0 && reports.length > 0) {
        const latestReport = reports[0];
        setPipelineData({
          resume: resumes[0],
          report: latestReport,
          nex_score: latestReport.nex_score || 89,
          ats_score: latestReport.ats_score || 92,
          skills_match: 78,
          interview_readiness: 74,
          roadmap: latestReport.roadmap_data?.milestones || [],
          projects: latestReport.project_recommendations || []
        });
      } else {
        setPipelineData({
          nex_score: 89,
          ats_score: 92,
          skills_match: 78,
          interview_readiness: 74
        });
      }
    } catch (err: any) {
      console.error('Error loading workspace:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadWorkspace();
  }, []);

  const handleSendPrompt = (text: string) => {
    if (!text.trim()) return;
    window.location.href = `/dashboard/coach?q=${encodeURIComponent(text)}`;
  };

  if (isLoading) {
    return (
      <div className="min-h-[80vh] flex items-center justify-center p-6 bg-[#fbf9f5]">
        <div className="text-center space-y-3">
          <div className="w-10 h-10 border-3 border-[#0F5E4E] border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-xs font-semibold text-slate-500">Loading NexPath Workspace...</p>
        </div>
      </div>
    );
  }

  const nexScore = pipelineData?.nex_score || 89;
  const atsScore = pipelineData?.ats_score || 92;
  const skillsMatch = pipelineData?.skills_match || 78;
  const intReadiness = pipelineData?.interview_readiness || 74;

  return (
    <div className="p-8 max-w-[1650px] mx-auto space-y-8 bg-[#fbf9f5] min-h-screen text-slate-900 font-sans">
      {/* Top Header Bar */}
      <div className="flex flex-wrap items-start justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <p className="text-sm font-semibold text-slate-600 flex items-center gap-1.5">
            Good morning, {user?.full_name?.split(' ')[0] || 'Tishal'} 👋
          </p>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 mt-1">
            Your career is moving <span className="font-serif italic text-[#0F5E4E]">forward</span>
          </h1>
          <p className="text-xs text-slate-500 max-w-xl mt-1.5 leading-relaxed">
            NexPath AI analyzed your profile and prepared everything to help you reach <strong className="text-[#0F5E4E] font-semibold">{user?.target_job_role || 'AI Engineer'}</strong> at top product companies.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white border border-slate-200 text-xs font-semibold text-slate-700 shadow-sm hover:bg-slate-50">
            <Calendar className="w-3.5 h-3.5 text-slate-500" />
            <span>Today</span>
            <ChevronDown className="w-3 h-3 text-slate-400" />
          </button>
          <button className="p-2 rounded-lg bg-white border border-slate-200 text-slate-600 shadow-sm hover:bg-slate-50 relative">
            <Bell className="w-4 h-4" />
            <span className="w-2 h-2 rounded-full bg-emerald-500 absolute top-1.5 right-1.5" />
          </button>
          <div className="w-8 h-8 rounded-full bg-[#0F5E4E] text-white flex items-center justify-center font-bold text-xs">
            {user?.full_name ? user.full_name[0].toUpperCase() : 'T'}
          </div>
        </div>
      </div>

      {/* Main Layout Grid: Left 2/3 Content + Right 1/3 AI Coach Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left Column (2 Cols wide) */}
        <div className="lg:col-span-2 space-y-8">
          
          {/* Row 1: 4 Score Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            
            {/* Card 1: NexScore */}
            <div className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-sm space-y-3">
              <div className="flex justify-between items-center text-xs">
                <span className="font-bold text-slate-700">NexScore</span>
                <span className="text-[10px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full">Excellent</span>
              </div>
              <div className="flex items-baseline gap-1">
                <span className="text-3xl font-extrabold text-slate-900">{nexScore}</span>
                <span className="text-xs text-slate-400 font-medium">/100</span>
              </div>
              <div className="h-6 flex items-end gap-1 pt-1">
                {[35, 42, 58, 64, 72, 81, nexScore].map((h, i) => (
                  <div key={i} className="flex-1 bg-emerald-500/20 rounded-t hover:bg-emerald-500 transition-all" style={{ height: `${h}%` }} />
                ))}
              </div>
              <p className="text-[11px] font-semibold text-emerald-700 flex items-center gap-1">
                <TrendingUp className="w-3 h-3" /> ↑ 8 points this week
              </p>
            </div>

            {/* Card 2: ATS Score */}
            <div className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-sm space-y-3 flex flex-col justify-between">
              <div className="flex justify-between items-center text-xs">
                <span className="font-bold text-slate-700">ATS Score</span>
                <span className="text-[10px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full">Excellent</span>
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-3xl font-extrabold text-slate-900">{atsScore}%</span>
                  <p className="text-[11px] font-semibold text-emerald-700 flex items-center gap-1 mt-1">
                    <TrendingUp className="w-3 h-3" /> ↑ 6% this week
                  </p>
                </div>
                <div className="w-12 h-12 rounded-full border-4 border-emerald-500 border-t-emerald-200 transform -rotate-45" />
              </div>
            </div>

            {/* Card 3: Skills Match */}
            <div className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-sm space-y-3 flex flex-col justify-between">
              <div className="flex justify-between items-center text-xs">
                <span className="font-bold text-slate-700">Skills Match</span>
                <span className="text-[10px] font-bold text-amber-700 bg-amber-50 px-2 py-0.5 rounded-full">Good</span>
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-3xl font-extrabold text-slate-900">{skillsMatch}%</span>
                  <p className="text-[11px] font-semibold text-emerald-700 flex items-center gap-1 mt-1">
                    <TrendingUp className="w-3 h-3" /> ↑ 7% this week
                  </p>
                </div>
                <div className="w-12 h-12 rounded-full border-4 border-amber-500 border-t-amber-200 transform -rotate-45" />
              </div>
            </div>

            {/* Card 4: Interview Readiness */}
            <div className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-sm space-y-3 flex flex-col justify-between">
              <div className="flex justify-between items-center text-xs">
                <span className="font-bold text-slate-700">Interview Readiness</span>
                <span className="text-[10px] font-bold text-blue-700 bg-blue-50 px-2 py-0.5 rounded-full">Good</span>
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-3xl font-extrabold text-slate-900">{intReadiness}%</span>
                  <p className="text-[11px] font-semibold text-emerald-700 flex items-center gap-1 mt-1">
                    <TrendingUp className="w-3 h-3" /> ↑ 5% this week
                  </p>
                </div>
                <div className="w-12 h-12 rounded-full border-4 border-blue-500 border-t-blue-200 transform -rotate-45" />
              </div>
            </div>
          </div>

          {/* Section 2: Your Career Overview */}
          <div className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-sm space-y-6">
            <div className="flex items-center justify-between border-b border-slate-100 pb-4">
              <h2 className="text-base font-bold text-slate-900">Your Career Overview</h2>
              <Link href="/dashboard/reports" className="text-xs font-semibold text-[#0F5E4E] hover:underline flex items-center gap-1">
                View Full Report →
              </Link>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Top Strengths */}
              <div className="space-y-3">
                <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider">Top Strengths</h3>
                <div className="space-y-2 text-xs">
                  {[
                    { name: 'Python', level: 'Advanced' },
                    { name: 'Machine Learning', level: 'Advanced' },
                    { name: 'Problem Solving', level: 'Advanced' },
                    { name: 'SQL', level: 'Intermediate' },
                    { name: 'Data Structures', level: 'Intermediate' }
                  ].map((s, idx) => (
                    <div key={idx} className="flex justify-between items-center p-2 rounded-lg bg-slate-50 border border-slate-100">
                      <span className="font-semibold text-slate-800">{s.name}</span>
                      <span className="text-[10px] font-bold text-emerald-700">{s.level}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Top Skill Gaps */}
              <div className="space-y-3">
                <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider">Top Skill Gaps</h3>
                <div className="space-y-2 text-xs">
                  {[
                    { name: 'System Design', prio: 'High', color: 'text-rose-700 bg-rose-50' },
                    { name: 'Cloud (AWS)', prio: 'High', color: 'text-rose-700 bg-rose-50' },
                    { name: 'Docker', prio: 'Medium', color: 'text-amber-700 bg-amber-50' },
                    { name: 'Kubernetes', prio: 'Medium', color: 'text-amber-700 bg-amber-50' },
                    { name: 'CI/CD', prio: 'Low', color: 'text-emerald-700 bg-emerald-50' }
                  ].map((g, idx) => (
                    <div key={idx} className="flex justify-between items-center p-2 rounded-lg bg-slate-50 border border-slate-100">
                      <span className="font-semibold text-slate-800">{g.name}</span>
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${g.color}`}>{g.prio}</span>
                    </div>
                  ))}
                </div>
                <Link href="/dashboard/reports" className="text-[11px] font-semibold text-[#0F5E4E] block text-center pt-1 hover:underline">
                  View Skill Gap Analysis →
                </Link>
              </div>

              {/* Roadmap Progress Donut */}
              <div className="space-y-3 text-center flex flex-col justify-between">
                <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider">Roadmap Progress</h3>
                <div className="relative w-32 h-32 mx-auto flex items-center justify-center">
                  <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
                    <path strokeWidth="3.5" stroke="#e2e8f0" fill="none" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                    <path strokeWidth="3.5" strokeDasharray="42, 100" stroke="#0F5E4E" strokeLinecap="round" fill="none" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                  </svg>
                  <div className="absolute">
                    <span className="text-xl font-extrabold text-slate-900">42%</span>
                    <span className="text-[9px] block text-slate-400 uppercase font-bold">Completed</span>
                  </div>
                </div>
                <div className="space-y-1 text-[11px] text-slate-600 text-left px-2">
                  <div className="flex justify-between"><span>🟢 Completed</span><span className="font-bold">42%</span></div>
                  <div className="flex justify-between"><span>🟠 In Progress</span><span className="font-bold">30%</span></div>
                  <div className="flex justify-between"><span>⚪ Upcoming</span><span className="font-bold">28%</span></div>
                </div>
                <Link href="/dashboard/coach" className="text-[11px] font-semibold text-[#0F5E4E] hover:underline">
                  View Roadmap →
                </Link>
              </div>
            </div>
          </div>

          {/* Section 3: Recommended for You Cards */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-bold text-slate-900">Recommended for You</h2>
              <div className="flex items-center gap-1">
                <button className="p-1 rounded bg-slate-200 text-slate-600 hover:bg-slate-300"><ChevronLeft className="w-4 h-4" /></button>
                <button className="p-1 rounded bg-slate-200 text-slate-600 hover:bg-slate-300"><ChevronRight className="w-4 h-4" /></button>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              
              {/* Card 1: Next Milestone */}
              <div className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-sm space-y-3 flex flex-col justify-between">
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-xs font-bold text-[#0F5E4E]">
                    <Map className="w-4 h-4" /> Next Milestone
                  </div>
                  <h3 className="text-sm font-bold text-slate-900">Learn System Design</h3>
                  <p className="text-xs text-slate-500 leading-relaxed">
                    Important for scaling applications and clearing senior role interviews.
                  </p>
                  <div className="pt-2 text-[11px] text-slate-500 flex justify-between">
                    <span>Estimated Time</span>
                    <span className="font-semibold text-slate-700">3-4 weeks</span>
                  </div>
                  <div className="w-full bg-slate-100 rounded-full h-1.5 overflow-hidden">
                    <div className="bg-[#0F5E4E] h-1.5 w-[20%]" />
                  </div>
                </div>
                <button onClick={() => window.location.href='/dashboard/coach'} className="w-full py-2 rounded-xl bg-emerald-50 border border-emerald-200 text-xs font-bold text-[#0F5E4E] hover:bg-emerald-100 transition-all text-center">
                  Continue Learning →
                </button>
              </div>

              {/* Card 2: Build This Project */}
              <div className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-sm space-y-3 flex flex-col justify-between">
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-xs font-bold text-amber-700">
                    <FolderGit2 className="w-4 h-4" /> Build This Project
                  </div>
                  <h3 className="text-sm font-bold text-slate-900">AI Image Classification API</h3>
                  <p className="text-xs text-slate-500 leading-relaxed">
                    Build and deploy an end-to-end ML API using FastAPI and Docker.
                  </p>
                  <div className="pt-2 text-[11px] text-slate-500 flex justify-between">
                    <span>Impact: <strong className="text-emerald-700">High</strong></span>
                    <span className="font-semibold text-slate-700">2-3 weeks</span>
                  </div>
                </div>
                <button onClick={() => window.location.href='/dashboard/coach'} className="w-full py-2 rounded-xl bg-amber-50 border border-amber-200 text-xs font-bold text-amber-800 hover:bg-amber-100 transition-all text-center">
                  View Project →
                </button>
              </div>

              {/* Card 3: Practice Interview */}
              <div className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-sm space-y-3 flex flex-col justify-between">
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-xs font-bold text-blue-700">
                    <Bot className="w-4 h-4" /> Practice Interview
                  </div>
                  <h3 className="text-sm font-bold text-slate-900">System Design Mock</h3>
                  <p className="text-xs text-slate-500 leading-relaxed">
                    Based on your resume and target role. Improve your system design skills.
                  </p>
                  <div className="pt-2 text-[11px] text-slate-500 flex justify-between">
                    <span>Difficulty: <strong className="text-blue-700">Intermediate</strong></span>
                    <span className="font-semibold text-slate-700">12 Qs</span>
                  </div>
                </div>
                <button onClick={() => window.location.href='/dashboard/coach'} className="w-full py-2 rounded-xl bg-blue-50 border border-blue-200 text-xs font-bold text-blue-800 hover:bg-blue-100 transition-all text-center">
                  Start Mock Interview →
                </button>
              </div>
            </div>
          </div>

          {/* Recent Activity Footer Row */}
          <div className="p-4 rounded-xl bg-white border border-slate-200/80 shadow-sm flex flex-wrap items-center justify-between gap-4 text-xs">
            <div className="flex items-center gap-6 overflow-x-auto">
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-emerald-600" />
                <div><p className="font-bold text-slate-800">Resume analyzed</p><p className="text-[10px] text-slate-400">2 days ago</p></div>
              </div>
              <div className="flex items-center gap-2">
                <Map className="w-4 h-4 text-amber-600" />
                <div><p className="font-bold text-slate-800">Roadmap updated</p><p className="text-[10px] text-slate-400">Yesterday</p></div>
              </div>
              <div className="flex items-center gap-2">
                <FolderGit2 className="w-4 h-4 text-blue-600" />
                <div><p className="font-bold text-slate-800">Project added</p><p className="text-[10px] text-slate-400">3 days ago</p></div>
              </div>
            </div>
            <Link href="/dashboard/reports" className="text-xs font-bold text-[#0F5E4E] hover:underline flex items-center gap-1">
              View All Activity →
            </Link>
          </div>

        </div>

        {/* Right Column: AI Career Coach Panel */}
        <div className="lg:col-span-1">
          <div className="sticky top-6 p-6 rounded-2xl bg-[#0c141c] text-white border border-white/10 shadow-2xl space-y-6 flex flex-col justify-between min-h-[780px]">
            
            <div className="space-y-5">
              {/* Header */}
              <div className="flex items-center justify-between pb-3 border-b border-white/10">
                <div className="flex items-center gap-2 text-emerald-400">
                  <Sparkles className="w-5 h-5" />
                  <h2 className="text-base font-bold text-white">AI Career Coach</h2>
                </div>
                <span className="px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 text-[10px] font-bold border border-emerald-500/30 flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" /> Online
                </span>
              </div>

              <p className="text-xs text-slate-300 leading-relaxed">
                "I've analyzed your progress and prepared some recommendations for you."
              </p>

              {/* 4 Proactive Feed Cards */}
              <div className="space-y-3">
                {proactiveMessages.map((msg) => (
                  <div key={msg.id} className="p-3.5 rounded-xl bg-[#141e29] border border-white/10 hover:border-emerald-500/40 transition-all text-xs text-slate-200 flex items-start gap-3">
                    <span className="text-base shrink-0">{msg.icon}</span>
                    <p className="leading-relaxed">{msg.text}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Quick Action Pills & Input Bar */}
            <div className="space-y-4 pt-4 border-t border-white/10">
              <div className="grid grid-cols-2 gap-2 text-[11px] font-semibold">
                <button onClick={() => handleSendPrompt("Update my roadmap")} className="py-2 px-3 rounded-xl bg-[#141e29] border border-emerald-500/30 text-emerald-400 hover:bg-slate-800 text-center truncate">
                  Update my roadmap
                </button>
                <button onClick={() => handleSendPrompt("Suggest projects")} className="py-2 px-3 rounded-xl bg-[#141e29] border border-emerald-500/30 text-emerald-400 hover:bg-slate-800 text-center truncate">
                  Suggest projects
                </button>
                <button onClick={() => handleSendPrompt("Start interview")} className="py-2 px-3 rounded-xl bg-[#141e29] border border-white/10 text-slate-300 hover:bg-slate-800 text-center truncate">
                  Start interview
                </button>
                <button onClick={() => handleSendPrompt("Explain skill gaps")} className="py-2 px-3 rounded-xl bg-[#141e29] border border-white/10 text-slate-300 hover:bg-slate-800 text-center truncate">
                  Explain skill gaps
                </button>
              </div>

              <div className="relative flex items-center">
                <input
                  type="text"
                  placeholder="Ask anything about your career..."
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSendPrompt(chatInput)}
                  className="w-full bg-[#141e29] border border-white/10 rounded-xl py-3 pl-4 pr-10 text-xs text-white placeholder-slate-500 outline-none focus:border-emerald-500"
                />
                <button
                  onClick={() => handleSendPrompt(chatInput)}
                  className="absolute right-2 p-2 rounded-lg bg-[#0F5E4E] text-white hover:bg-emerald-600 transition-all"
                >
                  <Send className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
