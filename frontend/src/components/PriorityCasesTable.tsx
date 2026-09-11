'use client';

import React from 'react';
import Link from 'next/link';
import { Case } from '@/types';
import { StatusBadge } from './StatusBadge';
import { ArrowUpRight, ChevronRight, Layers } from 'lucide-react';
import { MOCK_RISK_SCORES } from '@/lib/mockData';

interface PriorityCasesTableProps {
  cases: Case[];
  limit?: number;
}

export function PriorityCasesTable({ cases = [], limit = 6 }: PriorityCasesTableProps) {
  // Sort priority cases: Critical & High risk first, then flagged / verification_pending
  const sortedCases = [...cases].sort((a, b) => {
    const scoreA = MOCK_RISK_SCORES[a.case_number]?.overall_score ?? (a.risk_level === 'critical' ? 95 : a.risk_level === 'high' ? 82 : a.risk_level === 'medium' ? 50 : 10);
    const scoreB = MOCK_RISK_SCORES[b.case_number]?.overall_score ?? (b.risk_level === 'critical' ? 95 : b.risk_level === 'high' ? 82 : b.risk_level === 'medium' ? 50 : 10);
    return scoreB - scoreA;
  });

  const displayCases = sortedCases.slice(0, limit);

  const getTopSignal = (c: Case): string => {
    if (c.case_number === 'CAS-2026-007') return 'Duplicate Serial + Image Reuse';
    if (c.case_number === 'CAS-2026-005') return 'Cross-Case Duplicate Serial (ASP-99881)';
    if (c.case_number === 'CAS-2026-003') return 'Invoice Price Variance (+121%)';
    if (c.case_number === 'CAS-2026-010') return 'EXIF GPS Telemetry Variance (74.8 km)';
    if (c.case_number === 'CAS-2026-006') return 'External Serial Collision';
    if (c.case_number === 'CAS-2026-008') return 'Shared Director Contact Cluster';
    if (c.risk_level === 'low') return 'Verified Clean Registry';
    return c.notes?.split('-')[1]?.trim() || 'Pending Engine Execution';
  };

  return (
    <div className="rounded-2xl border border-[#E5E9F2] bg-white shadow-xs overflow-hidden">
      {/* Header */}
      <div className="p-4 sm:p-5 border-b border-[#E5E9F2] flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="h-7 w-7 rounded-lg bg-[#4F6EF7]/10 text-[#4F6EF7] flex items-center justify-center">
            <Layers className="h-4 w-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-[#182033]">Priority Verification Cases</h3>
            <p className="text-xs text-[#68738A]">High-risk and pending verification workload requiring triage</p>
          </div>
        </div>

        <Link
          href="/cases"
          className="text-xs font-bold text-[#4F6EF7] hover:text-[#3E5DE6] flex items-center gap-1"
        >
          <span>View All ({cases.length})</span>
          <ChevronRight className="h-3.5 w-3.5" />
        </Link>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-[#E5E9F2] bg-[#F8FAFD] text-[10px] font-extrabold uppercase tracking-wider text-[#8E99AD]">
              <th className="py-2.5 px-4">Case ID</th>
              <th className="py-2.5 px-4">Customer</th>
              <th className="py-2.5 px-4">Dealer</th>
              <th className="py-2.5 px-4">Asset</th>
              <th className="py-2.5 px-4">Risk</th>
              <th className="py-2.5 px-4">Top Evidence Signal</th>
              <th className="py-2.5 px-4">Status</th>
              <th className="py-2.5 px-4 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#F1F4FA] text-xs">
            {displayCases.map((c) => {
              const score = MOCK_RISK_SCORES[c.case_number]?.overall_score ?? (c.risk_level === 'critical' ? 95 : c.risk_level === 'high' ? 82 : c.risk_level === 'medium' ? 50 : 10);
              const topSignal = getTopSignal(c);

              return (
                <tr key={c.id} className="hover:bg-[#F8FAFD] transition-colors">
                  {/* Case ID */}
                  <td className="py-3 px-4">
                    <Link
                      href={`/cases/${c.id}`}
                      className="font-mono font-bold text-[#4F6EF7] hover:underline"
                    >
                      {c.case_number}
                    </Link>
                  </td>

                  {/* Customer */}
                  <td className="py-3 px-4 text-[#182033] font-medium truncate max-w-[130px]">
                    {c.customer_name || 'Borrower'}
                  </td>

                  {/* Dealer */}
                  <td className="py-3 px-4 text-[#68738A] font-mono text-[11px] truncate max-w-[140px]">
                    {c.dealer_name || c.dealer_id}
                  </td>

                  {/* Asset */}
                  <td className="py-3 px-4 text-[#182033] truncate max-w-[140px]">
                    {c.asset_type}
                  </td>

                  {/* Risk */}
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-1.5">
                      <StatusBadge type="risk" value={c.risk_level} size="sm" />
                      <span className="font-mono text-[10px] text-[#8E99AD] font-bold">
                        {score}
                      </span>
                    </div>
                  </td>

                  {/* Top Evidence Signal */}
                  <td className="py-3 px-4 text-[#68738A] text-[11px] max-w-[200px] truncate">
                    <span className={c.risk_level === 'critical' || c.risk_level === 'high' ? 'text-[#991B1B] font-semibold' : ''}>
                      {topSignal}
                    </span>
                  </td>

                  {/* Status */}
                  <td className="py-3 px-4">
                    <StatusBadge type="case_status" value={c.status} size="sm" />
                  </td>

                  {/* Action */}
                  <td className="py-3 px-4 text-right">
                    <Link
                      href={`/cases/${c.id}`}
                      className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-white border border-[#E5E9F2] text-[11px] font-bold text-[#4F6EF7] hover:bg-[#4F6EF7] hover:text-white transition-colors shadow-2xs"
                    >
                      <span>View</span>
                      <ArrowUpRight className="h-3 w-3" />
                    </Link>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
