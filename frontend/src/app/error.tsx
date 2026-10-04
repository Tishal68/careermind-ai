'use client';

import React from 'react';
import Link from 'next/link';
import { AlertTriangle, ArrowLeft, RefreshCw } from 'lucide-react';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="min-h-screen bg-[#070c14] flex items-center justify-center p-6">
      <div className="max-w-md w-full text-center space-y-6">
        <div className="inline-flex p-4 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-400">
          <AlertTriangle className="w-8 h-8" />
        </div>
        <h1 className="text-2xl font-extrabold text-white">Something went wrong</h1>
        <p className="text-sm text-slate-400 leading-relaxed">
          {error.message || 'An unexpected error occurred. Please try again.'}
        </p>
        <div className="flex flex-wrap justify-center gap-3 pt-2">
          <button
            onClick={reset}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-[#0F5E4E] text-white text-xs font-semibold hover:bg-emerald-700 transition-all"
          >
            <RefreshCw className="w-4 h-4" /> Try Again
          </button>
          <Link
            href="/"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl border border-white/10 text-slate-300 text-xs font-semibold hover:bg-white/5 transition-all"
          >
            <ArrowLeft className="w-4 h-4" /> Back to Home
          </Link>
        </div>
      </div>
    </div>
  );
}
