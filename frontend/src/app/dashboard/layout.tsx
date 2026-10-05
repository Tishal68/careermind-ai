"use client";

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Compass, Target, Bot, FileText } from 'lucide-react';

const items = [
  { title: 'Role match', href: '/dashboard', icon: Target },
  { title: 'Career coach', href: '/dashboard/coach', icon: Bot },
  { title: 'My resumes', href: '/dashboard/resume', icon: FileText },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  return <div className="min-h-screen bg-[#0b121b] text-slate-100">
    <header className="border-b border-white/10 bg-[#0b121b] sticky top-0 z-20">
      <div className="max-w-6xl mx-auto px-4 sm:px-8 py-4 flex flex-wrap items-center justify-between gap-4">
        <Link href="/dashboard" className="flex items-center gap-2 font-bold text-lg"><Compass className="text-emerald-400" />CareerMind AI</Link>
        <nav aria-label="Main navigation" className="flex gap-1 sm:gap-3">
          {items.map(({title, href, icon: Icon}) => <Link key={href} href={href} className={`flex items-center gap-2 text-xs sm:text-sm rounded-lg px-3 py-2 ${pathname === href ? 'bg-emerald-500/15 text-emerald-300' : 'text-slate-400 hover:text-white'}`}><Icon className="w-4 h-4" />{title}</Link>)}
        </nav>
      </div>
    </header>
    <main>{children}</main>
  </div>;
}
