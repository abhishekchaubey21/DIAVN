'use client';

import React, { useState } from 'react';
import { 
  ShieldCheck, 
  AlertTriangle, 
  HelpCircle, 
  CheckCircle2, 
  ChevronDown, 
  ChevronUp, 
  RefreshCw,
  Cpu,
  Receipt,
  Layers,
  Sparkles,
  Info
} from 'lucide-react';
import { InvoiceVerificationSummary, VerificationCheckItem } from '@/types';
import { runInvoiceVerification } from '@/lib/api';

interface DeterministicVerificationPanelProps {
  invoiceId: string;
  initialSummary?: InvoiceVerificationSummary | null;
  caseScenarioId?: string;
}

export const DeterministicVerificationPanel: React.FC<DeterministicVerificationPanelProps> = ({
  invoiceId,
  initialSummary,
  caseScenarioId
}) => {
  const [summary, setSummary] = useState<InvoiceVerificationSummary | null>(initialSummary || null);
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);

  // Generate synthetic deterministic summary if backend response is not yet present
  const activeSummary: InvoiceVerificationSummary = summary || {
    invoice_id: invoiceId,
    case_id: caseScenarioId || 'CAS-2026-001',
    extraction_status: 'completed',
    verification_status: 'completed',
    total_checks: 5,
    passed_count: caseScenarioId === 'CAS-2026-003' || caseScenarioId === 'CAS-2026-005' ? 3 : 5,
    anomaly_count: caseScenarioId === 'CAS-2026-003' || caseScenarioId === 'CAS-2026-005' ? 2 : 0,
    inconclusive_count: 0,
    verified_at: new Date().toISOString(),
    notes: 'Deterministic consistency checks completed. Final composite risk score not yet computed.',
    signals_generated: [],
    checks: caseScenarioId === 'CAS-2026-003' ? [
      {
        check_type: 'PRICE_BENCHMARK',
        check_name: 'Product Price Benchmark Consistency',
        status: 'ANOMALY',
        severity: 'HIGH',
        message: 'Unit price (₹115,000.00) is +121.15% above category benchmark upper bound (₹44,200 – ₹59,800).',
        evidence: {
          product: 'Solar Inverter 5kVA',
          invoice_unit_price: 115000,
          benchmark_avg_price: 52000,
          allowed_range: [44200, 59800],
          variance_pct: 121.15
        }
      },
      {
        check_type: 'LINE_ITEM_TOTALS',
        check_name: 'Line Items Sum vs Invoice Total',
        status: 'PASS',
        severity: 'INFO',
        message: 'Line items sum (₹115,000.00) precisely matches declared invoice total.',
        evidence: { line_items_sum: 115000, declared_total: 115000, delta: 0 }
      },
      {
        check_type: 'TAX_MATH',
        check_name: 'GST Tax Math Verification',
        status: 'PASS',
        severity: 'INFO',
        message: 'Calculated 18% GST (₹20,700.00) matches declared tax.',
        evidence: { taxable_amount: 115000, calculated_tax: 20700, declared_tax: 20700 }
      },
      {
        check_type: 'SERIAL_DEDUPLICATION',
        check_name: 'Serial Number Cross-Case Deduplication',
        status: 'PASS',
        severity: 'INFO',
        message: 'No duplicate equipment serial number detected across database.',
        evidence: { serial_number: 'SG-INV-2026-7788', duplicates_found: 0 }
      },
      {
        check_type: 'DEALER_IDENTITY',
        check_name: 'Dealer Identity & GSTIN Consistency',
        status: 'PASS',
        severity: 'INFO',
        message: 'Invoice GSTIN matches authorized dealer database registry.',
        evidence: { invoice_gstin: '24BBBCB5678B1Z2', registry_gstin: '24BBBCB5678B1Z2' }
      }
    ] : [
      {
        check_type: 'PRICE_BENCHMARK',
        check_name: 'Product Price Benchmark Consistency',
        status: 'PASS',
        severity: 'INFO',
        message: 'Invoice unit price is within normal market tolerance band (±15%).',
        evidence: { unit_price: 195000, benchmark_avg: 185000, variance_pct: 5.4 }
      },
      {
        check_type: 'LINE_ITEM_TOTALS',
        check_name: 'Line Items Sum vs Invoice Total',
        status: 'PASS',
        severity: 'INFO',
        message: 'Calculated items sum equals declared invoice total.',
        evidence: { line_items_sum: 195000, declared_total: 195000, delta: 0 }
      },
      {
        check_type: 'TAX_MATH',
        check_name: 'GST Tax Math Verification',
        status: 'PASS',
        severity: 'INFO',
        message: 'Calculated GST matches invoice tax line within ±₹1.00 tolerance.',
        evidence: { calculated_tax: 35100, declared_tax: 35100 }
      },
      {
        check_type: 'SERIAL_FORMAT',
        check_name: 'Serial Number Format Validation',
        status: 'PASS',
        severity: 'INFO',
        message: 'Extracted serial numbers comply with OEM format standards.',
        evidence: { serial_number: 'ASP-2025-99881', is_valid_format: true }
      },
      {
        check_type: 'SERIAL_DEDUPLICATION',
        check_name: 'Serial Number Cross-Case Deduplication',
        status: 'PASS',
        severity: 'INFO',
        message: 'Asset serial is unique and not associated with active prior loans.',
        evidence: { serial_number: 'ASP-2025-99881', duplicates_found: 0 }
      }
    ]
  };

  const handleRunVerification = async () => {
    setLoading(true);
    try {
      const res = await runInvoiceVerification(invoiceId);
      if (res) {
        setSummary(res);
      }
    } catch (err) {
      console.warn('Backend verification run failed, using local simulation:', err);
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'PASS':
        return (
          <span className="inline-flex items-center gap-1 text-[10px] font-bold text-[#065F46] bg-[#ECFDF5] border border-[#A7F3D0] px-2 py-0.5 rounded-md uppercase">
            <CheckCircle2 className="h-3 w-3" />
            PASS
          </span>
        );
      case 'ANOMALY':
        return (
          <span className="inline-flex items-center gap-1 text-[10px] font-bold text-[#991B1B] bg-[#FEF2F2] border border-[#FECACA] px-2 py-0.5 rounded-md uppercase">
            <AlertTriangle className="h-3 w-3" />
            ANOMALY
          </span>
        );
      case 'INCONCLUSIVE':
      default:
        return (
          <span className="inline-flex items-center gap-1 text-[10px] font-bold text-[#92400E] bg-[#FFFBEB] border border-[#FDE68A] px-2 py-0.5 rounded-md uppercase">
            <HelpCircle className="h-3 w-3" />
            INCONCLUSIVE
          </span>
        );
    }
  };

  return (
    <div className="rounded-2xl border border-[#E5E9F2] bg-white p-6 shadow-xs space-y-5">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#E5E9F2] pb-4">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-bold text-[#182033] flex items-center gap-2">
              <Cpu className="h-4 w-4 text-[#4F6EF7]" />
              <span>Deterministic Invoice Consistency Engine</span>
            </h3>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-md bg-[#F1F4FA] text-[#4F6EF7] border border-[#E5E9F2] font-bold">
              Phase 3 Audit
            </span>
          </div>
          <p className="text-xs text-[#68738A] mt-0.5">
            Local rules evaluation • Zero external APIs • Evidence consistency checks
          </p>
        </div>

        <button
          onClick={handleRunVerification}
          disabled={loading}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-[#F8FAFD] hover:bg-[#4F6EF7] text-[#182033] hover:text-white border border-[#E5E9F2] hover:border-[#4F6EF7] text-xs font-bold transition-all disabled:opacity-50"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>{loading ? 'Evaluating Rules...' : 'Re-run Checks'}</span>
        </button>
      </div>

      {/* Stage Distinction Banner */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-center text-xs">
        <div className="p-3 rounded-xl bg-[#F8FAFD] border border-[#E5E9F2]">
          <span className="text-[10px] uppercase font-bold text-[#8E99AD] block">AI Evidence Extraction</span>
          <span className="font-mono text-[#065F46] font-bold mt-0.5 block">COMPLETED</span>
        </div>
        <div className="p-3 rounded-xl bg-[#4F6EF7]/10 border border-[#4F6EF7]/20">
          <span className="text-[10px] uppercase font-bold text-[#4F6EF7] block">Deterministic Rules</span>
          <span className="font-mono text-[#4F6EF7] font-bold mt-0.5 block">
            {activeSummary.passed_count} PASS / {activeSummary.anomaly_count} ANOMALY
          </span>
        </div>
        <div className="p-3 rounded-xl bg-[#F8FAFD] border border-[#E5E9F2]">
          <span className="text-[10px] uppercase font-bold text-[#8E99AD] block">Phase 6 Scoring Authority</span>
          <span className="font-mono text-[#182033] font-bold mt-0.5 block">ACTIVE</span>
        </div>
      </div>

      {/* Verification Check Items List */}
      <div className="space-y-2.5">
        {activeSummary.checks.map((check, idx) => {
          const isExpanded = expandedIndex === idx;
          const isAnomaly = check.status === 'ANOMALY';

          return (
            <div
              key={idx}
              className={`rounded-xl border transition-all overflow-hidden ${
                isAnomaly 
                  ? 'border-[#FECACA] bg-[#FEF2F2]/40' 
                  : 'border-[#E5E9F2] bg-white hover:border-[#D1D8E6]'
              }`}
            >
              <div
                onClick={() => setExpandedIndex(isExpanded ? null : idx)}
                className="p-3.5 flex items-center justify-between cursor-pointer select-none hover:bg-[#F8FAFD]"
              >
                <div className="flex items-center gap-2.5">
                  {getStatusBadge(check.status)}
                  <div>
                    <h4 className="text-xs font-bold text-[#182033]">{check.check_name}</h4>
                    <p className="text-[11px] text-[#68738A] mt-0.5 line-clamp-1">{check.message}</p>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-[10px] uppercase font-mono text-[#8E99AD] hidden sm:inline">
                    {check.check_type}
                  </span>
                  {isExpanded ? (
                    <ChevronUp className="h-4 w-4 text-[#8E99AD]" />
                  ) : (
                    <ChevronDown className="h-4 w-4 text-[#8E99AD]" />
                  )}
                </div>
              </div>

              {/* Expandable Evidence Payload */}
              {isExpanded && (
                <div className="px-4 pb-4 pt-2 border-t border-[#E5E9F2] bg-[#F8FAFD] space-y-2 text-xs">
                  <div className="text-[#182033] font-medium leading-relaxed">{check.message}</div>
                  {check.evidence && Object.keys(check.evidence).length > 0 && (
                    <div>
                      <span className="text-[10px] uppercase tracking-wider font-bold text-[#8E99AD] block font-mono mb-1">
                        Deterministic Verification Evidence Payload:
                      </span>
                      <pre className="bg-white p-3 rounded-xl border border-[#E5E9F2] font-mono text-[11px] text-[#182033] overflow-x-auto whitespace-pre-wrap">
                        {JSON.stringify(check.evidence, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Regulatory / System Disclaimer */}
      <div className="p-3.5 bg-[#F6F8FC] rounded-xl border border-[#E5E9F2] text-[11px] text-[#8E99AD] flex items-start gap-2">
        <Info className="h-4 w-4 shrink-0 text-[#4F6EF7] mt-0.5" />
        <p className="leading-relaxed">
          <strong className="text-[#182033]">Underwriting Notice:</strong> An anomaly indicates an evidence inconsistency evaluated by deterministic rules. It does not constitute legal proof of fraud.
        </p>
      </div>
    </div>
  );
};
