'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import { fetchApi } from '@/lib/api';

interface User {
  id: number;
  email: string;
  full_name: string | null;
  is_active: boolean;
  is_superuser?: boolean;
  target_job_role?: string | null;
  preferred_ai_model?: string | null;
  created_at: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  sessionError: string;
  retrySession: () => void;
  login: (token: string, user: User) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [sessionError, setSessionError] = useState('');
  const [attempt, setAttempt] = useState(0);
  const retrySession = () => { setIsLoading(true); setSessionError(''); setAttempt(value => value + 1); };

  useEffect(() => {
    let active = true;
    const saved = localStorage.getItem('careermind_token');
    if (!saved) { setIsLoading(false); return; }
    setToken(saved);
    fetchApi<User>('/auth/me')
      .then(data => { if (active) setUser(data); })
      .catch(err => { if (active) {
        if (err.status === 401) { localStorage.removeItem('careermind_token'); localStorage.removeItem('careermind_research_job'); setToken(null); setUser(null); }
        else setSessionError('We could not reconnect to your account. Your session is saved. Please try again.');
      } })
      .finally(() => { if (active) setIsLoading(false); });
    return () => { active = false; };
  }, [attempt]);

  const login = (newToken: string, newUser: User) => {
    localStorage.removeItem('careermind_research_job');
    setSessionError('');
    localStorage.setItem('careermind_token', newToken);
    setToken(newToken);
    setUser(newUser);
  };

  const logout = async () => {
    // Start revocation with the current token, then clear this device immediately.
    const revocation = fetchApi('/auth/logout', { method: 'POST' }).catch(() => undefined);
    localStorage.removeItem('careermind_token');
    localStorage.removeItem('careermind_research_job');
    setToken(null);
    setUser(null);
    setSessionError('');
    await revocation;
  };

  return (
    <AuthContext.Provider value={{ user, token, isLoading, sessionError, retrySession, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
