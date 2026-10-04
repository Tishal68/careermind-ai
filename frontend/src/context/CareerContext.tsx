'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import { fetchApi } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';
import { useSession } from '@/context/SessionContext';

interface CareerContextType {
  careerProfile: any | null;
  nexScoreBreakdown: any | null;
  targetRole: string;
  isLoading: boolean;
  updateTargetRole: (newRole: string) => Promise<void>;
  refreshCareer: () => Promise<void>;
}

const CareerContext = createContext<CareerContextType | undefined>(undefined);

export const CareerProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user } = useAuth();
  const { activeSession, latestReport } = useSession();
  const [careerProfile, setCareerProfile] = useState<any | null>(null);
  const [nexScoreBreakdown, setNexScoreBreakdown] = useState<any | null>(null);
  const [targetRole, setTargetRole] = useState<string>(user?.target_job_role || 'AI Engineer');
  const [isLoading, setIsLoading] = useState(true);

  const refreshCareer = async () => {
    if (!user) {
      setCareerProfile(null);
      setNexScoreBreakdown(null);
      setIsLoading(false);
      return;
    }

    try {
      if (latestReport) {
        setCareerProfile(latestReport);
        setNexScoreBreakdown(latestReport.nex_score_breakdown || {
          nex_score: latestReport.nex_score || 89.0,
          ats_compatibility: latestReport.ats_score || 92.0,
          resume_quality: latestReport.resume_score || 80.0,
          role_readiness: latestReport.readiness_score || 75.0
        });
        if (latestReport.job_role) {
          setTargetRole(latestReport.job_role);
        }
      }
    } catch (err) {
      console.error("Error loading career context:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    refreshCareer();
  }, [user, activeSession, latestReport]);

  const updateTargetRole = async (newRole: string) => {
    setTargetRole(newRole);
    try {
      await fetchApi('/user/settings', {
        method: 'PUT',
        body: JSON.stringify({ target_job_role: newRole })
      });
    } catch (err) {
      console.error("Failed to update target role:", err);
    }
  };

  return (
    <CareerContext.Provider value={{ careerProfile, nexScoreBreakdown, targetRole, isLoading, updateTargetRole, refreshCareer }}>
      {children}
    </CareerContext.Provider>
  );
};

export const useCareerContext = () => {
  const context = useContext(CareerContext);
  if (!context) {
    throw new Error('useCareerContext must be used within a CareerProvider');
  }
  return context;
};
