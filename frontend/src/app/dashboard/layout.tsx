"use client";

import Link from 'next/link';
import { useEffect } from 'react';
import { useAuth } from '@/context/AuthContext';
import { usePathname, useRouter } from 'next/navigation';
import { Compass, Target, Bot, FileText, ListChecks, MessagesSquare, Settings2, LogOut, ArrowUpRight, FolderOpen } from 'lucide-react';
import DashboardLoading from './loading';

const items = [
  { title: 'Role match', href: '/dashboard', icon: Target },
  { title: 'Career coach', href: '/dashboard/coach', icon: Bot },
  { title: 'My resumes', href: '/dashboard/resume', icon: FileText },
  { title: 'Reports', href: '/dashboard/reports', icon: FolderOpen },
  { title: 'Action plan', href: '/dashboard/roadmap', icon: ListChecks },
  { title: 'Interview practice', href: '/dashboard/interview', icon: MessagesSquare },
  { title: 'Settings', href: '/dashboard/settings', icon: Settings2 },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, isLoading, sessionError, retrySession, logout } = useAuth();
  useEffect(() => { if (!isLoading && !user && !sessionError) router.replace('/login'); }, [isLoading, user, sessionError, router]);
  if (sessionError) return <div className="max-w-md mx-auto p-8 space-y-5"><h1 className="text-2xl font-bold">Let’s reconnect</h1><p role="alert" className="text-slate-300">{sessionError}</p><button onClick={retrySession} className="rounded-xl bg-emerald-600 px-5 py-3 font-semibold">Try again</button><button onClick={logout} className="ml-4 underline">Sign out</button></div>;
  if (isLoading || !user) return <DashboardLoading />;

  const activeTitle = items.find(item => item.href === pathname)?.title || 'Workspace';
  return <div className="workspace-shell min-h-screen text-slate-100 lg:pl-60">
    <a href="#main-content" className="skip-link">Skip to content</a>
    <aside className="workspace-sidebar hidden lg:flex fixed inset-y-0 left-0 w-60 flex-col overflow-y-auto border-r border-white/10 p-5 z-30">
      <Link href="/dashboard" className="flex items-center gap-3 py-3 font-semibold tracking-tight"><span className="brand-mark"><Compass size={22} /></span>CareerMind AI</Link>
      <p className="mt-10 mb-3 px-3 text-[10px] font-semibold tracking-[0.2em] text-slate-500 uppercase">Your workspace</p>
      <nav aria-label="Main navigation" className="space-y-1">
        {items.map(({title, href, icon: Icon}) => <Link key={href} href={href} aria-current={pathname === href ? 'page' : undefined} className="workspace-nav-link"><Icon size={18} aria-hidden="true" />{title}{pathname === href && <span className="ml-auto h-1.5 w-1.5 rounded-full bg-emerald-300" />}</Link>)}
      </nav>
      <div className="mt-auto pt-8">
        <div className="rounded-2xl border border-emerald-300/10 bg-emerald-300/5 p-4 mb-5"><p className="text-sm font-medium text-emerald-200">One step at a time.</p><p className="text-xs leading-relaxed text-slate-400 mt-2">Turn your next report into a practical learning plan.</p><Link href="/dashboard/roadmap" className="inline-flex items-center gap-2 mt-3 text-xs font-semibold text-emerald-300">Open your plan<ArrowUpRight size={14} /></Link></div>
        <button onClick={logout} className="workspace-nav-link w-full"><LogOut size={18} />Sign out</button>
      </div>
    </aside>
    <header className="workspace-topbar sticky top-0 z-20 border-b border-white/10">
      <div className="px-4 sm:px-8 h-16 flex items-center justify-between gap-4">
        <Link href="/dashboard" className="lg:hidden flex items-center gap-2 font-semibold"><span className="brand-mark"><Compass size={20} /></span>CareerMind AI</Link>
        <p className="hidden lg:block text-sm text-slate-400">Workspace <span className="mx-3 text-slate-600">/</span><span className="text-slate-200">{activeTitle}</span></p>
        <div className="flex items-center gap-3 min-w-0"><span className="hidden sm:block text-sm text-slate-300 truncate max-w-48">{user.full_name || 'Your workspace'}</span><span aria-hidden="true" className="hidden lg:grid w-9 h-9 place-items-center rounded-full bg-emerald-300/10 border border-emerald-300/20 text-sm text-emerald-200">{(user.full_name || user.email || 'C').slice(0, 1).toUpperCase()}</span><button onClick={logout} className="lg:hidden min-h-11 px-2 text-xs text-slate-300">Sign out</button></div>
      </div>
      <nav aria-label="Mobile navigation" className="lg:hidden flex overflow-x-auto gap-1 px-4 pb-3 overscroll-x-contain">
        {items.map(({title, href, icon: Icon}) => <Link key={href} href={href} aria-current={pathname === href ? 'page' : undefined} className="workspace-nav-link shrink-0 whitespace-nowrap"><Icon size={16} aria-hidden="true" />{title}</Link>)}
      </nav>
    </header>
    <main key={user.id} id="main-content" tabIndex={-1} className="min-w-0 outline-none">{children}</main>
  </div>;
}
