'use client';

import React from 'react';

export const NexScoreGauge: React.FC<{ score: number; label?: string }> = ({ score, label = "NexScore™" }) => {
  const rounded = Math.round(score);
  const color = rounded >= 80 ? 'text-emerald-400' : rounded >= 65 ? 'text-amber-400' : 'text-rose-400';
  const strokeColor = rounded >= 80 ? '#059669' : rounded >= 65 ? '#d97706' : '#e11d48';

  return (
    <div className="flex flex-col items-center justify-center p-4">
      <div className="relative w-36 h-36 flex items-center justify-center">
        <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
          <path
            className="text-slate-800"
            strokeWidth="3.5"
            stroke="currentColor"
            fill="none"
            d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
          />
          <path
            strokeWidth="3.5"
            strokeDasharray={`${rounded}, 100`}
            stroke={strokeColor}
            strokeLinecap="round"
            fill="none"
            d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
          />
        </svg>
        <div className="absolute text-center">
          <span className={`text-3xl font-extrabold tracking-tight ${color}`}>{rounded}</span>
          <span className="text-[10px] block font-semibold text-slate-400 uppercase tracking-widest mt-0.5">{label}</span>
        </div>
      </div>
    </div>
  );
};
