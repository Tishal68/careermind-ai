export default function DashboardLoading() {
  return <div role="status" aria-label="Loading your workspace" className="max-w-6xl mx-auto w-full px-4 sm:px-8 py-10 space-y-8">
    <span className="sr-only">Loading your workspace…</span>
    <div aria-hidden="true" className="space-y-4"><div className="skeleton h-3 w-32" /><div className="skeleton h-10 w-3/4 max-w-lg" /><div className="skeleton h-4 w-2/3" /></div>
    <div aria-hidden="true" className="grid xl:grid-cols-[380px_1fr] gap-6"><div className="skeleton h-96 rounded-2xl" /><div className="skeleton h-80 rounded-2xl" /></div>
  </div>;
}
