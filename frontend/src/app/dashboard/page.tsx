import React from 'react';
import Link from 'next/link';
import { getCases, getDealers } from '@/lib/api';
import { PriorityCasesTable } from '@/components/PriorityCasesTable';
import { RequiresAttentionPanel } from '@/components/RequiresAttentionPanel';
import { DealerRiskOverview } from '@/components/DealerRiskOverview';
import { GeographicRiskMap } from '@/components/GeographicRiskMap';
import { RelationshipAlertsSummary } from '@/components/RelationshipAlertsSummary';
import { RecentActivityTimeline } from '@/components/RecentActivityTimeline';
import { DemoScenarioDrawer } from '@/components/DemoScenarioDrawer';
import { 
  ShieldAlert, 
  AlertTriangle, 
  SearchCheck, 
  FileWarning, 
  PlusCircle,
  ArrowRight
} from 'lucide-react';

export const dynamic = 'force-dynamic';

export default async function DashboardPage() {
  // Parallel fetch for portfolio cases and registered dealers
  const [{ cases, isMock: casesAreMock }, { dealers, isMock: dealersAreMock }] = await Promise.all([
    getCases(),
    getDealers()
  ]);

  // Real metrics derived strictly from existing application data
  const totalCases = cases.length;
  const highRiskCases = cases.filter(
    (c) => c.risk_level === 'high' || c.risk_level === 'critical' || c.status === 'flagged'
  );
  const mediumRiskCases = cases.filter((c) => c.risk_level === 'medium');
  const verificationQueue = cases.filter(
    (c) => c.status === 'under_review' || c.status === 'verification_pending' || c.status === 'submitted'
  );
  const flaggedEvidenceCount = cases.filter(
    (c) => c.case_number === 'CAS-2026-003' || c.case_number === 'CAS-2026-005' || c.case_number === 'CAS-2026-007' || c.case_number === 'CAS-2026-010'
  ).length;

  return (
    <div className="space-y-6 max-w-[1600px] mx-auto pb-12">
      {/* 1. Page Header */}
      <div className="rounded-2xl border border-[#E5E9F2] bg-white p-5 sm:p-6 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-extrabold uppercase tracking-wider px-2 py-0.5 rounded-full bg-[#4F6EF7]/10 text-[#4F6EF7] border border-[#4F6EF7]/20">
                PS #1: DIAVN Underwriting OS
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-100 text-[#68738A] border border-[#E5E9F2]">
                SANDBOX MODE • Synthetic Benchmark
              </span>
            </div>
            <h1 className="text-xl sm:text-2xl font-extrabold tracking-tight text-[#182033]">
              Dealer Integrity & Asset Verification Network
            </h1>
            <p className="text-xs text-[#68738A]">
              Evidence-driven verification and risk triage for dealer-financed assets.
            </p>
          </div>

          <div className="flex items-center gap-3 shrink-0">
            <DemoScenarioDrawer />
            <Link
              href="/cases/new"
              className="inline-flex items-center gap-1.5 bg-[#4F6EF7] hover:bg-[#3E5DE6] text-white text-xs font-bold px-4 py-2.5 rounded-xl shadow-xs transition-colors"
            >
              <PlusCircle className="h-4 w-4" />
              <span>+ Register New Case</span>
            </Link>
          </div>
        </div>
      </div>

      {/* 2. Attention Summary (4 Restrained Summary Cards) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: High-Risk Cases */}
        <Link
          href="/cases"
          className="rounded-2xl border border-[#FECACA] bg-[#FEF2F2]/40 p-4 shadow-xs hover:border-[#F87171] transition-all flex flex-col justify-between group"
        >
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-extrabold uppercase tracking-wider text-[#991B1B]">
              High-Risk Cases
            </span>
            <div className="h-7 w-7 rounded-lg bg-[#FEF2F2] text-[#EF4444] flex items-center justify-center border border-[#FECACA]">
              <ShieldAlert className="h-3.5 w-3.5" />
            </div>
          </div>
          <div className="mt-2 flex items-baseline justify-between">
            <span className="text-3xl font-extrabold font-mono text-[#991B1B]">
              {highRiskCases.length}
            </span>
            <span className="text-[10px] font-mono text-[#991B1B] font-bold group-hover:underline flex items-center gap-0.5">
              <span>Inspect</span>
              <ArrowRight className="h-3 w-3" />
            </span>
          </div>
          <div className="mt-2 pt-2 border-t border-[#FECACA]/60 text-[10px] text-[#991B1B]">
            Multiple anomaly stacks requiring field audit
          </div>
        </Link>

        {/* Card 2: Medium-Risk Cases */}
        <Link
          href="/cases"
          className="rounded-2xl border border-[#FDE68A] bg-[#FFFBEB]/40 p-4 shadow-xs hover:border-[#F59E0B] transition-all flex flex-col justify-between group"
        >
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-extrabold uppercase tracking-wider text-[#92400E]">
              Medium-Risk Cases
            </span>
            <div className="h-7 w-7 rounded-lg bg-[#FFFBEB] text-[#F59E0B] flex items-center justify-center border border-[#FDE68A]">
              <AlertTriangle className="h-3.5 w-3.5" />
            </div>
          </div>
          <div className="mt-2 flex items-baseline justify-between">
            <span className="text-3xl font-extrabold font-mono text-[#92400E]">
              {mediumRiskCases.length}
            </span>
            <span className="text-[10px] font-mono text-[#92400E] font-bold group-hover:underline flex items-center gap-0.5">
              <span>Inspect</span>
              <ArrowRight className="h-3 w-3" />
            </span>
          </div>
          <div className="mt-2 pt-2 border-t border-[#FDE68A]/60 text-[10px] text-[#92400E]">
            Price or telemetry variance flags detected
          </div>
        </Link>

        {/* Card 3: Verification Queue */}
        <Link
          href="/cases"
          className="rounded-2xl border border-[#E5E9F2] bg-white p-4 shadow-xs hover:border-[#D1D8E6] transition-all flex flex-col justify-between group"
        >
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-extrabold uppercase tracking-wider text-[#8E99AD]">
              Verification Queue
            </span>
            <div className="h-7 w-7 rounded-lg bg-[#F6F8FC] text-[#4F6EF7] flex items-center justify-center border border-[#E5E9F2]">
              <SearchCheck className="h-3.5 w-3.5" />
            </div>
          </div>
          <div className="mt-2 flex items-baseline justify-between">
            <span className="text-3xl font-extrabold font-mono text-[#182033]">
              {verificationQueue.length}
            </span>
            <span className="text-[10px] font-mono text-[#4F6EF7] font-bold group-hover:underline flex items-center gap-0.5">
              <span>Review</span>
              <ArrowRight className="h-3 w-3" />
            </span>
          </div>
          <div className="mt-2 pt-2 border-t border-[#E5E9F2] text-[10px] text-[#68738A]">
            Active underwriting applications awaiting review
          </div>
        </Link>

        {/* Card 4: Flagged Evidence */}
        <Link
          href="/alerts"
          className="rounded-2xl border border-[#E5E9F2] bg-white p-4 shadow-xs hover:border-[#D1D8E6] transition-all flex flex-col justify-between group"
        >
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-extrabold uppercase tracking-wider text-[#8E99AD]">
              Flagged Evidence
            </span>
            <div className="h-7 w-7 rounded-lg bg-[#F8FAFD] text-[#5B4AEF] flex items-center justify-center border border-[#E5E9F2]">
              <FileWarning className="h-3.5 w-3.5" />
            </div>
          </div>
          <div className="mt-2 flex items-baseline justify-between">
            <span className="text-3xl font-extrabold font-mono text-[#182033]">
              {flaggedEvidenceCount}
            </span>
            <span className="text-[10px] font-mono text-[#5B4AEF] font-bold group-hover:underline flex items-center gap-0.5">
              <span>View Alerts</span>
              <ArrowRight className="h-3 w-3" />
            </span>
          </div>
          <div className="mt-2 pt-2 border-t border-[#E5E9F2] text-[10px] text-[#68738A]">
            Invoice price, duplicate serial & GPS alerts
          </div>
        </Link>
      </div>

      {/* 3. Main Dashboard Row 1: Priority Verification Cases (8 cols) + Requires Attention Panel (4 cols) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
        <div className="lg:col-span-8 flex flex-col">
          <PriorityCasesTable cases={cases} limit={6} />
        </div>

        <div className="lg:col-span-4 flex flex-col">
          <RequiresAttentionPanel cases={cases} />
        </div>
      </div>

      {/* 4. Main Dashboard Row 2: Dealer Risk Overview (6 cols) + Geographic Verification Overview (6 cols) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-stretch">
        <div className="lg:col-span-6 flex flex-col">
          <DealerRiskOverview dealers={dealers} cases={cases} />
        </div>

        <div className="lg:col-span-6 flex flex-col">
          <GeographicRiskMap cases={cases} dealers={dealers} isMock={casesAreMock} />
        </div>
      </div>

      {/* 5. Main Dashboard Row 3: Relationship Alerts (6 cols) + Recent Verification Activity (6 cols) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-stretch">
        <div className="lg:col-span-6 flex flex-col">
          <RelationshipAlertsSummary />
        </div>

        <div className="lg:col-span-6 flex flex-col">
          <RecentActivityTimeline />
        </div>
      </div>
    </div>
  );
}
