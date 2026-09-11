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
        check_type: 'SERIAL_PRESENCE_AND_FORMAT',
        check_name: 'Serial Number Format Validity',
        status: 'PASS',
        severity: 'INFO',
        message: 'Serial number conforms to standard alphanumeric equipment format.',
        evidence: { serial_number: 'SG-5K-99014' }
      },
      {
        check_type: 'INVOICE_ARITHMETIC',
        check_name: 'Invoice Internal Arithmetic Integrity',
        status: 'PASS',
        severity: 'INFO',
        message: 'All line item multiplications and gross totals reconcile with subtotal + tax.',
        evidence: { stated_total: 115000, subtotal: 97457.6, tax: 17542.4 }
      },
      {
        check_type: 'CASE_ENTITY_CONSISTENCY',
        check_name: 'Case Entity & Asset Correspondence',
        status: 'PASS',
        severity: 'INFO',
        message: 'Invoice issuing dealer and customer match authorized underwriting application.',
        evidence: { matched_dealer: 'SunPower Retail & Infra Solutions', matched_customer: 'Meera Patel' }
      },
      {
        check_type: 'REQUIRED_EVIDENCE_FIELDS',
        check_name: 'Required Evidence Completeness',
        status: 'PASS',
        severity: 'INFO',
        message: 'All mandatory invoice evidence fields are present.',
        evidence: { validated_fields: ['invoice_number', 'invoice_date', 'dealer_name', 'customer_name', 'total_amount'] }
      }
    ] : caseScenarioId === 'CAS-2026-005' ? [
      {
        check_type: 'SERIAL_INTERNAL_DUPLICATE',
        check_name: 'Internal Asset Registry Duplicate Check',
        status: 'ANOMALY',
        severity: 'HIGH',
        message: "Serial number 'ASP-2025-99881' already belongs to existing active case #CAS-2026-001 in internal database.",
        evidence: {
          serial_number: 'ASP-2025-99881',
          current_case_id: 'CAS-2026-005',
          prior_case_id: 'CAS-2026-001',
          prior_installed_at: '2025-08-14',
          scope: 'internal_lender_registry'
        }
      },
      {
        check_type: 'PRICE_BENCHMARK',
        check_name: 'Product Price Benchmark Consistency',
        status: 'PASS',
        severity: 'INFO',
        message: 'Unit price (₹190,000.00) is within normal benchmark range (₹157,250 – ₹212,750).',
        evidence: { product: 'Solar Water Pump 5HP', invoice_unit_price: 190000, benchmark_avg_price: 185000, variance_pct: 2.7 }
      },
      {
        check_type: 'INVOICE_ARITHMETIC',
        check_name: 'Invoice Internal Arithmetic Integrity',
        status: 'PASS',
        severity: 'INFO',
        message: 'All line item multiplications and gross totals reconcile with subtotal + tax.',
        evidence: { stated_total: 190000, subtotal: 161016.9, tax: 28983.1 }
      },
      {
        check_type: 'CASE_ENTITY_CONSISTENCY',
        check_name: 'Case Entity & Asset Correspondence',
        status: 'PASS',
        severity: 'INFO',
        message: 'Invoice issuing dealer and customer match authorized underwriting application.',
        evidence: { matched_dealer: 'Radiant AgroTech Distributions', matched_customer: 'GreenFields Agri Enterprises' }
      },
      {
        check_type: 'REQUIRED_EVIDENCE_FIELDS',
        check_name: 'Required Evidence Completeness',
        status: 'PASS',
        severity: 'INFO',
        message: 'All mandatory invoice evidence fields are present.',
        evidence: { validated_fields: ['invoice_number', 'invoice_date', 'dealer_name', 'customer_name', 'total_amount'] }
      }
    ] : [
      {
        check_type: 'PRICE_BENCHMARK',
        check_name: 'Product Price Benchmark Consistency',
        status: 'PASS',
        severity: 'INFO',
        message: 'Unit price (₹195,000.00) is within normal benchmark range (₹157,250 – ₹212,750).',
        evidence: { product: 'Solar Water Pump 5HP', invoice_unit_price: 195000, benchmark_avg_price: 185000, allowed_range: [157250, 212750], variance_pct: 5.4 }
      },
      {
        check_type: 'SERIAL_PRESENCE_AND_FORMAT',
        check_name: 'Serial Number Format & Uniqueness',
        status: 'PASS',
        severity: 'INFO',
        message: 'Serial ASP-2025-99881 verified unique and correctly formatted in registry.',
        evidence: { serial_number: 'ASP-2025-99881', format: 'valid_alphanumeric' }
      },
      {
        check_type: 'INVOICE_ARITHMETIC',
        check_name: 'Invoice Internal Arithmetic Integrity',
        status: 'PASS',
        severity: 'INFO',
        message: 'All line item multiplications and gross totals reconcile with subtotal + tax.',
        evidence: { stated_total: 195000, subtotal: 165254.2, tax: 29745.8 }
      },
      {
        check_type: 'CASE_ENTITY_CONSISTENCY',
        check_name: 'Case Entity & Asset Correspondence',
        status: 'PASS',
        severity: 'INFO',
        message: 'Invoice issuing dealer and customer match authorized underwriting application.',
        evidence: { matched_dealer: 'Apex Solar Solutions', matched_customer: 'Rajesh Sharma' }
      },
      {
        check_type: 'REQUIRED_EVIDENCE_FIELDS',
        check_name: 'Required Evidence Completeness',
        status: 'PASS',
        severity: 'INFO',
        message: 'All mandatory invoice evidence fields are present.',
        evidence: { validated_fields: ['invoice_number', 'invoice_date', 'dealer_name', 'customer_name', 'total_amount'] }
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
      console.error('Verification execution error:', err);
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'PASS':
        return (
          <span className="inline-flex items-center gap-1 text-xs font-mono font-bold text-emerald-400 bg-emerald-950/60 border border-emerald-500/40 px-2 py-0.5 rounded">
            <CheckCircle2 className="h-3.5 w-3.5" />
            PASS
          </span>
        );
      case 'ANOMALY':
        return (
          <span className="inline-flex items-center gap-1 text-xs font-mono font-bold text-rose-400 bg-rose-950/60 border border-rose-500/40 px-2 py-0.5 rounded animate-pulse">
            <AlertTriangle className="h-3.5 w-3.5" />
            ANOMALY
          </span>
        );
      case 'INCONCLUSIVE':
      default:
        return (
          <span className="inline-flex items-center gap-1 text-xs font-mono font-bold text-slate-300 bg-slate-800 border border-slate-700 px-2 py-0.5 rounded">
            <HelpCircle className="h-3.5 w-3.5" />
            INCONCLUSIVE
          </span>
        );
    }
  };

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-5 backdrop-blur-md space-y-4 shadow-xl">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <Cpu className="h-5 w-5 text-indigo-400" />
            <h3 className="text-base font-bold text-slate-100">
              Deterministic Invoice Verification Engine
            </h3>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Local rules evaluation • Zero external APIs • Evidence consistency checks
          </p>
        </div>

        <button
          onClick={handleRunVerification}
          disabled={loading}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 text-white text-xs font-semibold shadow-md transition-colors"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>{loading ? 'Evaluating Rules...' : 'Re-run Checks'}</span>
        </button>
      </div>

      {/* Stage Distinction Banner */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 text-center text-xs">
        <div className="p-2.5 rounded-lg bg-slate-950/70 border border-slate-800">
          <span className="text-[10px] uppercase font-semibold text-slate-500 block">AI Evidence Extraction</span>
          <span className="font-mono text-emerald-400 font-bold mt-0.5 block">COMPLETED</span>
        </div>
        <div className="p-2.5 rounded-lg bg-indigo-950/30 border border-indigo-500/30">
          <span className="text-[10px] uppercase font-semibold text-indigo-300 block">Deterministic Rules</span>
          <span className="font-mono text-indigo-400 font-bold mt-0.5 block">COMPLETED ({activeSummary.passed_count} PASS / {activeSummary.anomaly_count} ANOMALY)</span>
        </div>
        <div className="p-2.5 rounded-lg bg-slate-950/70 border border-slate-800">
          <span className="text-[10px] uppercase font-semibold text-slate-500 block">Final Risk Score</span>
          <span className="font-mono text-slate-400 font-medium mt-0.5 block">NOT YET COMPUTED</span>
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
              className={`rounded-lg border transition-all ${
                isAnomaly 
                  ? 'border-rose-500/40 bg-rose-950/20' 
                  : check.status === 'PASS' 
                    ? 'border-slate-800 bg-slate-950/40' 
                    : 'border-slate-800 bg-slate-950/30'
              }`}
            >
              <div
                onClick={() => setExpandedIndex(isExpanded ? null : idx)}
                className="p-3.5 flex items-center justify-between cursor-pointer select-none"
              >
                <div className="flex items-center gap-2.5">
                  {getStatusBadge(check.status)}
                  <div>
                    <h4 className="text-xs font-semibold text-slate-200">{check.check_name}</h4>
                    <p className="text-[11px] text-slate-400 mt-0.5 line-clamp-1">{check.message}</p>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-[10px] uppercase font-mono text-slate-500 hidden sm:inline">
                    {check.check_type}
                  </span>
                  {isExpanded ? (
                    <ChevronUp className="h-4 w-4 text-slate-400" />
                  ) : (
                    <ChevronDown className="h-4 w-4 text-slate-400" />
                  )}
                </div>
              </div>

              {/* Expandable Evidence Payload */}
              {isExpanded && (
                <div className="px-3.5 pb-3.5 pt-1 border-t border-slate-800/80 space-y-2 text-xs">
                  <div className="text-slate-300 font-normal">{check.message}</div>
                  {check.evidence && Object.keys(check.evidence).length > 0 && (
                    <div>
                      <span className="text-[10px] uppercase tracking-wider font-semibold text-slate-400 block font-mono mb-1">
                        Deterministic Verification Evidence Payload:
                      </span>
                      <pre className="bg-slate-950 p-2.5 rounded border border-slate-800 font-mono text-[11px] text-slate-300 overflow-x-auto whitespace-pre-wrap">
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
      <div className="p-3 bg-slate-950/80 rounded-lg border border-slate-800 text-[11px] text-slate-400 flex items-start gap-2">
        <Info className="h-4 w-4 shrink-0 text-slate-500 mt-0.5" />
        <div>
          <span className="font-semibold text-slate-300 block">Important Underwriting Notice:</span>
          An anomaly is an evidence-based inconsistency requiring human underwriter or field audit review. It is <strong>not</strong> a determination of fraud.
        </div>
      </div>
    </div>
  );
};
