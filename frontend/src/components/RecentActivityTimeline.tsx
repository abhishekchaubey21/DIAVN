'use client';

import React from 'react';
import Link from 'next/link';
import { 
  Activity, 
  FileText, 
  Camera, 
  MapPin, 
  ShieldCheck, 
  CheckSquare, 
  Clock 
} from 'lucide-react';

export function RecentActivityTimeline() {
  const activities = [
    {
      id: 'act-1',
      time: '10 mins ago',
      caseId: 'CAS-2026-007',
      event: 'Deterministic Risk Assessment Computed',
      detail: 'Phase 6 Engine computed Score: 92 (HIGH) based on 4 stacked verification anomalies.',
      icon: ShieldCheck,
      color: 'text-[#EF4444] bg-[#FEF2F2]'
    },
    {
      id: 'act-2',
      time: '25 mins ago',
      caseId: 'CAS-2026-010',
      event: 'GPS Geolocation Variance Identified',
      detail: 'Image EXIF location variance (74.8 km) exceeds 10km threshold. Field visit dispatched.',
      icon: MapPin,
      color: 'text-[#F59E0B] bg-[#FFFBEB]'
    },
    {
      id: 'act-3',
      time: '1 hour ago',
      caseId: 'CAS-2026-005',
      event: 'Cross-Case Duplicate Serial Flagged',
      detail: 'Equipment serial ASP-2025-99881 matches existing active loan in Pune registry.',
      icon: CheckSquare,
      color: 'text-[#EF4444] bg-[#FEF2F2]'
    },
    {
      id: 'act-4',
      time: '2 hours ago',
      caseId: 'CAS-2026-003',
      event: 'Invoice Benchmark Verification Completed',
      detail: 'Unit price exceeds category benchmark by +121%. Flagged for underwriter review.',
      icon: FileText,
      color: 'text-[#F59E0B] bg-[#FFFBEB]'
    },
    {
      id: 'act-5',
      time: '3 hours ago',
      caseId: 'CAS-2026-001',
      event: 'Pipeline Verification Completed Clean',
      detail: 'All 7 deterministic checks PASSED. Risk Score: 8 (LOW). Ready for disbursement.',
      icon: ShieldCheck,
      color: 'text-[#10B981] bg-[#ECFDF5]'
    }
  ];

  return (
    <div className="rounded-2xl border border-[#E5E9F2] bg-white p-5 shadow-xs flex flex-col justify-between space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-[#E5E9F2]">
        <div className="flex items-center gap-2">
          <div className="h-7 w-7 rounded-lg bg-[#4F6EF7]/10 text-[#4F6EF7] flex items-center justify-center">
            <Activity className="h-4 w-4" />
          </div>
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-[#182033]">
              Recent Verification Activity
            </h3>
            <span className="text-[10px] text-[#68738A]">
              Deterministic audit trail events across underwriting pipeline
            </span>
          </div>
        </div>

        <span className="text-[10px] font-mono text-[#8E99AD] flex items-center gap-1">
          <Clock className="h-3 w-3" />
          <span>Real-time Log</span>
        </span>
      </div>

      {/* Activity Timeline List */}
      <div className="space-y-3">
        {activities.map((act) => {
          const Icon = act.icon;
          return (
            <div key={act.id} className="flex items-start gap-3 text-xs">
              <div className={`h-7 w-7 rounded-lg flex items-center justify-center shrink-0 mt-0.5 ${act.color}`}>
                <Icon className="h-3.5 w-3.5" />
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                  <span className="font-bold text-[#182033] truncate">
                    {act.event}
                  </span>
                  <span className="text-[10px] font-mono text-[#8E99AD] shrink-0">
                    {act.time}
                  </span>
                </div>

                <p className="text-[11px] text-[#68738A] leading-snug mt-0.5">
                  {act.detail}
                </p>

                <div className="mt-1">
                  <Link
                    href={`/cases/${act.caseId}`}
                    className="font-mono text-[10px] font-bold text-[#4F6EF7] hover:underline"
                  >
                    {act.caseId}
                  </Link>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Footer */}
      <div className="pt-2 border-t border-[#E5E9F2] text-[10px] text-[#8E99AD] flex items-center justify-between">
        <span>Phase 9 Outbox & Audit Pipeline</span>
        <span className="font-mono">Audit Traceability</span>
      </div>
    </div>
  );
}
