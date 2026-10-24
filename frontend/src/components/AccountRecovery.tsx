'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Button, Input } from '@/components/UIComponents';
import { fetchApi } from '@/lib/api';

export default function AccountRecovery({ mode }: { mode: 'forgot' | 'reset' | 'verify' }) {
  const [token, setToken] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmation, setConfirmation] = useState('');
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  useEffect(() => {
    const value = new URLSearchParams(window.location.hash.slice(1)).get('token')
      || new URLSearchParams(window.location.search).get('token') || '';
    setToken(value);
    // Remove the credential from history after reading it; links use a fragment
    // so reset credentials are not sent to hosting access logs.
    if (value) window.history.replaceState(null, '', window.location.pathname);
  }, []);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (busy) return;
    setError('');
    if (mode !== 'forgot' && !token) { setError('This link is missing its token. Request a new email and open its link.'); return; }
    if (mode === 'reset' && password !== confirmation) { setError('The passwords do not match.'); return; }
    setBusy(true);
    try {
      const endpoint = mode === 'forgot' ? '/auth/forgot-password' : mode === 'reset' ? '/auth/reset-password' : '/auth/verify-email';
      const body = mode === 'forgot' ? { email: email.trim() } : mode === 'reset' ? { token, new_password: password } : { token };
      const result = await fetchApi<{detail: string}>(endpoint, { method: 'POST', body: JSON.stringify(body) });
      setMessage(result.detail); setDone(true); setPassword(''); setConfirmation('');
    } catch (err) { setError(err instanceof Error ? err.message : 'Please try again.'); }
    finally { setBusy(false); }
  }

  const title = mode === 'forgot' ? 'Recover your account' : mode === 'reset' ? 'Choose a new password' : 'Verify your email';
  return <main className="auth-surface min-h-screen flex items-center justify-center p-5">
    <section className="w-full max-w-md rounded-3xl border border-white/10 bg-[#151e29] p-7 space-y-6">
      <Link href="/" className="text-emerald-300 font-semibold">CareerMind AI</Link>
      <h1 className="text-3xl font-semibold">{title}</h1>
      {error && <p role="alert" className="rounded-xl bg-rose-500/10 p-3 text-rose-200">{error}</p>}
      {done ? <p role="status" className="text-emerald-200">{message}</p> : <form onSubmit={submit} className="space-y-5">
        <fieldset disabled={busy} className="space-y-5">
          {mode === 'forgot' && <Input label="Email address" type="email" autoComplete="email" required value={email} onChange={e => setEmail(e.target.value)} />}
          {mode === 'reset' && <>
            <Input label="New password" type="password" autoComplete="new-password" minLength={12} maxLength={1024} required value={password} onChange={e => setPassword(e.target.value)} />
            <Input label="Confirm new password" type="password" autoComplete="new-password" required value={confirmation} onChange={e => setConfirmation(e.target.value)} />
            <p className="text-sm text-slate-400">Use at least 12 characters. Other signed-in sessions will be signed out.</p>
          </>}
          {mode === 'verify' && <p className="text-slate-300">Confirm that you want to verify the email address associated with this link.</p>}
          <Button type="submit" isLoading={busy} className="w-full">{mode === 'forgot' ? 'Send reset link' : mode === 'reset' ? 'Reset password' : 'Verify email'}</Button>
        </fieldset>
      </form>}
      <Link href="/login" className="inline-block text-emerald-300 underline">Back to sign in</Link>
      {mode === 'reset' && <Link href="/forgot-password" className="block text-slate-300 underline">Request a new reset link</Link>}
    </section>
  </main>;
}
