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
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
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

  return (
    <div className="min-h-[85vh] flex items-center justify-center px-4 relative">
      <Card glass className="w-full max-w-md p-8 relative z-10">
        <div className="text-center mb-6">
          <div className="inline-flex p-3 rounded-2xl bg-indigo-600/10 border border-indigo-500/20 text-indigo-400 mb-4"><Sparkles className="w-6 h-6" /></div>
          <h1 className="text-2xl font-bold text-white mb-2">Welcome Back</h1>
          <p className="text-sm text-slate-400">Sign in to access your CareerMind AI workspace</p>
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
