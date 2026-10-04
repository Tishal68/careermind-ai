'use client';

import React from 'react';

export const Card: React.FC<{
  children: React.ReactNode;
  className?: string;
  hover?: boolean;
}> = ({ children, className = '', hover = false }) => {
  return (
    <div className={`nexpath-card ${hover ? 'nexpath-card-hover cursor-pointer' : ''} p-6 ${className}`}>
      {children}
    </div>
  );
};
