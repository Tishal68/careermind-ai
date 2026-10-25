'use client';

import { useEffect, useState } from 'react';
import { fetchApi } from '@/lib/api';

export default function DeploymentNotice() {
  const [demo, setDemo] = useState(false);
  useEffect(() => {
    let active = true;
    fetchApi<{ disposable_demo: boolean }>('/deployment-info')
      .then(info => { if (active) setDemo(info.disposable_demo); })
      .catch(() => {});
    return () => { active = false; };
  }, []);
  if (!demo) return null;
  return <aside aria-label="Demo storage notice" className="rounded-xl border border-amber-300/20 bg-amber-300/5 p-4 text-sm text-amber-100">
    <strong>Disposable demo.</strong> Accounts, resumes, and reports may reset when the service restarts or updates. Keep your original resume and export important results. If an old account stops working after a reset, create a new demo account. The first visit may take up to 90 seconds.
  </aside>;
}
