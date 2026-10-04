'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import { fetchApi } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';
import { useSession } from '@/context/SessionContext';

interface WorkspaceContextType {
  overview: any | null;
  isLoading: boolean;
  refreshOverview: () => Promise<void>;
}

const WorkspaceContext = createContext<WorkspaceContextType | undefined>(undefined);

export const WorkspaceProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user } = useAuth();
  const { activeSession } = useSession();
  const [overview, setOverview] = useState<any | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refreshOverview = async () => {
    if (!user) {
      setOverview(null);
      setIsLoading(false);
      return;
    }

    try {
      const data = await fetchApi<any>('/dashboard/overview').catch(() => null);
      setOverview(data);
    } catch (err) {
      console.error("Error loading workspace overview:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    refreshOverview();
  }, [user, activeSession]);

  return (
    <WorkspaceContext.Provider value={{ overview, isLoading, refreshOverview }}>
      {children}
    </WorkspaceContext.Provider>
  );
};

export const useWorkspace = () => {
  const context = useContext(WorkspaceContext);
  if (!context) {
    throw new Error('useWorkspace must be used within a WorkspaceProvider');
  }
  return context;
};
