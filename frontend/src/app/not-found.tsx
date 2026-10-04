'use client';

import React from 'react';
import Link from 'next/link';
import { Compass, ArrowLeft } from 'lucide-react';

export default function NotFound() {
  return (
    <div className="min-h-screen bg-[#070c14] flex items-center justify-center p-6">
      <div className="max-w-md w-full text-center space-y-6">
        <div className="inline-flex p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
          <Compass className="w-8 h-8" />
        </div>
        <h1 className="text-5xl font-extrabold text-white">404</h1>
        <p className="text-sm text-slate-400 leading-relaxed">
          This page doesn't exist. Let's get you back on track.
        </p>
        <Link
          href="/"
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-[#0F5E4E] text-white text-xs font-semibold hover:bg-emerald-700 transition-all"
        >
          <ArrowLeft className="w-4 h-4" /> Back to NexPath
        </Link>
      </div>
    </div>
  );
}
