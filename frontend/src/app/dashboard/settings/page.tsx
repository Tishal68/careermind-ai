'use client';

import React, { useState, useEffect } from 'react';
import { Card, Button, Input } from '@/components/UIComponents';
import { fetchApi } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';
import { Settings, Target, Cpu, Key, Trash2, CheckCircle2, ShieldCheck } from 'lucide-react';

export default function SettingsPage() {
  const { user } = useAuth();
  const [targetRole, setTargetRole] = useState(user?.target_job_role || 'AI Engineer');
  const [preferredModel, setPreferredModel] = useState(user?.preferred_ai_model || 'gemini-2.5-flash');
  const [apiKey, setApiKey] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');

  useEffect(() => {
    fetchApi<any>('/user/settings')
      .then(data => {
        if (data.target_job_role) setTargetRole(data.target_job_role);
        if (data.preferred_ai_model) setPreferredModel(data.preferred_ai_model);
      })
      .catch(() => {});
  }, []);

  const handleSaveSettings = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setSuccessMsg('');
    try {
      await fetchApi('/user/settings', {
        method: 'PUT',
        body: JSON.stringify({
          target_job_role: targetRole,
          preferred_ai_model: preferredModel,
        })
      });
      setSuccessMsg('NexPath settings saved successfully.');
    } catch {
      alert('Error saving settings.');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-6 py-10 space-y-8">
      <div className="pb-4 border-b border-white/10">
        <h1 className="text-2xl font-extrabold text-white flex items-center gap-2.5">
          <Settings className="w-6 h-6 text-emerald-400" /> Platform Settings & Preferences
        </h1>
        <p className="text-xs text-slate-400 mt-1">Configure your career goal, preferred AI intelligence model, and session settings.</p>
      </div>

      {successMsg && (
        <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

      <form onSubmit={handleSaveSettings} className="space-y-6">
        {/* Career Goal Card */}
        <Card className="p-6 bg-[#0b1320] border-white/10 space-y-4">
          <h2 className="text-sm font-bold text-white flex items-center gap-2">
            <Target className="w-4 h-4 text-emerald-400" /> Primary Career Goal
          </h2>
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">Target Job Role</label>
            <select
              value={targetRole}
              onChange={(e) => setTargetRole(e.target.value)}
              className="w-full bg-[#070c14] border border-white/10 rounded-xl px-4 py-2.5 text-xs text-white focus:border-emerald-500 outline-none"
            >
              <option value="AI Engineer">AI Engineer</option>
              <option value="Machine Learning Engineer">Machine Learning Engineer</option>
              <option value="Data Scientist">Data Scientist</option>
              <option value="Generative AI Engineer">Generative AI Engineer</option>
              <option value="Software Development">Software Developer</option>
            </select>
          </div>
        </Card>

        {/* AI Model Selection */}
        <Card className="p-6 bg-[#0b1320] border-white/10 space-y-4">
          <h2 className="text-sm font-bold text-white flex items-center gap-2">
            <Cpu className="w-4 h-4 text-orange-400" /> Preferred AI Model
          </h2>
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">Select Model Engine</label>
            <select
              value={preferredModel}
              onChange={(e) => setPreferredModel(e.target.value)}
              className="w-full bg-[#070c14] border border-white/10 rounded-xl px-4 py-2.5 text-xs text-white focus:border-emerald-500 outline-none"
            >
              <option value="gemini-2.5-flash">Google Gemini 2.5 Flash (Recommended - Ultra Fast)</option>
              <option value="gemini-1.5-pro">Google Gemini 1.5 Pro (Deep Reasoning)</option>
              <option value="gemini-2.0-flash">Google Gemini 2.0 Flash</option>
            </select>
          </div>
        </Card>

        <Button type="submit" isLoading={isSaving} leftIcon={<CheckCircle2 className="w-4 h-4" />}>
          Save Preferences
        </Button>
      </form>
    </div>
  );
}
