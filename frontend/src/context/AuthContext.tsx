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

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const storedToken = typeof window !== 'undefined' ? localStorage.getItem('careermind_token') : null;
    if (storedToken) {
      setToken(storedToken);
      fetchApi<User>('/auth/me')
        .then((userData) => setUser(userData))
        .catch(() => {
          if (typeof window !== 'undefined') localStorage.removeItem('careermind_token');
          setToken(null);
          setUser(null);
        })
        .finally(() => setIsLoading(false));
    } else {
      setIsLoading(false);
    }
  }, []);

  const login = (newToken: string, newUser: User) => {
    if (typeof window !== 'undefined') localStorage.setItem('careermind_token', newToken);
    setToken(newToken);
    setUser(newUser);
  };

  const logout = () => {
    if (typeof window !== 'undefined') localStorage.removeItem('careermind_token');
    setToken(null);
    setUser(null);
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
