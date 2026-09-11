'use client';

import React from 'react';
import Link from 'next/link';
import { Network, AlertTriangle, ArrowRight, ShieldAlert } from 'lucide-react';

export function RelationshipAlertsSummary() {
  const relationshipAlerts = [
    {
      id: 'rel-1',
      dealer: 'Radiant AgroTech Distributions (DLR-RAD-03)',
      customer: 'GreenFields Agri Enterprises',
      issue: 'Claimed installation address matches dealer equipment yard in Hebbal, Bengaluru.',
      caseId: 'CAS-2026-007'
    },
    {
      id: 'rel-2',
      dealer: 'Radiant AgroTech Distributions (DLR-RAD-03)',
      customer: 'Anita Sundaram',
      issue: 'Borrower contact phone matches dealer director registered KYC record.',
      caseId: 'CAS-2026-008'
    },
    {
      id: 'rel-3',
      dealer: 'Cross-Dealer Correlation',
      customer: 'Multi-Borrower Shared Serial',
      issue: 'Solar Pump Serial ASP-2025-99881 registered to active loans across Pune and Bengaluru.',
      caseId: 'CAS-2026-005'
    }
  ];

  return (
    <div className="rounded-2xl border border-[#E5E9F2] bg-white p-5 shadow-xs flex flex-col justify-between space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-[#E5E9F2]">
        <div className="flex items-center gap-2">
          <div className="h-7 w-7 rounded-lg bg-[#5B4AEF]/10 text-[#5B4AEF] flex items-center justify-center">
            <Network className="h-4 w-4" />
          </div>
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-[#182033]">
              Relationship Alerts
            </h3>
            <span className="text-[10px] text-[#68738A]">
              Multi-entity correlation & collusion indicators
            </span>
          </div>
        </div>

        <Link
          href="/relationships"
          className="text-[11px] font-bold text-[#4F6EF7] hover:text-[#3E5DE6] flex items-center gap-1"
        >
          <span>Open Investigation Graph</span>
          <ArrowRight className="h-3 w-3" />
        </Link>
      </div>

      {/* Alert Items List */}
      <div className="space-y-2.5">
        {relationshipAlerts.map((alt) => (
          <div
            key={alt.id}
            className="p-3 rounded-xl border border-[#FECACA] bg-[#FEF2F2]/40 transition-all space-y-1.5"
          >
            <div className="flex items-center justify-between">
              <span className="font-bold text-xs text-[#182033] truncate">
                {alt.dealer}
              </span>
              <Link
                href={`/cases/${alt.caseId}`}
                className="font-mono text-[10px] font-bold text-[#4F6EF7] hover:underline shrink-0"
              >
                {alt.caseId}
              </Link>
            </div>

            <p className="text-[11px] text-[#991B1B] font-medium leading-snug">
              {alt.issue}
            </p>
          </div>
        ))}
      </div>

      {/* Footer */}
      <div className="pt-2 border-t border-[#E5E9F2] text-[10px] text-[#8E99AD] flex items-center justify-between">
        <span>Phase 7 Network Analysis</span>
        <span className="font-mono">Zero Double-Counting (Weight: 0.0)</span>
      </div>
    </div>
  );
}
