'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import { fetchApi } from '@/lib/api';

interface User {
  id: number;
  email: string;
  full_name: string | null;
  is_active: boolean;
  is_superuser?: boolean;
  is_verified?: boolean;
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
  updateTargetRole: (userId: number, role: string) => void;
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
      .then(data => { if (active && localStorage.getItem('careermind_token') === saved) setUser(data); })
      .catch(err => { if (active && localStorage.getItem('careermind_token') === saved) {
        if (err.status === 401) { localStorage.removeItem('careermind_token'); localStorage.removeItem('careermind_research_job'); setToken(null); setUser(null); }
        else setSessionError('We could not reconnect to your account. Your session is saved. Please try again.');
      } })
      .finally(() => { if (active) setIsLoading(false); });
    return () => { active = false; };
  }, [attempt]);

  useEffect(() => {
    const sync = (event: StorageEvent) => {
      if (event.key !== 'careermind_token') return;
      setUser(null); setToken(null); setSessionError('');
      setIsLoading(true); setAttempt(value => value + 1);
    };
    window.addEventListener('storage', sync);
    return () => window.removeEventListener('storage', sync);
  }, []);

  const login = (newToken: string, newUser: User) => {
    localStorage.removeItem('careermind_research_job');
    setSessionError('');
    localStorage.setItem('careermind_token', newToken);
    setAttempt(value => value + 1);
    setIsLoading(false);
    setToken(newToken);
    setUser(newUser);
  };

  const updateTargetRole = (userId: number, role: string) => {
    setUser(current => current?.id === userId ? {...current, target_job_role: role} : current);
  };

  const logout = async () => {
    // Start revocation with the current token, then clear this device immediately.
    const revocation = fetchApi('/auth/logout', { method: 'POST' }).catch(() => undefined);
    localStorage.removeItem('careermind_token');
    localStorage.removeItem('careermind_research_job');
    setToken(null);
    setUser(null);
    setSessionError('');
    setAttempt(value => value + 1);
    await revocation;
  };

  return (
    <AuthContext.Provider value={{ user, token, isLoading, sessionError, retrySession, login, logout, updateTargetRole }}>
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
