'use client';

import React from 'react';
import { Loader2 } from 'lucide-react';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'emerald' | 'copper' | 'outline' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'emerald',
  size = 'md',
  isLoading = false,
  leftIcon,
  rightIcon,
  className = '',
  disabled,
  ...props
}) => {
  const baseStyles = 'inline-flex items-center justify-center font-semibold rounded-xl transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 disabled:opacity-50 disabled:cursor-not-allowed';
  
  const variants = {
    emerald: 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-md shadow-emerald-900/30',
    copper: 'bg-orange-700 hover:bg-orange-600 text-white shadow-md shadow-orange-900/30',
    outline: 'border border-white/15 bg-slate-900/60 hover:bg-slate-800 text-slate-200 hover:border-slate-400',
    ghost: 'bg-transparent hover:bg-white/5 text-slate-300 hover:text-white',
  };

  const sizes = {
    sm: 'text-xs px-3 py-1.5 gap-1.5',
    md: 'text-xs px-4 py-2.5 gap-2',
    lg: 'text-sm px-6 py-3.5 gap-2.5',
  };

  return (
    <button
      className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${className}`}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? <Loader2 className="w-4 h-4 animate-spin shrink-0" /> : leftIcon}
      <span>{children}</span>
      {!isLoading && rightIcon}
    </button>
  );
};
