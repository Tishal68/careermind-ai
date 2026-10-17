"use client";

import Link from 'next/link';
import { useEffect } from 'react';
import { useAuth } from '@/context/AuthContext';
import { usePathname, useRouter } from 'next/navigation';
import { Compass, Target, Bot, FileText } from 'lucide-react';

const items = [
  { title: 'Role match', href: '/dashboard', icon: Target },
  { title: 'Career coach', href: '/dashboard/coach', icon: Bot },
  { title: 'My resumes', href: '/dashboard/resume', icon: FileText },
  { title: 'Reports', href: '/dashboard/reports', icon: FileText },
  { title: 'Action plan', href: '/dashboard/roadmap', icon: Target },
  { title: 'Settings', href: '/dashboard/settings', icon: Compass },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, isLoading, sessionError, retrySession, logout } = useAuth();
  useEffect(() => { if (!isLoading && !user && !sessionError) router.replace('/login'); }, [isLoading, user, sessionError, router]);
  if (sessionError) return <div className="max-w-md mx-auto p-8 space-y-5"><h1 className="text-2xl font-bold">Let’s reconnect</h1><p role="alert" className="text-slate-300">{sessionError}</p><button onClick={retrySession} className="rounded-xl bg-emerald-600 px-5 py-3 font-semibold">Try again</button><button onClick={logout} className="ml-4 underline">Sign out</button></div>;
  if (isLoading || !user) return <p role="status" className="p-8">Loading your account…</p>;

  return <div className="min-h-screen bg-[#0b121b] text-slate-100">
    <a href="#main-content" className="sr-only focus:not-sr-only focus:block focus:p-4">Skip to content</a>
    <header className="border-b border-white/10 bg-[#0b121b] sticky top-0 z-20">
      <div className="max-w-6xl mx-auto px-4 sm:px-8 py-4 flex flex-wrap items-center justify-between gap-4">
        <Link href="/dashboard" className="flex items-center gap-2 font-bold text-lg"><Compass className="text-emerald-400" />CareerMind AI</Link>
        <nav aria-label="Main navigation" className="flex flex-wrap gap-1 sm:gap-3">
          {items.map(({title, href, icon: Icon}) => <Link key={href} href={href} aria-current={pathname === href ? 'page' : undefined} className={`flex items-center gap-2 text-xs sm:text-sm rounded-lg px-3 py-2 ${pathname === href ? 'bg-emerald-500/15 text-emerald-300' : 'text-slate-400 hover:text-white'}`}><Icon className="w-4 h-4" />{title}</Link>)}
          <button onClick={logout} className="px-3 py-2 text-sm text-slate-300">Sign out</button>
        </nav>
      </div>
    </header>
    <main key={user.id} id="main-content">{children}</main>
  </div>;
}
