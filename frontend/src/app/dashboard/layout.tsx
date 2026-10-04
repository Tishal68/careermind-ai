'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { 
  LayoutDashboard, 
  Bot, 
  FileCheck2, 
  Settings, 
  ShieldCheck,
  Compass,
  FileText,
  Target,
  Briefcase,
  LogOut,
  TrendingUp
} from 'lucide-react';

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  const navItems = [
    { label: 'Dashboard', href: '/dashboard', icon: <LayoutDashboard className="w-4 h-4" /> },
    { label: 'Career Coach', href: '/dashboard/coach', icon: <Bot className="w-4 h-4" /> },
    { label: 'Reports', href: '/dashboard/reports', icon: <FileCheck2 className="w-4 h-4" /> },
    { label: 'Settings', href: '/dashboard/settings', icon: <Settings className="w-4 h-4" /> },
  ];

  if (user?.is_superuser) {
    navItems.push({
      label: 'Admin Portal', href: '/dashboard/admin', icon: <ShieldCheck className="w-4 h-4 text-amber-400" />
    });
  }

  return (
    <div className="flex h-screen bg-[#070c14] overflow-hidden">
      {/* NexPath Sidebar (Matching Mockup 1 & 2) */}
      <aside className="w-64 border-r border-white/10 bg-[#070c14] shrink-0 hidden lg:flex flex-col justify-between p-5 overflow-y-auto">
        <div className="space-y-6">
          {/* Logo & Tagline */}
          <Link href="/dashboard" className="flex items-center gap-3 group px-2 pt-1">
            <div className="p-2 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 group-hover:bg-emerald-500/20 transition-all">
              <Compass className="w-6 h-6" />
            </div>
            <div>
              <span className="text-xl font-extrabold text-white tracking-tight">NexPath</span>
              <p className="text-[10px] font-medium text-slate-400">Your AI Career Operating System</p>
            </div>
          </Link>

          {/* Navigation Links */}
          <nav className="space-y-1">
            {navItems.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all ${
                    isActive
                      ? 'bg-[#0F5E4E] text-white shadow-md shadow-emerald-950/50'
                      : 'text-slate-400 hover:text-white hover:bg-slate-900/60'
                  }`}
                >
                  {item.icon}
                  {item.label}
                </Link>
              );
            })}
          </nav>

          {/* CURRENT SESSION Widget (Matching Mockup 1) */}
          <div className="space-y-3 pt-2 border-t border-white/10">
            <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest px-2">CURRENT SESSION</p>
            <div className="p-3.5 rounded-xl bg-[#0b131c] border border-white/10 space-y-2 text-xs">
              <div className="flex items-center gap-2 text-slate-300">
                <FileText className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                <div className="truncate">
                  <p className="text-[10px] text-slate-500 font-bold uppercase">Resume</p>
                  <p className="font-semibold text-slate-200 truncate">Tishal_Mohan_Resume.pdf</p>
                </div>
              </div>
              <div className="flex items-center gap-2 text-slate-300">
                <Target className="w-3.5 h-3.5 text-orange-400 shrink-0" />
                <div>
                  <p className="text-[10px] text-slate-500 font-bold uppercase">Role</p>
                  <p className="font-semibold text-slate-200">{user?.target_job_role || 'AI Engineer'}</p>
                </div>
              </div>
              <div className="flex items-center gap-2 text-slate-300">
                <Briefcase className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                <div>
                  <p className="text-[10px] text-slate-500 font-bold uppercase">Experience</p>
                  <p className="font-semibold text-slate-200">1.5 Years</p>
                </div>
              </div>
              <button onClick={() => window.location.href='/dashboard/reports'} className="w-full mt-2 py-1.5 rounded-lg bg-slate-900 border border-white/10 text-[11px] font-semibold text-slate-300 hover:text-white hover:border-emerald-500/40 transition-all text-center">
                View Full Profile →
              </button>
            </div>
          </div>

          {/* NexScore Sparkline Widget Card (Matching Mockup 1 & 2) */}
          <div className="p-4 rounded-xl bg-gradient-to-br from-[#0d1620] to-[#070c14] border border-emerald-500/30 space-y-2">
            <div className="flex justify-between items-center text-xs">
              <span className="font-bold text-slate-300">NexScore</span>
              <span className="text-[10px] text-emerald-400 font-semibold bg-emerald-500/10 px-1.5 py-0.5 rounded">Excellent</span>
            </div>
            <div className="flex items-baseline gap-1">
              <span className="text-2xl font-extrabold text-white">89</span>
              <span className="text-xs text-slate-400 font-medium">/100</span>
            </div>
            <div className="h-8 flex items-end gap-1 pt-1">
              {[35, 42, 58, 64, 72, 81, 89].map((h, i) => (
                <div key={i} className="flex-1 bg-emerald-500/30 rounded-t hover:bg-emerald-400 transition-all" style={{ height: `${h}%` }} />
              ))}
            </div>
            <p className="text-[10px] font-semibold text-emerald-400 flex items-center gap-1">
              <TrendingUp className="w-3 h-3" /> ↑ 8 points this week
            </p>
          </div>
        </div>

        {/* User Profile Footer */}
        {user && (
          <div className="pt-4 border-t border-white/10 flex items-center justify-between">
            <div className="flex items-center gap-2.5 overflow-hidden">
              <div className="w-8 h-8 rounded-full bg-emerald-700 flex items-center justify-center text-white font-bold text-xs shrink-0">
                {user.full_name ? user.full_name[0].toUpperCase() : 'T'}
              </div>
              <div className="overflow-hidden">
                <p className="text-xs font-bold text-white truncate">{user.full_name || 'Tishal Mohan'}</p>
                <p className="text-[10px] text-slate-400 truncate">{user.target_job_role || 'AI Engineer'}</p>
              </div>
            </div>
          </div>
        )}
      </aside>

      {/* Main Experience Viewport */}
      <main className="flex-1 bg-[#fbf9f5] text-slate-900 overflow-y-auto">{children}</main>
    </div>
  );
}
