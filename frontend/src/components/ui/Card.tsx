'use client';

import React from 'react';

export const Card: React.FC<{
  children: React.ReactNode;
  className?: string;
  hover?: boolean;
  glass?: boolean;
  glow?: boolean;
}> = ({ children, className = '', hover = false, glass = false, glow = false }) => {
  const extraStyles = `${glass ? 'backdrop-blur-md bg-slate-900/40 border border-white/10' : ''} ${glow ? 'shadow-lg shadow-emerald-950/20' : ''}`;
  return (
    <div className={`nexpath-card ${hover ? 'nexpath-card-hover cursor-pointer' : ''} ${extraStyles} p-6 ${className}`}>
      {children}
    </div>
  );
};
