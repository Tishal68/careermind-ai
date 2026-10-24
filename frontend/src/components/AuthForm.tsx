'use client';

import { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Input, Button } from '@/components/UIComponents';
import { useAuth } from '@/context/AuthContext';
import { fetchApi } from '@/lib/api';
import { ArrowRight, Check, Compass, Eye, EyeOff, FileText, Target, TrendingUp } from 'lucide-react';

export default function AuthForm({ register = false }: { register?: boolean }) {
  const router = useRouter();
  const { user, isLoading: checking, sessionError, retrySession, login, logout } = useAuth();
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [password, setPassword] = useState('');
  const [visible, setVisible] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const submitting = useRef(false);
  const alert = useRef<HTMLDivElement>(null);
  useEffect(() => { if (user) router.replace('/dashboard'); }, [user, router]);
  useEffect(() => { if (error) alert.current?.focus(); }, [error]);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (submitting.current) return;
    submitting.current = true; setBusy(true); setError('');
    try {
      const result = await fetchApi<{ access_token: string; user: any }>(register ? '/auth/register' : '/auth/login', {
        method: 'POST', body: JSON.stringify({ email: email.trim(), password, ...(register ? { full_name: name.trim() } : {}) }),
      });
      login(result.access_token, result.user); router.replace('/dashboard');
    } catch (err: any) { setError(err.message || 'Please try again.'); }
    finally { submitting.current = false; setBusy(false); }
  }

  return <main className="auth-surface min-h-screen px-5 py-8 sm:px-10 flex flex-col">
    <Link href="/" className="inline-flex items-center gap-2 text-lg font-bold w-fit"><Compass className="text-emerald-400" />CareerMind AI</Link>
    <div className="w-full max-w-5xl mx-auto flex-1 grid lg:grid-cols-2 gap-10 lg:gap-20 items-center py-10">
      <section className="hidden lg:block space-y-8">
        <span className="inline-flex rounded-full border border-emerald-400/20 bg-emerald-400/10 px-4 py-2 text-xs font-semibold tracking-wide text-emerald-300">YOUR NEXT CHAPTER STARTS HERE</span>
        <h1 className="text-5xl font-semibold leading-tight tracking-tight">A clearer path to<br /><span className="text-emerald-400">your next role.</span></h1>
        <p className="text-slate-400 text-lg max-w-sm">Turn your experience into a practical plan for the work you want to do.</p>
        <div className="space-y-5">{[[FileText, 'Start with your experience', 'Upload your resume once.'], [Target, 'Find where you fit', 'Compare your skills with role requirements.'], [TrendingUp, 'Know what to learn next', 'Build a focused plan with your career coach.']].map(([Icon, title, text]: any) => <div key={title} className="flex gap-4"><div className="rounded-xl border border-white/10 bg-white/5 p-3 h-fit"><Icon className="w-5 h-5 text-emerald-300" /></div><div><h2 className="font-medium">{title}</h2><p className="text-sm text-slate-400 mt-1">{text}</p></div></div>)}</div>
      </section>
      <section className="w-full max-w-md mx-auto rounded-3xl border border-white/10 bg-[#151e29] p-6 sm:p-9 shadow-xl">
        <p className="text-xs font-semibold uppercase tracking-widest text-emerald-400 mb-3">{register ? 'Get started' : 'Your workspace'}</p>
        <h2 className="text-3xl font-semibold tracking-tight">{register ? 'Create your account' : 'Welcome back'}</h2>
        <p className="text-sm text-slate-400 mt-3 mb-7">{register ? 'Save your resume, explore roles, and track your next steps.' : 'Sign in to continue your career plan.'}</p>
        {checking || user ? <p role="status" className="py-8 text-slate-300">Opening your workspace…</p> : sessionError ? <div className="space-y-4"><p role="alert">{sessionError}</p><Button onClick={retrySession}>Try again</Button><button onClick={logout} className="ml-4 underline">Use another account</button></div> : <>
          {error && <div ref={alert} tabIndex={-1} role="alert" className="mb-5 rounded-xl border border-rose-400/30 bg-rose-400/10 p-4 text-sm text-rose-200">{error}</div>}
          <form onSubmit={submit} className="space-y-5" aria-busy={busy}>
            <fieldset disabled={busy} className="space-y-5">
              {register && <Input label="Full name" name="name" autoComplete="name" value={name} onChange={e => setName(e.target.value)} maxLength={150} required />}
              <Input label="Email address" name="email" type="email" autoComplete="email" autoCapitalize="none" spellCheck={false} placeholder="you@example.com" value={email} onChange={e => setEmail(e.target.value)} required />
              <div className="space-y-2">
                <div className="relative"><Input label="Password" name="password" type={visible ? 'text' : 'password'} autoComplete={register ? 'new-password' : 'current-password'} minLength={register ? 12 : undefined} maxLength={1024} className="pr-16" value={password} onChange={e => setPassword(e.target.value)} required /><button type="button" aria-label={visible ? 'Hide password' : 'Show password'} aria-pressed={visible} onClick={() => setVisible(!visible)} className="absolute right-1 bottom-1 rounded-lg p-3 text-slate-300 hover:bg-white/10">{visible ? <EyeOff size={20} /> : <Eye size={20} />}</button></div>
                {register && <p className={`text-xs flex items-center gap-2 ${password.length >= 12 ? 'text-emerald-300' : 'text-slate-400'}`}><Check size={14} />Use at least 12 characters.</p>}
              </div>
              <Button type="submit" size="lg" className="w-full" isLoading={busy} rightIcon={<ArrowRight size={18} />}>{busy ? (register ? 'Creating account…' : 'Signing in…') : (register ? 'Create account' : 'Sign in')}</Button>
            </fieldset>
            {busy && <p role="status" className="text-xs text-slate-400">Connecting securely. The first visit may take a moment.</p>}
          </form>
          {!register && <Link href="/forgot-password" className="mt-5 block text-sm text-emerald-300 underline">Forgot password?</Link>}
          <p className="text-sm text-center text-slate-400 mt-7">{register ? 'Already have an account?' : 'New to CareerMind?'} <Link href={register ? '/login' : '/register'} className="text-emerald-300 hover:text-emerald-200 font-semibold underline underline-offset-4">{register ? 'Sign in' : 'Create account'}</Link></p>
        </>}
      </section>
    </div>
    <p className="text-center text-xs text-slate-500">Your experience. Your direction. Your next step.</p>
  </main>;
}
