'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Card, Button, Input } from '@/components/UIComponents';
import JobRoleInput from '@/components/JobRoleInput';
import PasswordSettings from '@/components/PasswordSettings';
import { fetchApi } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';
import { Settings, Target, Cpu, Key, Trash2, CheckCircle2, ShieldCheck } from 'lucide-react';

export default function SettingsPage() {
  const { user, updateTargetRole } = useAuth();
  const edited = useRef(false);
  const [targetRole, setTargetRole] = useState(user?.target_job_role || 'AI Engineer');
  const [preferredModel, setPreferredModel] = useState('Loading…');
  const [error, setError] = useState('');
  const [provider, setProvider] = useState<any>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');

  useEffect(() => {
    const controller = new AbortController();
    fetchApi<any>('/user/settings', {signal: controller.signal})
      .then(data => {
        setProvider(data);
        if (!edited.current && data.target_job_role) setTargetRole(data.target_job_role);
        if (data.preferred_ai_model) setPreferredModel(data.preferred_ai_model);
      })
      .catch(err => { if (!controller.signal.aborted) setError(err.message); });
    return () => controller.abort();
  }, []);

  const handleSaveSettings = async (e: React.FormEvent) => {
    e.preventDefault();
    if (targetRole.trim().length < 2) { setError('Enter a job title of 2 to 100 characters.'); return; }
    setIsSaving(true);
    setSuccessMsg(''); setError('');
    try {
      const saved = await fetchApi<any>('/user/settings', {
        method: 'PUT',
        body: JSON.stringify({
          target_job_role: targetRole.trim(),

        })
      });
      if (user && saved.user?.target_job_role) updateTargetRole(user.id, saved.user.target_job_role);
      setSuccessMsg('CareerMind settings saved successfully.');
    } catch (err: any) {
      setError(err.message || 'Could not save settings.');
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
        <p className="text-xs text-slate-400 mt-1">Set your career goal and view the configured research model.</p>
      </div>

      {error && <p role="alert" className="text-rose-300">{error}</p>}
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
            <label htmlFor="settings-role" className="block text-xs font-semibold text-slate-300 mb-1.5">Target Job Role</label>
            <JobRoleInput id="settings-role" value={targetRole} onChange={value => { edited.current = true; setTargetRole(value); setSuccessMsg(''); }} />
          </div>
        </Card>

        {/* AI Model Selection */}
        <Card className="p-6 bg-[#0b1320] border-white/10 space-y-4">
          <h2 className="text-sm font-bold text-white flex items-center gap-2">
            <Cpu className="w-4 h-4 text-orange-400" /> Configured AI Model
          </h2>
          <p className="text-base text-emerald-300 break-words">{preferredModel}</p>
          <p className="text-sm text-slate-400">Research uses this service-configured Ollama model. Contact the administrator to change it.</p>
          {provider && <p className="text-sm text-slate-400">Coach: {provider.coach_provider} / {provider.coach_model}. Provider fallback {provider.fallback_enabled ? 'enabled' : 'disabled'}.</p>}
        </Card>

        <Button type="submit" isLoading={isSaving} leftIcon={<CheckCircle2 className="w-4 h-4" />}>
          Save Preferences
        </Button>
      </form>
      <PasswordSettings />
    </div>
  );
}
