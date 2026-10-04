'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Card, Input, Button } from '@/components/UIComponents';
import { fetchApi } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';
import { Mail, Lock, Sparkles, ArrowRight, Zap, ShieldCheck } from 'lucide-react';

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [email, setEmail] = useState('demo@careermind.ai');
  const [password, setPassword] = useState('Password123!');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setError('');
    setIsLoading(true);
    try {
      const response = await fetchApi<{ access_token: string; user: any }>('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      });
      login(response.access_token, response.user);
      router.push('/dashboard');
    } catch (err: any) {
      setError(err.message || 'Login failed. Please check your credentials.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDemoLogin = (demoEmail: string, demoPass: string) => {
    setEmail(demoEmail);
    setPassword(demoPass);
    setTimeout(() => {
      handleSubmit();
    }, 100);
  };

  return (
    <div className="min-h-[85vh] flex items-center justify-center px-4 relative">
      <Card glass className="w-full max-w-md p-8 relative z-10">
        <div className="text-center mb-6">
          <div className="inline-flex p-3 rounded-2xl bg-indigo-600/10 border border-indigo-500/20 text-indigo-400 mb-4"><Sparkles className="w-6 h-6" /></div>
          <h1 className="text-2xl font-bold text-white mb-2">Welcome Back</h1>
          <p className="text-sm text-slate-400">Sign in to access your CareerMind AI workspace</p>
        </div>

        {/* Quick Access Account Banners */}
        <div className="mb-6 space-y-2">
          <div className="p-3 rounded-xl bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-between text-xs text-indigo-300">
            <div>
              <p className="font-semibold text-white">Demo User Account</p>
              <p className="text-slate-400">demo@careermind.ai</p>
            </div>
            <Button type="button" size="sm" variant="outline" onClick={() => handleDemoLogin('demo@careermind.ai', 'Password123!')} leftIcon={<Zap className="w-3.5 h-3.5" />}>
              Demo Login
            </Button>
          </div>

          <div className="p-3 rounded-xl bg-purple-500/10 border border-purple-500/30 flex items-center justify-between text-xs text-purple-300">
            <div>
              <p className="font-semibold text-white flex items-center gap-1">
                <ShieldCheck className="w-3.5 h-3.5 text-purple-400" /> Special Admin Access
              </p>
              <p className="text-slate-400">admin@careermind.ai</p>
            </div>
            <Button type="button" size="sm" variant="outline" className="border-purple-500/40 text-purple-300 hover:bg-purple-500/20" onClick={() => handleDemoLogin('admin@careermind.ai', 'AdminPass123!')} leftIcon={<ShieldCheck className="w-3.5 h-3.5" />}>
              Admin Login
            </Button>
          </div>
        </div>

        {error && <div className="mb-6 p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs text-center font-medium">{error}</div>}

        <form onSubmit={handleSubmit} className="space-y-5">
          <Input label="Email Address (Mail ID)" type="email" placeholder="you@gmail.com" value={email} onChange={(e) => setEmail(e.target.value)} leftIcon={<Mail className="w-4 h-4" />} required />
          <Input label="Password" type="password" placeholder="••••••••" value={password} onChange={(e) => setPassword(e.target.value)} leftIcon={<Lock className="w-4 h-4" />} required />
          <Button type="submit" className="w-full mt-2" isLoading={isLoading} rightIcon={<ArrowRight className="w-4 h-4" />}>Sign In</Button>
        </form>

        <p className="text-xs text-center text-slate-400 mt-6">
          Don't have an account?{' '}
          <Link href="/register" className="text-indigo-400 hover:text-indigo-300 font-semibold underline underline-offset-4">
            Create new account with Email ID
          </Link>
        </p>
      </Card>
    </div>
  );
}
