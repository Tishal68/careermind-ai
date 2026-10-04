'use client';

import React, { useState, useEffect } from 'react';
import { fetchApi } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';
import { 
  Sparkles, Settings, Send, Bot, User, CheckCircle2, AlertTriangle, 
  Map, FolderGit2, Mic, ArrowRight, ShieldCheck, Award, Zap, ChevronRight, Target
} from 'lucide-react';

export default function CareerCoachPage() {
  const { user } = useAuth();
  const [messages, setMessages] = useState<any[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    fetchApi<any>('/chat/history')
      .then(d => {
        if (d.messages?.length) {
          setMessages(d.messages);
        } else {
          setMessages([
            {
              role: 'assistant',
              time: '9:30 AM',
              content: `Good morning, ${user?.full_name?.split(' ')[0] || 'Tishal'}! 👋 I analyzed your progress and found some key insights for you today. Here's what I recommend you focus on next.`,
              priority_card: {
                title: 'Your top priority',
                text: `Improve System Design and AWS skills to become a better ${user?.target_job_role || 'AI Engineer'}.`
              }
            }
          ]);
        }
      })
      .catch(() => {});
  }, [user]);

  const handleSend = async (text?: string) => {
    const query = text || input;
    if (!query.trim() || isLoading) return;

    const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    setMessages(prev => [...prev, { role: 'user', time: timeStr, content: query }]);
    if (!text) setInput('');
    setIsLoading(true);

    try {
      const res = await fetchApi<any>('/chat/message', {
        method: 'POST',
        body: JSON.stringify({ content: query })
      });
      setMessages(prev => [
        ...prev, 
        { 
          role: 'assistant', 
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }), 
          content: res.content 
        }
      ]);
    } catch (err) {
      setMessages(prev => [...prev, { role: 'assistant', time: timeStr, content: 'Unable to connect to AI Coach.' }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="p-8 max-w-[1600px] mx-auto space-y-6 bg-[#0e1318] min-h-screen text-slate-100">
      <div className="flex items-center justify-between pb-4 border-b border-white/10">
        <div>
          <div className="flex items-center gap-2 text-emerald-400">
            <Sparkles className="w-5 h-5" />
            <h1 className="text-xl font-extrabold text-white">AI Career Coach</h1>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">Your personal AI mentor guiding your career journey</p>
        </div>
        <button className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-[#151c24] border border-white/10 text-xs font-semibold text-slate-300 hover:text-white">
          <Settings className="w-3.5 h-3.5" /> Coach Settings
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 flex flex-col justify-between h-[780px] bg-[#151c24] border border-white/10 rounded-2xl p-6">
          <div className="flex-1 overflow-y-auto space-y-6 pr-2">
            {messages.map((m, idx) => (
              <div key={idx} className={`flex items-start gap-3.5 ${m.role === 'user' ? 'flex-row-reverse' : ''}`}>
                <div className={`w-8 h-8 rounded-xl flex items-center justify-center text-xs font-bold shrink-0 ${
                  m.role === 'user' ? 'bg-[#0F5E4E] text-white' : 'bg-emerald-950 text-emerald-400 border border-emerald-500/30'
                }`}>
                  {m.role === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                </div>

                <div className={`max-w-[85%] space-y-3 ${m.role === 'user' ? 'text-right' : ''}`}>
                  <div className="flex items-center gap-2 text-[11px] text-slate-400 font-semibold">
                    <span>{m.role === 'user' ? 'You' : 'AI Coach'}</span>
                    <span>•</span>
                    <span>{m.time || '9:30 AM'}</span>
                  </div>

                  <div className={`p-4 rounded-2xl text-xs leading-relaxed text-left ${
                    m.role === 'user' ? 'bg-[#0F5E4E] text-white font-medium' : 'bg-[#0e1318] border border-white/10 text-slate-200'
                  }`}>
                    <p>{m.content}</p>

                    {m.priority_card && (
                      <div className="mt-3 p-3.5 rounded-xl bg-gradient-to-r from-amber-950/40 to-slate-900 border border-amber-500/30 flex items-start gap-3">
                        <span className="text-base">👑</span>
                        <div>
                          <p className="text-[10px] font-bold uppercase text-amber-400">{m.priority_card.title}</p>
                          <p className="text-xs font-semibold text-slate-200 mt-0.5">{m.priority_card.text}</p>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}

            {messages.length === 1 && (
              <div className="flex items-start gap-3.5">
                <div className="w-8 h-8 rounded-xl bg-emerald-950 text-emerald-400 border border-emerald-500/30 flex items-center justify-center shrink-0">
                  <Bot className="w-4 h-4" />
                </div>
                <div className="max-w-[85%] space-y-2">
                  <div className="text-[11px] text-slate-400 font-semibold">AI Coach • 9:31 AM</div>
                  <div className="p-4 rounded-2xl bg-[#0e1318] border border-white/10 text-xs text-slate-200 space-y-3">
                    <p>Based on your goal and current skill gaps, I recommend this learning order for maximum impact.</p>
                    
                    <div className="space-y-2.5">
                      <div className="p-3 rounded-xl bg-[#151c24] border border-white/5 flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <span className="w-6 h-6 rounded-full bg-emerald-500/20 text-emerald-400 font-bold text-xs flex items-center justify-center">1</span>
                          <div>
                            <p className="font-bold text-white">System Design Fundamentals</p>
                            <p className="text-[11px] text-slate-400">High impact for interviews</p>
                          </div>
                        </div>
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">2-3 weeks</span>
                      </div>

                      <div className="p-3 rounded-xl bg-[#151c24] border border-white/5 flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <span className="w-6 h-6 rounded-full bg-amber-500/20 text-amber-400 font-bold text-xs flex items-center justify-center">2</span>
                          <div>
                            <p className="font-bold text-white">AWS Cloud Practitioner</p>
                            <p className="text-[11px] text-slate-400">Boosts your deployment and cloud skills</p>
                          </div>
                        </div>
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/30">3-4 weeks</span>
                      </div>

                      <div className="p-3 rounded-xl bg-[#151c24] border border-white/5 flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <span className="w-6 h-6 rounded-full bg-blue-500/20 text-blue-400 font-bold text-xs flex items-center justify-center">3</span>
                          <div>
                            <p className="font-bold text-white">Docker & Kubernetes</p>
                            <p className="text-[11px] text-slate-400">Essential for deploying AI applications</p>
                          </div>
                        </div>
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/30">2-3 weeks</span>
                      </div>
                    </div>

                    <p className="pt-1 text-slate-300 font-medium">Would you like me to update your roadmap with this plan?</p>
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="pt-4 border-t border-white/10 space-y-3">
            <div className="flex items-center gap-2 overflow-x-auto text-[11px] font-semibold">
              <button onClick={() => handleSend("Update my roadmap with this plan")} className="px-3.5 py-2 rounded-xl bg-[#0e1318] border border-emerald-500/40 text-emerald-400 hover:bg-slate-800 whitespace-nowrap flex items-center gap-1.5">
                <Map className="w-3.5 h-3.5" /> Update my roadmap
              </button>
              <button onClick={() => handleSend("Explain skill gap analysis")} className="px-3.5 py-2 rounded-xl bg-[#0e1318] border border-white/10 text-slate-300 hover:bg-slate-800 whitespace-nowrap flex items-center gap-1.5">
                <AlertTriangle className="w-3.5 h-3.5 text-amber-400" /> Explain skill gap
              </button>
              <button onClick={() => handleSend("Suggest portfolio projects")} className="px-3.5 py-2 rounded-xl bg-[#0e1318] border border-white/10 text-slate-300 hover:bg-slate-800 whitespace-nowrap flex items-center gap-1.5">
                <FolderGit2 className="w-3.5 h-3.5 text-blue-400" /> Suggest projects
              </button>
              <button onClick={() => handleSend("Prepare for interview mock")} className="px-3.5 py-2 rounded-xl bg-[#0e1318] border border-white/10 text-slate-300 hover:bg-slate-800 whitespace-nowrap flex items-center gap-1.5">
                <Mic className="w-3.5 h-3.5 text-rose-400" /> Prepare for interview
              </button>
            </div>

            <div className="space-y-1.5">
              <div className="relative flex items-center">
                <input
                  type="text"
                  placeholder="Ask anything about your career..."
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                  className="w-full bg-[#0e1318] border border-white/10 rounded-xl py-3 pl-4 pr-12 text-xs text-white placeholder-slate-500 outline-none focus:border-emerald-500"
                />
                <button
                  onClick={() => handleSend()}
                  className="absolute right-2 p-2 rounded-lg bg-[#0F5E4E] text-white hover:bg-emerald-600 transition-all"
                >
                  <Send className="w-4 h-4" />
                </button>
              </div>
              <p className="text-[10px] text-slate-500 flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3 text-emerald-500" /> Coach remembers your resume, goals, progress and previous conversations.
              </p>
            </div>
          </div>
        </div>

        <div className="lg:col-span-1 space-y-6">
          <div className="p-6 rounded-2xl bg-[#151c24] border border-white/10 space-y-4">
            <div className="flex items-center gap-2 text-emerald-400">
              <Sparkles className="w-4 h-4" />
              <h2 className="text-sm font-bold text-white">Coach Summary</h2>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              I have analyzed your profile deeply and prepared a personalized plan.
            </p>

            <div className="flex items-center gap-4 pt-2">
              <div className="relative w-24 h-24 flex items-center justify-center shrink-0">
                <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
                  <path strokeWidth="3.5" stroke="#1e293b" fill="none" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                  <path strokeWidth="3.5" strokeDasharray="89, 100" stroke="#10b981" strokeLinecap="round" fill="none" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                </svg>
                <div className="absolute text-center">
                  <span className="text-xl font-extrabold text-white">89</span>
                  <span className="text-[9px] block text-slate-400 font-bold">NexScore</span>
                </div>
              </div>

              <div className="space-y-1.5 text-xs">
                <div className="flex items-center gap-2"><div className="w-2 h-2 rounded-full bg-emerald-400" /><span className="text-slate-300">Strengths:</span><strong className="text-white ml-auto">12</strong></div>
                <div className="flex items-center gap-2"><div className="w-2 h-2 rounded-full bg-amber-400" /><span className="text-slate-300">Skill Gaps:</span><strong className="text-white ml-auto">8</strong></div>
                <div className="flex items-center gap-2"><div className="w-2 h-2 rounded-full bg-blue-400" /><span className="text-slate-300">Opportunities:</span><strong className="text-white ml-auto">6</strong></div>
                <div className="flex items-center gap-2"><div className="w-2 h-2 rounded-full bg-rose-400" /><span className="text-slate-300">Watchouts:</span><strong className="text-white ml-auto">3</strong></div>
              </div>
            </div>

            <button onClick={() => window.location.href='/dashboard/reports'} className="w-full py-2 rounded-xl bg-[#0e1318] border border-white/10 text-xs font-semibold text-slate-300 hover:text-white hover:border-emerald-500/40 transition-all text-center">
              View Full Report →
            </button>
          </div>

          <div className="p-6 rounded-2xl bg-[#151c24] border border-white/10 space-y-4">
            <div className="flex items-center gap-2 text-orange-400">
              <Award className="w-4 h-4" />
              <h2 className="text-sm font-bold text-white">Today's Focus</h2>
            </div>
            <div className="space-y-2.5 text-xs">
              <div className="p-3 rounded-xl bg-[#0e1318] border border-white/5 flex items-center justify-between">
                <div>
                  <p className="font-bold text-white">Learn System Design Basics</p>
                  <p className="text-[10px] text-slate-400">Next milestone</p>
                </div>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-rose-500/10 text-rose-400 border border-rose-500/30">High</span>
              </div>

              <div className="p-3 rounded-xl bg-[#0e1318] border border-white/5 flex items-center justify-between">
                <div>
                  <p className="font-bold text-white">Finish AWS Basics</p>
                  <p className="text-[10px] text-slate-400">Continue learning path</p>
                </div>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/30">Medium</span>
              </div>

              <div className="p-3 rounded-xl bg-[#0e1318] border border-white/5 flex items-center justify-between">
                <div>
                  <p className="font-bold text-white">Solve 2 DSA Problems</p>
                  <p className="text-[10px] text-slate-400">Keep your streak alive</p>
                </div>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/30">Low</span>
              </div>
            </div>
          </div>

          <div className="p-6 rounded-2xl bg-[#151c24] border border-white/10 space-y-4">
            <div className="flex items-center gap-2 text-amber-400">
              <Award className="w-4 h-4" />
              <h2 className="text-sm font-bold text-white">Recent Achievements</h2>
            </div>
            <div className="space-y-2.5 text-xs">
              <div className="flex justify-between items-center p-2.5 rounded-xl bg-[#0e1318] border border-white/5">
                <div>
                  <p className="font-semibold text-slate-200">NexScore improved by 8 points</p>
                  <p className="text-[10px] text-slate-500">2 days ago</p>
                </div>
                <span className="text-xs font-extrabold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded">+8</span>
              </div>
              <div className="flex justify-between items-center p-2.5 rounded-xl bg-[#0e1318] border border-white/5">
                <div>
                  <p className="font-semibold text-slate-200">Completed Docker Basics</p>
                  <p className="text-[10px] text-slate-500">3 days ago</p>
                </div>
                <span className="text-xs font-extrabold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded">+12</span>
              </div>
              <div className="flex justify-between items-center p-2.5 rounded-xl bg-[#0e1318] border border-white/5">
                <div>
                  <p className="font-semibold text-slate-200">Mock interview score improved</p>
                  <p className="text-[10px] text-slate-500">4 days ago</p>
                </div>
                <span className="text-xs font-extrabold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded">+15</span>
              </div>
            </div>
          </div>

          <div className="p-5 rounded-2xl bg-gradient-to-br from-emerald-950/40 to-[#151c24] border border-emerald-500/30 text-xs space-y-2">
            <p className="font-serif italic text-emerald-300 leading-relaxed">
              "Consistency is your superpower. Keep showing up, and results will follow."
            </p>
            <p className="text-[10px] text-slate-400 font-semibold">— NexPath AI Coach</p>
          </div>
        </div>
      </div>
    </div>
  );
}
