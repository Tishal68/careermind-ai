'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import { fetchApi } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';

interface ResumeSessionData {
  id: number;
  session_uuid: string;
  file_name: string;
  file_type: string;
  file_path: string;
  raw_text: string | null;
  parsed_data: any;
  created_at: string;
}

interface SessionContextType {
  activeSession: ResumeSessionData | null;
  latestReport: any | null;
  isLoading: boolean;
  refreshSession: () => Promise<void>;
  clearSession: () => Promise<void>;
}

const SessionContext = createContext<SessionContextType | undefined>(undefined);

export const SessionProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user } = useAuth();
  const [activeSession, setActiveSession] = useState<ResumeSessionData | null>(null);
  const [latestReport, setLatestReport] = useState<any | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refreshSession = async () => {
    if (!user) {
      setActiveSession(null);
      setLatestReport(null);
      setIsLoading(false);
      return;
    }

    try {
      const [resumes, reports] = await Promise.all([
        fetchApi<ResumeSessionData[]>('/resume/my-resumes').catch(() => []),
        fetchApi<any[]>('/analysis/reports').catch(() => [])
      ]);

      if (resumes && resumes.length > 0) {
        setActiveSession(resumes[0]);
      } else {
        setActiveSession(null);
      }

      if (reports && reports.length > 0) {
        setLatestReport(reports[0]);
      } else {
        setLatestReport(null);
      }
    } catch (err) {
      console.error("Error loading active session context:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    refreshSession();
  }, [user]);

  const clearSession = async () => {
    if (activeSession) {
      try {
        await fetchApi(`/resume/session/${activeSession.id}`, { method: 'DELETE' });
      } catch (e) {
        console.error("Session delete error:", e);
      }
    }
    setActiveSession(null);
    setLatestReport(null);
  };

  return (
    <SessionContext.Provider value={{ activeSession, latestReport, isLoading, refreshSession, clearSession }}>
      {children}
    </SessionContext.Provider>
  );
};

export const useSession = () => {
  const context = useContext(SessionContext);
  if (!context) {
    throw new Error('useSession must be used within a SessionProvider');
  }
  return context;
};
