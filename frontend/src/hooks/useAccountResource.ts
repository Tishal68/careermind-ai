"use client";
import { useCallback, useEffect, useRef, useState } from 'react';
import { useAuth } from '@/context/AuthContext';
import { fetchApi } from '@/lib/api';

/** Keep a last good value only for the current authenticated session. */
export function useAccountResource<T>(endpoint: string) {
  const { token, user } = useAuth();
  const [state, setState] = useState<{token: string | null; data: T | null; error: string; loading: boolean}>({token: null, data: null, error: '', loading: true});
  const active = useRef<AbortController | null>(null);
  const current = state.token === token ? state : {token, data: null, error: '', loading: true};
  const reload = useCallback(async () => {
    active.current?.abort();
    const controller = new AbortController(); active.current = controller;
    if (!token || !user) { setState({token, data: null, error: '', loading: false}); return; }
    setState(previous => ({token, data: previous.token === token ? previous.data : null, error: '', loading: true}));
    try {
      const data = await fetchApi<T>(endpoint, {signal: AbortSignal.any([controller.signal, AbortSignal.timeout(20000)])});
      if (!controller.signal.aborted && localStorage.getItem('careermind_token') === token) setState({token, data, error: '', loading: false});
    } catch (err: any) {
      if (!controller.signal.aborted && localStorage.getItem('careermind_token') === token) setState(previous => ({token, data: previous.token === token ? previous.data : null, error: err.message || 'Could not load your saved data.', loading: false}));
    }
  }, [endpoint, token, user?.id]);
  useEffect(() => { reload(); return () => active.current?.abort(); }, [reload]);
  const update = useCallback((change: (previous: T | null) => T) => {
    if (!token || localStorage.getItem('careermind_token') !== token) return;
    active.current?.abort();
    setState(previous => ({token, data: change(previous.token === token ? previous.data : null), error: '', loading: false}));
  }, [token]);
  return {...current, reload, update};
}
