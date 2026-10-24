"use client";

import { useRef, useState } from 'react';
import { KeyRound } from 'lucide-react';
import { Card, Button, Input } from '@/components/UIComponents';
import { useAuth } from '@/context/AuthContext';
import { fetchApi } from '@/lib/api';

export default function PasswordSettings() {
  const { login } = useAuth();
  const [current, setCurrent] = useState('');
  const [password, setPassword] = useState('');
  const [confirmation, setConfirmation] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const submitting = useRef(false);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (submitting.current) return;
    setError(''); setSuccess(false);
    if (password !== confirmation) { setError('The new passwords do not match.'); return; }
    if (password === current) { setError('Choose a different new password.'); return; }
    submitting.current = true; setBusy(true);
    try {
      const result = await fetchApi<any>('/auth/change-password', {
        method: 'POST', body: JSON.stringify({current_password: current, new_password: password}),
      });
      login(result.access_token, result.user);
      setCurrent(''); setPassword(''); setConfirmation(''); setSuccess(true);
    } catch (err: any) {
      setError([408, 499, 503].includes(err.status)
        ? 'The connection was interrupted, so we could not confirm the change. Try signing in with your new password before retrying.'
        : err.message || 'Could not change your password. Please try again.');
    } finally { submitting.current = false; setBusy(false); }
  }

  return <Card className="space-y-5">
    <div><h2 className="flex items-center gap-2 font-semibold"><KeyRound size={18} className="text-emerald-300" />Change password</h2><p className="mt-2 text-sm text-slate-400">Confirm your current password to set a new one. Previous login sessions will be invalidated; this browser will stay signed in.</p></div>
    {success && <p role="status" className="rounded-xl bg-emerald-400/10 border border-emerald-400/20 p-3 text-sm text-emerald-200">Password changed. Previous login sessions can no longer access your account.</p>}
    {error && <p role="alert" className="text-sm text-rose-300">{error}</p>}
    <form onSubmit={submit} aria-busy={busy} className="space-y-4">
      <fieldset disabled={busy} className="space-y-4">
        <Input label="Current password" type="password" autoComplete="current-password" value={current} onChange={e => setCurrent(e.target.value)} required maxLength={1024} />
        <Input label="New password" type="password" autoComplete="new-password" value={password} onChange={e => setPassword(e.target.value)} required minLength={12} maxLength={1024} />
        <Input label="Confirm new password" type="password" autoComplete="new-password" value={confirmation} onChange={e => setConfirmation(e.target.value)} required minLength={12} maxLength={1024} />
        <p className="text-xs text-slate-400">Use at least 12 characters. Password managers and pasted passphrases are supported.</p>
        <Button type="submit" isLoading={busy}>{busy ? 'Changing password…' : 'Change password'}</Button>
      </fieldset>
    </form>
  </Card>;
}
