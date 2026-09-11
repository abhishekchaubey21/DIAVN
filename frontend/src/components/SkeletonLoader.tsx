import React from 'react';

export function CardSkeleton({ count = 1 }: { count?: number }) {
  return (
    <>
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="rounded-2xl border border-[#E5E9F2] bg-white p-5 shadow-xs animate-pulse space-y-3">
          <div className="h-4 w-24 bg-slate-100 rounded" />
          <div className="h-8 w-36 bg-slate-200 rounded" />
          <div className="h-3 w-48 bg-slate-100 rounded" />
        </div>
      ))}
    </>
  );
}

export function TableSkeleton({ rows = 5 }: { rows?: number }) {
  return (
    <div className="rounded-2xl border border-[#E5E9F2] bg-white p-4 shadow-xs animate-pulse space-y-3">
      <div className="h-5 w-48 bg-slate-200 rounded mb-4" />
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex items-center justify-between py-2 border-b border-[#F1F4FA]">
          <div className="h-4 w-28 bg-slate-200 rounded" />
          <div className="h-4 w-36 bg-slate-100 rounded hidden sm:block" />
          <div className="h-4 w-20 bg-slate-200 rounded" />
          <div className="h-4 w-16 bg-slate-100 rounded" />
        </div>
      ))}
    </div>
  );
}
