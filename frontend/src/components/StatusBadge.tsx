import React from 'react';
import { RiskLevel, CaseStatus, DealerStatus } from '@/types';

interface StatusBadgeProps {
  type: 'risk' | 'case_status' | 'dealer_status' | 'data_source';
  value: RiskLevel | CaseStatus | DealerStatus | 'mock' | 'live' | string;
  size?: 'sm' | 'md';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ type, value, size = 'md' }) => {
  const sizeClasses = size === 'sm' ? 'px-2 py-0.5 text-[10px] font-bold' : 'px-2.5 py-1 text-xs font-bold';

  if (type === 'data_source') {
    if (value === 'mock') {
      return (
        <span className={`inline-flex items-center gap-1.5 rounded-full border border-[#FDE68A] bg-[#FFFBEB] text-[#92400E] font-mono ${sizeClasses}`}>
          <span className="w-1.5 h-1.5 rounded-full bg-[#F59E0B] animate-pulse"></span>
          SYNTHETIC BENCHMARK
        </span>
      );
    }
    return (
      <span className={`inline-flex items-center gap-1.5 rounded-full border border-[#A7F3D0] bg-[#ECFDF5] text-[#065F46] font-mono ${sizeClasses}`}>
        <span className="w-1.5 h-1.5 rounded-full bg-[#10B981]"></span>
        LIVE NODE
      </span>
    );
  }

  if (type === 'risk') {
    const valLower = String(value).toLowerCase();
    switch (valLower) {
      case 'low':
        return (
          <span className={`inline-flex items-center rounded-full border border-[#A7F3D0] bg-[#ECFDF5] text-[#065F46] ${sizeClasses}`}>
            LOW RISK
          </span>
        );
      case 'medium':
        return (
          <span className={`inline-flex items-center rounded-full border border-[#FDE68A] bg-[#FFFBEB] text-[#92400E] ${sizeClasses}`}>
            MEDIUM RISK
          </span>
        );
      case 'high':
      case 'critical':
        return (
          <span className={`inline-flex items-center rounded-full border border-[#FECACA] bg-[#FEF2F2] text-[#991B1B] ${sizeClasses}`}>
            HIGH RISK
          </span>
        );
      case 'requires_verification':
      default:
        return (
          <span className={`inline-flex items-center rounded-full border border-[#E5E9F2] bg-[#F8FAFD] text-[#68738A] ${sizeClasses}`}>
            REQUIRES REVIEW
          </span>
        );
    }
  }

  if (type === 'case_status') {
    const valLower = String(value).toLowerCase();
    switch (valLower) {
      case 'verified':
        return (
          <span className={`inline-flex items-center rounded-lg border border-[#A7F3D0] bg-[#ECFDF5] text-[#065F46] ${sizeClasses}`}>
            Verified Clean
          </span>
        );
      case 'flagged':
        return (
          <span className={`inline-flex items-center rounded-lg border border-[#FECACA] bg-[#FEF2F2] text-[#991B1B] ${sizeClasses}`}>
            Flagged for Audit
          </span>
        );
      case 'under_review':
        return (
          <span className={`inline-flex items-center rounded-lg border border-[#FDE68A] bg-[#FFFBEB] text-[#92400E] ${sizeClasses}`}>
            Under Review
          </span>
        );
      case 'verification_pending':
        return (
          <span className={`inline-flex items-center rounded-lg border border-[#C7D2FE] bg-[#EEF2FF] text-[#4338CA] ${sizeClasses}`}>
            Verification Pending
          </span>
        );
      case 'submitted':
      default:
        return (
          <span className={`inline-flex items-center rounded-lg border border-[#E5E9F2] bg-[#F8FAFD] text-[#68738A] ${sizeClasses}`}>
            Submitted
          </span>
        );
    }
  }

  // Dealer status
  const dValLower = String(value).toLowerCase();
  switch (dValLower) {
    case 'active':
      return (
        <span className={`inline-flex items-center rounded-lg border border-[#A7F3D0] bg-[#ECFDF5] text-[#065F46] ${sizeClasses}`}>
          Authorized Active
        </span>
      );
    case 'under_review':
      return (
        <span className={`inline-flex items-center rounded-lg border border-[#FDE68A] bg-[#FFFBEB] text-[#92400E] ${sizeClasses}`}>
          Heightened Review
        </span>
      );
    case 'flagged':
    case 'suspended':
      return (
        <span className={`inline-flex items-center rounded-lg border border-[#FECACA] bg-[#FEF2F2] text-[#991B1B] ${sizeClasses}`}>
          Flagged Network
        </span>
      );
    default:
      return (
        <span className={`inline-flex items-center rounded-lg border border-[#E5E9F2] bg-[#F8FAFD] text-[#68738A] ${sizeClasses}`}>
          {String(value)}
        </span>
      );
  }
};
