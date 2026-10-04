'use client';

import React from 'react';
import { Loader2, CheckCircle2 } from 'lucide-react';

export interface PipelineStep {
  id: string;
  label: string;
  isComplete: boolean;
  isCurrent: boolean;
}

export const PipelineLoader: React.FC<{ steps: PipelineStep[] }> = ({ steps }) => {
  return (
    <div className="p-6 rounded-2xl bg-[#0b131c] border border-white/10 space-y-4 max-w-md w-full mx-auto">
      <div className="flex items-center gap-3 pb-3 border-b border-white/10">
        <Loader2 className="w-5 h-5 animate-spin text-emerald-400" />
        <div>
          <h4 className="text-sm font-bold text-white">Executing AI Career Pipeline</h4>
          <p className="text-[11px] text-slate-400">Processing resume & synchronizing Career OS Kernel</p>
        </div>
      </div>
      <div className="space-y-2.5">
        {steps.map((step) => (
          <div key={step.id} className="flex items-center justify-between text-xs">
            <div className="flex items-center gap-2.5">
              {step.isComplete ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
              ) : step.isCurrent ? (
                <Loader2 className="w-4 h-4 text-amber-400 animate-spin shrink-0" />
              ) : (
                <div className="w-4 h-4 rounded-full border border-slate-700 shrink-0" />
              )}
              <span className={step.isComplete ? 'text-slate-200 font-medium' : step.isCurrent ? 'text-white font-bold' : 'text-slate-500'}>
                {step.label}
              </span>
            </div>
            {step.isComplete && <span className="text-[10px] font-bold text-emerald-400 uppercase tracking-widest">Done</span>}
          </div>
        ))}
      </div>
    </div>
  );
};
