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
  login: (token: string, user: User) => void;
  logout: () => void;
}

const DEFAULT_STANDALONE_USER: User = {
  id: 1,
  email: 'user@nexpath.ai',
  full_name: 'NexPath Professional',
  is_active: true,
  is_superuser: true,
  target_job_role: 'AI Engineer',
  preferred_ai_model: 'gemini-2.5-flash',
  created_at: new Date().toISOString()
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(DEFAULT_STANDALONE_USER);
  const [token, setToken] = useState<string | null>('standalone-token');
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    // Attempt to synchronize with backend /auth/me silently if available
    fetchApi<User>('/auth/me')
      .then((userData) => {
        if (userData) setUser(userData);
      })
      .catch(() => {
        // Fallback to standalone user cleanly without blocking
        setUser(DEFAULT_STANDALONE_USER);
      });
  }, []);

  const login = (newToken: string, newUser: User) => {
    setToken(newToken);
    setUser(newUser);
  };

  const logout = () => {
    // Reset to standalone user
    setUser(DEFAULT_STANDALONE_USER);
  };

  return (
    <AuthContext.Provider value={{ user, token, isLoading, login, logout }}>
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
