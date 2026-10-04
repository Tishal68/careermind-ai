'use client';

import React from 'react';
import Link from 'next/link';
import { AlertTriangle, ArrowLeft, RefreshCw } from 'lucide-react';

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="min-h-[70vh] flex items-center justify-center p-6 bg-[#fbf9f5]">
      <div className="max-w-md w-full text-center space-y-6">
        <div className="inline-flex p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-500">
          <AlertTriangle className="w-8 h-8" />
        </div>
        <h1 className="text-2xl font-extrabold text-slate-900">Something went wrong</h1>
        <p className="text-sm text-slate-500 leading-relaxed">
          {error.message || 'An unexpected error occurred in the dashboard. Please try again.'}
        </p>
        <div className="flex flex-wrap justify-center gap-3 pt-2">
          <button
            onClick={reset}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-[#0F5E4E] text-white text-xs font-semibold hover:bg-emerald-700 transition-all"
          >
            <RefreshCw className="w-4 h-4" /> Try Again
          </button>
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl border border-slate-200 text-slate-700 text-xs font-semibold hover:bg-slate-50 transition-all"
          >
            <ArrowLeft className="w-4 h-4" /> Back to Dashboard
          </Link>
        </div>
      </div>
    </div>
  );
}
