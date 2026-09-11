import React from 'react';
import Link from 'next/link';
import { getCases } from '@/lib/api';
import { MOCK_RISK_SCORES, MOCK_RISK_SIGNALS, MOCK_VERIFICATION_TASKS } from '@/lib/mockData';
import { StatusBadge } from '@/components/StatusBadge';
import { 
  ShieldAlert, 
  ArrowUpRight, 
  AlertTriangle, 
  SearchCheck, 
  CheckSquare2, 
  Building2, 
  Layers, 
  Filter,
  CheckCircle2,
  Clock,
  Sparkles
} from 'lucide-react';

export const dynamic = 'force-dynamic';

interface AlertsPageProps {
  searchParams?: Promise<{ filter?: string; sort?: string }>;
}

export default async function AlertsPage({ searchParams }: AlertsPageProps) {
  const { cases, isMock } = await getCases();
  const resolvedSearchParams = searchParams ? await searchParams : {};
  const currentFilter = resolvedSearchParams?.filter || 'all';

  // Extract actionable risk cases from real dataset
  const actionableCases = cases.filter((c) => {
    const isHighOrMed = c.risk_level === 'high' || c.risk_level === 'critical' || c.risk_level === 'medium';
    const isUnderReviewOrFlagged = c.status === 'flagged' || c.status === 'under_review' || c.status === 'verification_pending';
    return isHighOrMed || isUnderReviewOrFlagged;
  });

  // Sort: Highest risk first (by score or risk severity)
  const sortedCases = [...actionableCases].sort((a, b) => {
    const scoreA = MOCK_RISK_SCORES[a.case_number]?.overall_score ?? (a.risk_level === 'critical' ? 95 : a.risk_level === 'high' ? 85 : a.risk_level === 'medium' ? 50 : 10);
    const scoreB = MOCK_RISK_SCORES[b.case_number]?.overall_score ?? (b.risk_level === 'critical' ? 95 : b.risk_level === 'high' ? 85 : b.risk_level === 'medium' ? 50 : 10);
    return scoreB - scoreA;
  });

  // Apply active tab filter
  const filteredCases = sortedCases.filter((c) => {
    if (currentFilter === 'high') {
      return c.risk_level === 'high' || c.risk_level === 'critical';
    }
    if (currentFilter === 'medium') {
      return c.risk_level === 'medium';
    }
    if (currentFilter === 'unresolved') {
      return c.status === 'flagged' || c.status === 'under_review';
    }
    return true;
  });

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Page Header */}
      <div className="rounded-2xl border border-[#E5E9F2] bg-white p-6 sm:p-8 shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
          <div className="space-y-2 max-w-2xl">
            <div className="flex items-center gap-2.5">
              <span className="text-[11px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-[#EF4444]/10 text-[#991B1B] border border-[#FECACA]">
                Actionable Risk Queue
              </span>
              {isMock && <StatusBadge type="data_source" value="mock" size="sm" />}
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-[#182033]">
              Risk Alerts & Required Actions
            </h1>
            <p className="text-sm text-[#68738A] leading-relaxed">
              Prioritized queue of loan submissions exhibiting verification anomalies, pricing deviations, or duplicated evidence requiring underwriter review.
            </p>
          </div>

          <div className="flex items-center gap-3 shrink-0">
            <div className="text-right">
              <div className="text-2xl font-extrabold text-[#991B1B] font-mono leading-none">
                {sortedCases.length}
              </div>
              <div className="text-[11px] font-bold uppercase text-[#8E99AD] tracking-wider mt-1">
                Cases Requiring Review
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center justify-between gap-4 border-b border-[#E5E9F2] pb-4 overflow-x-auto">
        <div className="flex items-center gap-2">
          <Link
            href="/alerts"
            className={`px-3.5 py-2 rounded-xl text-xs font-bold transition-all ${
              currentFilter === 'all'
                ? 'bg-[#182033] text-white shadow-xs'
                : 'text-[#68738A] hover:text-[#182033] hover:bg-white'
            }`}
          >
            All Actionable ({sortedCases.length})
          </Link>
          <Link
            href="/alerts?filter=high"
            className={`px-3.5 py-2 rounded-xl text-xs font-bold transition-all ${
              currentFilter === 'high'
                ? 'bg-[#991B1B] text-white shadow-xs'
                : 'text-[#68738A] hover:text-[#182033] hover:bg-white'
            }`}
          >
            High Risk ({sortedCases.filter(c => c.risk_level === 'high' || c.risk_level === 'critical').length})
          </Link>
          <Link
            href="/alerts?filter=medium"
            className={`px-3.5 py-2 rounded-xl text-xs font-bold transition-all ${
              currentFilter === 'medium'
                ? 'bg-[#92400E] text-white shadow-xs'
                : 'text-[#68738A] hover:text-[#182033] hover:bg-white'
            }`}
          >
            Medium Risk ({sortedCases.filter(c => c.risk_level === 'medium').length})
          </Link>
          <Link
            href="/alerts?filter=unresolved"
            className={`px-3.5 py-2 rounded-xl text-xs font-bold transition-all ${
              currentFilter === 'unresolved'
                ? 'bg-[#182033] text-white shadow-xs'
                : 'text-[#68738A] hover:text-[#182033] hover:bg-white'
            }`}
          >
            Unresolved Flagged ({sortedCases.filter(c => c.status === 'flagged' || c.status === 'under_review').length})
          </Link>
        </div>

        <div className="text-xs text-[#8E99AD] font-medium hidden sm:block">
          Sorted by: <span className="font-bold text-[#182033]">Highest Risk First</span>
        </div>
      </div>

      {/* Alerts Cards List */}
      {filteredCases.length === 0 ? (
        <div className="rounded-2xl border border-[#E5E9F2] bg-white p-12 text-center space-y-3 shadow-xs">
          <div className="h-12 w-12 rounded-full bg-[#ECFDF5] text-[#10B981] flex items-center justify-center mx-auto">
            <CheckCircle2 className="h-6 w-6" />
          </div>
          <h3 className="text-base font-bold text-[#182033]">No Active Risk Alerts in this Filter</h3>
          <p className="text-xs text-[#68738A] max-w-md mx-auto">
            All verification cases in this category are either verified clean or do not require immediate underwriter action.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredCases.map((c) => {
            const riskData = MOCK_RISK_SCORES[c.case_number] || MOCK_RISK_SCORES[c.id];
            const score = riskData?.overall_score ?? (c.risk_level === 'critical' ? 95 : c.risk_level === 'high' ? 85 : c.risk_level === 'medium' ? 50 : 10);
            const signals = MOCK_RISK_SIGNALS[c.case_number] || MOCK_RISK_SIGNALS[c.id] || [];
            const tasks = MOCK_VERIFICATION_TASKS[c.case_number] || MOCK_VERIFICATION_TASKS[c.id] || [];
            const isHigh = c.risk_level === 'high' || c.risk_level === 'critical';

            const containerStyles = isHigh
              ? 'border-[#FECACA] bg-gradient-to-br from-[#FEF2F2]/60 via-white to-white'
              : 'border-[#FDE68A] bg-gradient-to-br from-[#FFFBEB]/40 via-white to-white';

            return (
              <div
                key={c.id}
                className={`rounded-2xl border p-6 shadow-xs transition-all hover:shadow-sm space-y-5 ${containerStyles}`}
              >
                {/* Alert Card Header */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#E5E9F2] pb-4">
                  <div className="flex items-start sm:items-center gap-3">
                    <div className={`h-10 w-10 rounded-xl flex items-center justify-center font-bold text-sm shrink-0 shadow-2xs ${
                      isHigh ? 'bg-[#FEF2F2] text-[#991B1B] border border-[#FECACA]' : 'bg-[#FFFBEB] text-[#92400E] border border-[#FDE68A]'
                    }`}>
                      <ShieldAlert className="h-5 w-5" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2.5">
                        <span className="font-mono font-bold text-base text-[#182033]">
                          {c.case_number}
                        </span>
                        <StatusBadge type="risk" value={c.risk_level} size="sm" />
                        <StatusBadge type="case_status" value={c.status} size="sm" />
                      </div>
                      <div className="text-xs text-[#68738A] flex items-center gap-2 mt-0.5">
                        <span className="font-semibold text-[#182033]">{c.dealer_name || c.dealer_id}</span>
                        <span>•</span>
                        <span>Asset: <strong className="text-[#182033]">{c.asset_type}</strong></span>
                        <span>•</span>
                        <span>Disbursement: <strong className="font-mono text-[#182033]">₹{c.loan_amount.toLocaleString('en-IN')}</strong></span>
                      </div>
                    </div>
                  </div>

                  {/* Score Pill */}
                  <div className="flex items-center gap-4 self-end sm:self-center">
                    <div className="text-right">
                      <div className={`text-2xl font-extrabold font-mono leading-none ${isHigh ? 'text-[#991B1B]' : 'text-[#92400E]'}`}>
                        {score} <span className="text-xs font-normal text-[#8E99AD]">/ 100</span>
                      </div>
                      <div className="text-[10px] font-bold uppercase tracking-wider text-[#8E99AD] mt-0.5">
                        Composite Risk Score
                      </div>
                    </div>

                    <Link
                      href={`/cases/${c.id}`}
                      className={`inline-flex items-center gap-1.5 text-xs font-bold px-4 py-2.5 rounded-xl shadow-xs transition-colors ${
                        isHigh
                          ? 'bg-[#991B1B] hover:bg-[#7F1D1D] text-white'
                          : 'bg-[#4F6EF7] hover:bg-[#3E5DE6] text-white'
                      }`}
                    >
                      <span>Review Case</span>
                      <ArrowUpRight className="h-4 w-4" />
                    </Link>
                  </div>
                </div>

                {/* Anomaly Signals & Recommended Action Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                  {/* Left: Signals Identified */}
                  <div className="p-4 rounded-xl bg-white/80 border border-[#E5E9F2] space-y-2">
                    <span className="font-bold text-[11px] uppercase tracking-wider text-[#68738A] block">
                      Detected Verification Signals
                    </span>
                    {signals.length > 0 ? (
                      <div className="space-y-1.5">
                        {signals.map((sig) => (
                          <div key={sig.id} className="flex items-start gap-2 text-[#182033]">
                            <span className="h-1.5 w-1.5 rounded-full bg-[#EF4444] mt-1.5 shrink-0" />
                            <p className="leading-snug">{sig.description}</p>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-[#68738A] leading-relaxed">
                        {riskData?.summary_reasoning || c.notes || 'Anomalous telemetry or pricing variance recorded.'}
                      </p>
                    )}
                  </div>

                  {/* Right: Recommended Operational Action & Tasks */}
                  <div className="p-4 rounded-xl bg-white/80 border border-[#E5E9F2] space-y-2">
                    <span className="font-bold text-[11px] uppercase tracking-wider text-[#68738A] block">
                      Recommended Action & Audit Tasks
                    </span>
                    <div className="space-y-1.5 text-[#182033]">
                      <div className="font-semibold text-[#991B1B] flex items-center gap-1.5">
                        <CheckSquare2 className="h-4 w-4 text-[#991B1B]" />
                        <span>
                          {isHigh
                            ? 'Field Verification Recommended — Multi-anomaly stack identified'
                            : 'Desk Audit / Invoice Price Justification Required'}
                        </span>
                      </div>
                      {tasks.length > 0 ? (
                        <div className="text-[#68738A] space-y-1 pt-1">
                          {tasks.map((t) => (
                            <div key={t.id} className="flex items-center justify-between text-[11px]">
                              <span>• {t.instructions}</span>
                              <span className="font-bold uppercase text-[10px] text-[#92400E] px-1.5 py-0.5 rounded bg-[#FFFBEB] border border-[#FDE68A]">
                                {t.status}
                              </span>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-[#68738A] text-[11px]">
                          Automated n8n webhook notification dispatched for risk triage.
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
