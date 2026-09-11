import React from 'react';
import { RiskLevel, CaseStatus, DealerStatus } from '@/types';

interface StatusBadgeProps {
  type: 'risk' | 'case_status' | 'dealer_status' | 'data_source';
  value: RiskLevel | CaseStatus | DealerStatus | 'mock' | 'live' | string;
  size?: 'sm' | 'md';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ type, value, size = 'md' }) => {
  const sizeClasses = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-xs tracking-wide font-medium';

  if (type === 'data_source') {
    if (value === 'mock') {
      return (
        <span className={`inline-flex items-center gap-1.5 rounded-md border border-amber-500/30 bg-amber-500/10 text-amber-400 font-mono ${sizeClasses}`}>
          <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse"></span>
          SYNTHETIC MOCK DATA
        </span>
      );
    }
    return (
      <span className={`inline-flex items-center gap-1.5 rounded-md border border-emerald-500/30 bg-emerald-500/10 text-emerald-400 font-mono ${sizeClasses}`}>
        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
        LIVE API
      </span>
    );
  }

  if (type === 'risk') {
    switch (value) {
      case 'low':
        return (
          <span className={`inline-flex items-center rounded-full border border-emerald-500/30 bg-emerald-950/60 text-emerald-300 ${sizeClasses}`}>
            Low Risk
          </span>
        );
      case 'medium':
        return (
          <span className={`inline-flex items-center rounded-full border border-amber-500/30 bg-amber-950/60 text-amber-300 ${sizeClasses}`}>
            Moderate Anomaly
          </span>
        );
      case 'high':
        return (
          <span className={`inline-flex items-center rounded-full border border-orange-500/40 bg-orange-950/60 text-orange-300 font-semibold ${sizeClasses}`}>
            High Risk
          </span>
        );
      case 'critical':
        return (
          <span className={`inline-flex items-center rounded-full border border-rose-500/50 bg-rose-950/70 text-rose-300 font-semibold ${sizeClasses}`}>
            Critical Anomaly
          </span>
        );
      case 'requires_verification':
      default:
        return (
          <span className={`inline-flex items-center rounded-full border border-slate-600 bg-slate-800 text-slate-300 ${sizeClasses}`}>
            Requires Verification
          </span>
        );
    }
  }

  if (type === 'case_status') {
    switch (value) {
      case 'verified':
        return (
          <span className={`inline-flex items-center rounded-md border border-emerald-500/30 bg-emerald-950/50 text-emerald-300 ${sizeClasses}`}>
            Verified
          </span>
        );
      case 'flagged':
        return (
          <span className={`inline-flex items-center rounded-md border border-rose-500/40 bg-rose-950/60 text-rose-300 font-medium ${sizeClasses}`}>
            Flagged for Audit
          </span>
        );
      case 'under_review':
        return (
          <span className={`inline-flex items-center rounded-md border border-amber-500/30 bg-amber-950/50 text-amber-300 ${sizeClasses}`}>
            Under Review
          </span>
        );
      case 'verification_pending':
        return (
          <span className={`inline-flex items-center rounded-md border border-blue-500/30 bg-blue-950/50 text-blue-300 ${sizeClasses}`}>
            Verification Pending
          </span>
        );
      case 'submitted':
      default:
        return (
          <span className={`inline-flex items-center rounded-md border border-slate-700 bg-slate-800 text-slate-300 ${sizeClasses}`}>
            Submitted
          </span>
        );
    }
  }

  // Dealer status
  switch (value) {
    case 'active':
      return (
        <span className={`inline-flex items-center rounded-md border border-emerald-500/30 bg-emerald-950/50 text-emerald-300 ${sizeClasses}`}>
          Authorized
        </span>
      );
    case 'under_review':
      return (
        <span className={`inline-flex items-center rounded-md border border-amber-500/30 bg-amber-950/50 text-amber-300 ${sizeClasses}`}>
          Review Tier
        </span>
      );
    case 'flagged':
    case 'suspended':
      return (
        <span className={`inline-flex items-center rounded-md border border-rose-500/40 bg-rose-950/60 text-rose-300 ${sizeClasses}`}>
          Flagged Network
        </span>
      );
    default:
      return (
        <span className={`inline-flex items-center rounded-md border border-slate-700 bg-slate-800 text-slate-300 ${sizeClasses}`}>
          {String(value)}
        </span>
      );
  }
};
