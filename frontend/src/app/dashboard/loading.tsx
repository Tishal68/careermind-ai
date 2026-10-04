import React from 'react';

export default function DashboardLoading() {
  return (
    <div className="min-h-[70vh] flex items-center justify-center p-6 bg-[#fbf9f5]">
      <div className="text-center space-y-3">
        <div className="w-10 h-10 border-3 border-[#0F5E4E] border-t-transparent rounded-full animate-spin mx-auto" />
        <p className="text-xs font-semibold text-slate-500">Loading...</p>
      </div>
    </div>
  );
}
