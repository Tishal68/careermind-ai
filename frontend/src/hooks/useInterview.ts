'use client';

import { useState } from 'react';
import { fetchApi } from '@/lib/api';

export function useInterview() {
  const [session, setSession] = useState<any | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [evaluation, setEvaluation] = useState<any | null>(null);

  const startSession = async (interviewType: string, targetRole: string) => {
    setIsLoading(true);
    setEvaluation(null);
    try {
      const res = await fetchApi<any>('/interview/start', {
        method: 'POST',
        body: JSON.stringify({ interview_type: interviewType, target_role: targetRole })
      });
      setSession(res);
      return res;
    } catch (err) {
      console.error("Failed to start interview:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const evaluateAnswer = async (sessionId: number, question: string, userAnswer: string) => {
    setIsLoading(true);
    try {
      const res = await fetchApi<any>('/interview/evaluate', {
        method: 'POST',
        body: JSON.stringify({ session_id: sessionId, question, user_answer: userAnswer })
      });
      setEvaluation(res);
      return res;
    } catch (err) {
      console.error("Failed to evaluate answer:", err);
    } finally {
      setIsLoading(false);
    }
  };

  return { session, evaluation, isLoading, startSession, evaluateAnswer };
}
