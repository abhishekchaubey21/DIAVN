import React from 'react';
import Link from 'next/link';
import { getCases } from '@/lib/api';
import { CaseTable } from '@/components/CaseTable';
import { StatusBadge } from '@/components/StatusBadge';
import { PlusCircle, Search, Filter, FolderCheck, Download } from 'lucide-react';

export const dynamic = 'force-dynamic';

export default async function CasesPage() {
  const { cases, isMock } = await getCases();

  const totalCases = cases.length;
  const verifiedCount = cases.filter(c => c.status === 'verified').length;
  const flaggedCount = cases.filter(c => c.status === 'flagged' || c.risk_level === 'critical' || c.risk_level === 'high').length;
  const pendingCount = cases.filter(c => c.status === 'under_review' || c.status === 'verification_pending' || c.status === 'submitted').length;

  return (
    <div className="space-y-6 max-w-[1600px] mx-auto pb-12">
      {/* Header */}
      <div className="rounded-2xl border border-[#E5E9F2] bg-white p-5 sm:p-6 shadow-xs flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <div className="h-7 w-7 rounded-lg bg-[#4F6EF7]/10 text-[#4F6EF7] flex items-center justify-center">
              <FolderCheck className="h-4 w-4" />
            </div>
            <h1 className="text-xl font-extrabold text-[#182033]">
              Verification Cases Queue
            </h1>
            {isMock && <StatusBadge type="data_source" value="mock" size="sm" />}
          </div>
          <p className="text-xs text-[#68738A] mt-1">
            Complete registry of asset financing applications and multi-engine underwriting status
          </p>
        </div>

        <div className="flex items-center gap-3 shrink-0">
          <Link
            href="/cases/new"
            className="inline-flex items-center gap-1.5 bg-[#4F6EF7] hover:bg-[#3E5DE6] text-white text-xs font-bold px-4 py-2.5 rounded-xl shadow-xs transition-colors"
          >
            <PlusCircle className="h-4 w-4" />
            <span>Register New Case</span>
          </Link>
        </div>
      </div>

      {/* KPI Filter Strip */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl border border-[#E5E9F2] bg-white shadow-2xs">
          <span className="text-[10px] font-bold uppercase tracking-wider text-[#8E99AD] block">Total Registered</span>
          <span className="text-2xl font-extrabold font-mono text-[#182033] mt-1 block">{totalCases}</span>
          <span className="text-[10px] text-[#68738A]">All active portfolios</span>
        </div>
        <div className="p-4 rounded-xl border border-[#FECACA] bg-[#FEF2F2]/40 shadow-2xs">
          <span className="text-[10px] font-bold uppercase tracking-wider text-[#991B1B] block">Flagged for Audit</span>
          <span className="text-2xl font-extrabold font-mono text-[#991B1B] mt-1 block">{flaggedCount}</span>
          <span className="text-[10px] text-[#991B1B]">Requires underwriter action</span>
        </div>
        <div className="p-4 rounded-xl border border-[#FDE68A] bg-[#FFFBEB]/40 shadow-2xs">
          <span className="text-[10px] font-bold uppercase tracking-wider text-[#92400E] block">In Review Queue</span>
          <span className="text-2xl font-extrabold font-mono text-[#92400E] mt-1 block">{pendingCount}</span>
          <span className="text-[10px] text-[#92400E]">Pending verification</span>
        </div>
        <div className="p-4 rounded-xl border border-[#A7F3D0] bg-[#ECFDF5]/40 shadow-2xs">
          <span className="text-[10px] font-bold uppercase tracking-wider text-[#065F46] block">Verified Clean</span>
          <span className="text-2xl font-extrabold font-mono text-[#065F46] mt-1 block">{verifiedCount}</span>
          <span className="text-[10px] text-[#065F46]">Disbursement approved</span>
        </div>
      </div>

      {/* Main Table Card */}
      <div className="rounded-2xl border border-[#E5E9F2] bg-white shadow-xs p-5 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-[#E5E9F2]">
          <div className="text-xs font-bold uppercase tracking-wider text-[#182033]">
            Active Applications Registry
          </div>

          <div className="text-xs text-[#68738A] font-mono">
            Deterministic Phase 6 Risk Engine Active
          </div>
        </div>

        <CaseTable cases={cases} isMock={isMock} />
      </div>
    </div>
  );
}
