'use client';

import React from 'react';

export const Input: React.FC<{
  label?: string;
  error?: string;
  leftIcon?: React.ReactNode;
} & React.InputHTMLAttributes<HTMLInputElement>> = ({
  label,
  error,
  leftIcon,
  className = '',
  ...props
}) => {
  const generatedId = React.useId();
  const inputId = props.id || generatedId;
  return (
    <div className="w-full space-y-1.5">
      {label && <label htmlFor={inputId} className="block text-xs font-semibold text-slate-300">{label}</label>}
      <div className="relative flex items-center">
        {leftIcon && <div className="absolute left-3.5 text-slate-400 pointer-events-none">{leftIcon}</div>}
        <input
          id={inputId}
          aria-invalid={!!error}
          aria-describedby={error ? `${inputId}-error` : undefined}
          className={`w-full bg-[#0b1320] border border-white/10 rounded-xl py-3 ${
            leftIcon ? 'pl-10' : 'pl-3.5'
          } pr-3.5 text-base text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-colors ${className}`}
          {...props}
        />
      </div>
      {error && <p id={`${inputId}-error`} role="alert" className="text-[11px] font-medium text-rose-400 mt-1">{error}</p>}
    </div>
  );
};
