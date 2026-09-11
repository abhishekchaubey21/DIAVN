import React from 'react';
import Link from 'next/link';
import { getCases, getDealers } from '@/lib/api';
import { CaseTable } from '@/components/CaseTable';
import { StatusBadge } from '@/components/StatusBadge';
import { 
  ShieldAlert, 
  FileCheck, 
  Building2, 
  AlertTriangle, 
  PlusCircle, 
  TrendingUp, 
  Layers, 
  SearchCheck,
  Compass
} from 'lucide-react';

import { DemoScenarioDrawer } from '@/components/DemoScenarioDrawer';

export const dynamic = 'force-dynamic';

export default async function DashboardPage() {
  const { cases, isMock: casesAreMock } = await getCases();
  const { dealers, isMock: dealersAreMock } = await getDealers();

  const flaggedCases = cases.filter((c) => c.status === 'flagged' || c.risk_level === 'critical' || c.risk_level === 'high');
  const verifiedCases = cases.filter((c) => c.status === 'verified');
  const pendingCases = cases.filter((c) => c.status === 'submitted' || c.status === 'verification_pending' || c.status === 'under_review');
  const totalDisbursedExposure = cases.reduce((acc, c) => acc + (c.loan_amount || 0), 0);

  return (
    <div className="space-y-8">
      {/* Top Banner */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white">
              Underwriting & Verification Overview
            </h1>
            {casesAreMock && <StatusBadge type="data_source" value="mock" />}
          </div>
          <p className="mt-1 text-sm text-slate-400">
            Real-time equipment integrity monitoring, serial duplication tracking, and dealer network intelligence.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <DemoScenarioDrawer />
          <Link
            href="/cases/new"
            className="inline-flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold px-4 py-2.5 rounded-lg shadow-lg shadow-indigo-600/20 transition-all border border-indigo-400/30"
          >
            <PlusCircle className="h-4 w-4" />
            <span>Submit New Verification</span>
          </Link>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 shadow-lg">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Total Cases</span>
            <div className="p-2 rounded-lg bg-indigo-950/60 border border-indigo-500/30 text-indigo-400">
              <FileCheck className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold font-mono text-white">{cases.length}</span>
            <span className="text-xs text-slate-400">cases logged</span>
          </div>
          <div className="mt-2 text-xs text-slate-400">
            Total Exposure: <span className="text-slate-200 font-mono font-medium">₹{(totalDisbursedExposure / 100000).toFixed(2)} Lakhs</span>
          </div>
        </div>

        <div className="rounded-xl border border-rose-500/30 bg-rose-950/20 p-5 shadow-lg">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-rose-400">Flagged Anomalies</span>
            <div className="p-2 rounded-lg bg-rose-950/60 border border-rose-500/40 text-rose-400">
              <ShieldAlert className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold font-mono text-rose-300">{flaggedCases.length}</span>
            <span className="text-xs text-rose-400/80">high / critical risk</span>
          </div>
          <div className="mt-2 text-xs text-rose-300/80">
            Requires Underwriter / Field Audit
          </div>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 shadow-lg">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Verification Pending</span>
            <div className="p-2 rounded-lg bg-amber-950/60 border border-amber-500/30 text-amber-400">
              <SearchCheck className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold font-mono text-amber-300">{pendingCases.length}</span>
            <span className="text-xs text-slate-400">in queue</span>
          </div>
          <div className="mt-2 text-xs text-slate-400">
            {verifiedCases.length} cases verified clean
          </div>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 shadow-lg">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Monitored Dealers</span>
            <div className="p-2 rounded-lg bg-cyan-950/60 border border-cyan-500/30 text-cyan-400">
              <Building2 className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold font-mono text-cyan-300">{dealers.length}</span>
            <span className="text-xs text-slate-400">dealer networks</span>
          </div>
          <div className="mt-2 text-xs text-slate-400">
            {dealers.filter((d) => d.status === 'flagged' || d.status === 'under_review').length} under heightened review
          </div>
        </div>
      </div>

      {/* Synthetic Scenario Guidance Box */}
      <div className="rounded-xl border border-indigo-500/30 bg-gradient-to-r from-indigo-950/40 via-slate-900/60 to-slate-900/40 p-5 backdrop-blur-sm">
        <div className="flex items-center gap-2 text-indigo-400 font-semibold text-sm">
          <Compass className="h-4 w-4" />
          <span>Phase 1 Synthetic Test Scenarios (Seeded in Registry)</span>
        </div>
        <p className="mt-1 text-xs text-slate-300 leading-relaxed">
          The registry includes 4 deterministic test scenarios for local inspection:
        </p>
        <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          <Link
            href="/cases/CAS-2026-001"
            className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 hover:border-indigo-500/50 transition-colors"
          >
            <div className="text-xs font-bold text-emerald-400 flex items-center justify-between">
              <span>1. Clean Case</span>
              <span className="text-[10px] font-mono">CAS-2026-001</span>
            </div>
            <div className="text-[11px] text-slate-400 mt-1">Normal price & unique verified serial.</div>
          </Link>

          <Link
            href="/cases/CAS-2026-003"
            className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 hover:border-indigo-500/50 transition-colors"
          >
            <div className="text-xs font-bold text-orange-400 flex items-center justify-between">
              <span>2. Inflated Price</span>
              <span className="text-[10px] font-mono">CAS-2026-003</span>
            </div>
            <div className="text-[11px] text-slate-400 mt-1">+121% invoice variance vs market benchmark.</div>
          </Link>

          <Link
            href="/cases/CAS-2026-005"
            className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 hover:border-indigo-500/50 transition-colors"
          >
            <div className="text-xs font-bold text-rose-400 flex items-center justify-between">
              <span>3. Duplicate Serial</span>
              <span className="text-[10px] font-mono">CAS-2026-005</span>
            </div>
            <div className="text-[11px] text-slate-400 mt-1">Pump serial match against active loan.</div>
          </Link>

          <Link
            href="/cases/CAS-2026-007"
            className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 hover:border-indigo-500/50 transition-colors"
          >
            <div className="text-xs font-bold text-amber-400 flex items-center justify-between">
              <span>4. Collusion Anomaly</span>
              <span className="text-[10px] font-mono">CAS-2026-007</span>
            </div>
            <div className="text-[11px] text-slate-400 mt-1">Borrower site matches dealer business address.</div>
          </Link>
        </div>
      </div>

      {/* Case Table */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <Layers className="h-5 w-5 text-indigo-400" />
            Active Verification Pipeline Queue
          </h2>
          <Link href="/cases" className="text-xs text-indigo-400 hover:text-indigo-300 font-medium">
            View All ({cases.length}) →
          </Link>
        </div>
        <CaseTable cases={cases} isMock={casesAreMock} />
      </div>
    </div>
  );
}
