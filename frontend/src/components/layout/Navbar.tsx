'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { ShieldCheck, Compass, LogOut, User } from 'lucide-react';

export const Navbar: React.FC = () => {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  return (
    <header className="sticky top-0 z-50 bg-[#070c14]/90 backdrop-blur-md border-b border-white/10">
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        {/* Brand Logo & Tagline */}
        <Link href={user ? '/dashboard' : '/'} className="flex items-center gap-3 group">
          <div className="p-2 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 group-hover:bg-emerald-500/20 transition-all">
            <Compass className="w-5 h-5" />
          </div>
          <div>
            <span className="text-lg font-extrabold text-white tracking-tight">NexPath</span>
            <span className="hidden sm:inline-block ml-2.5 text-[11px] font-medium px-2 py-0.5 rounded-full bg-slate-800 text-emerald-400 border border-emerald-500/20">
              AI Career OS
            </span>
          </div>
        </Link>

        {/* User Workspace Navigation & Account Menu */}
        <div className="flex items-center gap-4">
          {user ? (
            <div className="flex items-center gap-3">
              <Link
                href="/dashboard/settings"
                className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900 border border-white/10 text-xs text-slate-300 hover:text-white hover:border-emerald-500/40 transition-all"
              >
                <User className="w-3.5 h-3.5 text-emerald-400" />
                <span className="font-medium truncate max-w-[120px]">{user.full_name || user.email}</span>
                {user.is_superuser && (
                  <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">
                    Admin
                  </span>
                )}
              </Link>
              <button
                onClick={logout}
                className="p-2 rounded-xl bg-slate-900 border border-white/10 text-slate-400 hover:text-rose-400 hover:border-rose-500/30 transition-all"
                title="Sign Out"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-3 text-xs font-semibold">
              <Link href="/login" className="px-4 py-2 rounded-xl text-slate-300 hover:text-white transition-colors">
                Sign In
              </Link>
              <Link href="/register" className="btn-emerald">
                Get Started
              </Link>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
