'use client';

import React from 'react';
import Link from 'next/link';
import { LucideIcon, Inbox } from 'lucide-react';

interface EmptyStateProps {
  icon?: LucideIcon;
  title: string;
  description: string;
  actionLabel?: string;
  actionHref?: string;
  onAction?: () => void;
}

export function EmptyState({
  icon: Icon = Inbox,
  title,
  description,
  actionLabel,
  actionHref,
  onAction
}: EmptyStateProps) {
  return (
    <div className="p-8 rounded-2xl border border-[#E5E9F2] bg-[#F8FAFD] text-center flex flex-col items-center justify-center space-y-3">
      <div className="h-10 w-10 rounded-xl bg-white border border-[#E5E9F2] flex items-center justify-center text-[#8E99AD] shadow-2xs">
        <Icon className="h-5 w-5" />
      </div>
      <div className="max-w-md space-y-1">
        <h4 className="text-sm font-bold text-[#182033]">{title}</h4>
        <p className="text-xs text-[#68738A] leading-relaxed">{description}</p>
      </div>
      {(actionLabel && actionHref) && (
        <Link
          href={actionHref}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white border border-[#E5E9F2] text-xs font-semibold text-[#4F6EF7] hover:bg-[#4F6EF7] hover:text-white transition-colors shadow-2xs"
        >
          {actionLabel}
        </Link>
      )}
      {(actionLabel && onAction && !actionHref) && (
        <button
          onClick={onAction}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white border border-[#E5E9F2] text-xs font-semibold text-[#4F6EF7] hover:bg-[#4F6EF7] hover:text-white transition-colors shadow-2xs"
        >
          {actionLabel}
        </button>
      )}
    </div>
  );
}
