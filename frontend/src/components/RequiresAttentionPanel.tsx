'use client';

import React from 'react';
import Link from 'next/link';
import { Case } from '@/types';
import { 
  ShieldAlert, 
  AlertTriangle, 
  ArrowRight, 
  SearchCheck, 
  MapPin, 
  FileWarning,
  Layers
} from 'lucide-react';

interface RequiresAttentionPanelProps {
  cases: Case[];
}

export function RequiresAttentionPanel({ cases = [] }: RequiresAttentionPanelProps) {
  // Extract actionable anomaly items
  const attentionItems = [
    {
      severity: 'HIGH' as const,
      caseNumber: 'CAS-2026-007',
      caseId: 'CAS-2026-007',
      title: 'Multi-Factor Anomaly Stack',
      reason: 'Duplicate serial (ASP-99881) + image reuse + GPS mismatch.',
      action: 'Review Case',
      href: '/cases/CAS-2026-007',
      icon: ShieldAlert
    },
    {
      severity: 'HIGH' as const,
      caseNumber: 'CAS-2026-005',
      caseId: 'CAS-2026-005',
      title: 'Duplicate Serial Collision',
      reason: 'Equipment serial registered to active loan in Pune.',
      action: 'Review Serial',
      href: '/cases/CAS-2026-005',
      icon: Layers
    },
    {
      severity: 'MEDIUM' as const,
      caseNumber: 'CAS-2026-003',
      caseId: 'CAS-2026-003',
      title: 'Invoice Price Variance (+121%)',
      reason: 'Unit rate exceeds market benchmark threshold (±15%).',
      action: 'Verify Invoice',
      href: '/cases/CAS-2026-003',
      icon: FileWarning
    },
    {
      severity: 'MEDIUM' as const,
      caseNumber: 'CAS-2026-010',
      caseId: 'CAS-2026-010',
      title: 'GPS EXIF Telemetry Discrepancy',
      reason: 'Installation image EXIF location differs from claimed site by 74.8 km.',
      action: 'Inspect GPS',
      href: '/cases/CAS-2026-010',
      icon: MapPin
    }
  ];

  return (
    <div className="rounded-2xl border border-[#E5E9F2] bg-white p-5 shadow-xs flex flex-col justify-between space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-[#E5E9F2]">
        <div className="flex items-center gap-2">
          <div className="h-7 w-7 rounded-lg bg-[#FEF2F2] text-[#EF4444] flex items-center justify-center border border-[#FECACA]">
            <ShieldAlert className="h-4 w-4" />
          </div>
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-[#182033]">
              Requires Attention
            </h3>
            <span className="text-[10px] text-[#68738A]">
              Urgent verification tasks & evidence anomalies
            </span>
          </div>
        </div>

        <span className="px-2 py-0.5 rounded-full text-[9px] font-mono font-bold bg-[#EF4444]/10 text-[#991B1B] border border-[#FECACA]">
          {attentionItems.length} Urgent
        </span>
      </div>

      {/* Action Items List */}
      <div className="space-y-2.5">
        {attentionItems.map((item, idx) => {
          const isHigh = item.severity === 'HIGH';
          const Icon = item.icon;

          return (
            <div
              key={idx}
              className={`p-3 rounded-xl border bg-[#F8FAFD] transition-all space-y-2 ${
                isHigh ? 'border-[#FECACA] hover:border-[#F87171]' : 'border-[#FDE68A] hover:border-[#F59E0B]'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className={`px-1.5 py-0.5 rounded text-[9px] font-mono font-extrabold border ${
                    isHigh 
                      ? 'bg-[#FEF2F2] text-[#991B1B] border-[#FECACA]' 
                      : 'bg-[#FFFBEB] text-[#92400E] border-[#FDE68A]'
                  }`}>
                    {item.severity}
                  </span>
                  <span className="font-mono font-bold text-xs text-[#182033]">
                    {item.caseNumber}
                  </span>
                </div>

                <Link
                  href={item.href}
                  className="text-[11px] font-bold text-[#4F6EF7] hover:text-[#3E5DE6] flex items-center gap-0.5"
                >
                  <span>{item.action}</span>
                  <ArrowRight className="h-3 w-3" />
                </Link>
              </div>

              <div>
                <div className="font-bold text-xs text-[#182033] flex items-center gap-1.5">
                  <Icon className={`h-3.5 w-3.5 ${isHigh ? 'text-[#EF4444]' : 'text-[#F59E0B]'}`} />
                  <span>{item.title}</span>
                </div>
                <p className="text-[11px] text-[#68738A] leading-snug mt-0.5">
                  {item.reason}
                </p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Footer */}
      <div className="pt-2 border-t border-[#E5E9F2] text-[10px] text-[#8E99AD] flex items-center justify-between">
        <span>Phase 8 Task Dispatch Queue</span>
        <span className="font-mono">Deterministic Prioritization</span>
      </div>
    </div>
  );
}
