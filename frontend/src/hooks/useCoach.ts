'use client';

import { useState, useEffect } from 'react';
import { fetchApi } from '@/lib/api';

export function useCoach() {
  const [messages, setMessages] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSending, setIsSending] = useState(false);

  const loadChatHistory = async () => {
    setIsLoading(true);
    try {
      const res = await fetchApi<any>('/chat/history');
      if (res && res.messages) {
        setMessages(res.messages);
      }
    } catch (err) {
      console.error("Failed to load chat history:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadChatHistory();
  }, []);

  const sendMessage = async (content: string) => {
    if (!content.trim() || isSending) return;

    const userMsg = {
      id: Date.now(),
      role: 'user',
      content,
      created_at: new Date().toISOString()
    };

    setMessages((prev) => [...prev, userMsg]);
    setIsSending(true);

    try {
      const res = await fetchApi<any>('/chat/message', {
        method: 'POST',
        body: JSON.stringify({ content })
      });
      setMessages((prev) => [...prev, res]);
    } catch (err) {
      console.error("Failed to send message:", err);
    } finally {
      setIsSending(false);
    }
  };

  return { messages, isLoading, isSending, sendMessage, refreshHistory: loadChatHistory };
}
