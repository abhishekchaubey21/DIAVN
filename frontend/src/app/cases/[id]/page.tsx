import React from 'react';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import { getCaseById } from '@/lib/api';
import { MOCK_RISK_SCORES, MOCK_RISK_SIGNALS, MOCK_EVIDENCE_ITEMS, MOCK_VERIFICATION_TASKS } from '@/lib/mockData';
import { RiskScoreCard } from '@/components/RiskScoreCard';
import { AlertCard } from '@/components/AlertCard';
import { EvidenceCard } from '@/components/EvidenceCard';
import { InvoiceEvidenceCard } from '@/components/InvoiceEvidenceCard';
import { DeterministicVerificationPanel } from '@/components/DeterministicVerificationPanel';
import { ImageVerificationPanel } from '@/components/ImageVerificationPanel';
import { RelationshipPanel } from '@/components/RelationshipPanel';
import { CaseVerificationPipeline } from '@/components/CaseVerificationPipeline';
import { VerificationResult } from '@/components/VerificationResult';
import { StatusBadge } from '@/components/StatusBadge';
import { 
  ArrowLeft, 
  Building2, 
  User, 
  MapPin, 
  Calendar, 
  ShieldAlert, 
  FileText, 
  CheckSquare2,
  Receipt,
  Layers,
  Cpu
} from 'lucide-react';

interface CaseDetailPageProps {
  params: Promise<{ id: string }>;
}

export const dynamic = 'force-dynamic';

export default async function CaseDetailPage({ params }: CaseDetailPageProps) {
  const { id } = await params;
  const { caseItem, isMock } = await getCaseById(id);

  if (!caseItem) {
    notFound();
  }

  const riskScore = MOCK_RISK_SCORES[caseItem.id] || MOCK_RISK_SCORES[caseItem.case_number] || null;
  const riskSignals = MOCK_RISK_SIGNALS[caseItem.id] || MOCK_RISK_SIGNALS[caseItem.case_number] || [];
  const evidenceItems = MOCK_EVIDENCE_ITEMS[caseItem.id] || MOCK_EVIDENCE_ITEMS[caseItem.case_number] || [];
  const verificationTasks = MOCK_VERIFICATION_TASKS[caseItem.id] || MOCK_VERIFICATION_TASKS[caseItem.case_number] || [];

  // Attached Invoices (from API response or synthetic mock)
  const attachedInvoices = (caseItem as any).invoices && (caseItem as any).invoices.length > 0 
    ? (caseItem as any).invoices 
    : [
        {
          id: `INV-${caseItem.case_number}-01`,
          original_filename: `tax_invoice_${caseItem.case_number.toLowerCase()}.pdf`,
          invoice_number: `INV-APX-2026-${caseItem.case_number.slice(-3)}`,
          invoice_date: '2026-01-15',
          dealer_name: caseItem.dealer_name || 'Apex Solar Solutions',
          dealer_gstin: '27AAACA1234A1Z5',
          customer_name: caseItem.customer_name || 'Rajesh Sharma',
          total_amount: caseItem.loan_amount,
          tax_amount: caseItem.loan_amount * 0.18,
          status: 'completed',
          verification_status: 'pending_verification',
          extraction_confidence: 0.96,
          line_items: [
            {
              product_name: caseItem.asset_type,
              hsn_code: '84137010',
              quantity: 1,
              unit_price: caseItem.loan_amount,
              total_amount: caseItem.loan_amount,
              serial_numbers: ['ASP-2025-99881']
            }
          ]
        }
      ];

  return (
    <div className="space-y-7 max-w-6xl mx-auto">
      {/* Breadcrumb Navigation */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-xs text-slate-400">
          <Link href="/cases" className="hover:text-slate-200 flex items-center gap-1">
            <ArrowLeft className="h-3.5 w-3.5" />
            Cases Queue
          </Link>
          <span>/</span>
          <span className="text-slate-200 font-mono">{caseItem.case_number}</span>
        </div>

        {isMock && <StatusBadge type="data_source" value="mock" size="sm" />}
      </div>

      {/* Case Header & Status Banner */}
      <VerificationResult
        status={caseItem.status}
        riskLevel={caseItem.risk_level}
        caseNumber={caseItem.case_number}
      />

      {/* Case-Level End-to-End Orchestration Pipeline (Phase 8) */}
      <CaseVerificationPipeline
        caseId={caseItem.id}
        caseScenarioId={caseItem.case_number}
      />

      {/* Primary Grid: Metadata & Risk Assessment */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Metadata Details */}
        <div className="space-y-6">
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-4">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-300 border-b border-slate-800 pb-3 flex items-center gap-2">
              <Layers className="h-4 w-4 text-indigo-400" />
              Underwriting Parameters
            </h3>

            <div className="space-y-3 text-xs">
              <div>
                <span className="text-slate-500 block">Equipment Model</span>
                <span className="text-slate-200 font-medium font-mono text-sm">{caseItem.asset_type}</span>
              </div>

              <div>
                <span className="text-slate-500 block">Loan Disbursement Amount</span>
                <span className="text-slate-100 font-mono font-bold text-base">
                  ₹{caseItem.loan_amount.toLocaleString('en-IN')}
                </span>
              </div>

              <div className="pt-2 border-t border-slate-800">
                <span className="text-slate-500 block flex items-center gap-1">
                  <Building2 className="h-3.5 w-3.5 text-cyan-400" />
                  Dealer
                </span>
                <Link
                  href={`/dealers/${caseItem.dealer_id}`}
                  className="text-indigo-400 hover:text-indigo-300 font-medium mt-0.5 block"
                >
                  {caseItem.dealer_name || caseItem.dealer_id}
                </Link>
              </div>

              <div className="pt-2 border-t border-slate-800">
                <span className="text-slate-500 block flex items-center gap-1">
                  <User className="h-3.5 w-3.5 text-emerald-400" />
                  Borrower / Customer
                </span>
                <span className="text-slate-200 font-medium mt-0.5 block">
                  {caseItem.customer_name || caseItem.customer_id}
                </span>
              </div>

              <div className="pt-2 border-t border-slate-800">
                <span className="text-slate-500 block flex items-center gap-1">
                  <MapPin className="h-3.5 w-3.5 text-amber-400" />
                  Claimed Installation Location
                </span>
                <p className="text-slate-300 mt-0.5 leading-relaxed">
                  {caseItem.claimed_installation_address}
                </p>
              </div>

              <div className="pt-2 border-t border-slate-800">
                <span className="text-slate-500 block flex items-center gap-1">
                  <Calendar className="h-3.5 w-3.5 text-slate-400" />
                  Case Inception Date
                </span>
                <span className="text-slate-400 font-mono">
                  {new Date(caseItem.created_at).toLocaleDateString()}
                </span>
              </div>
            </div>
          </div>

          {/* Verification Tasks */}
          {verificationTasks.length > 0 && (
            <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-3">
              <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-300 border-b border-slate-800 pb-3 flex items-center gap-2">
                <CheckSquare2 className="h-4 w-4 text-amber-400" />
                Actionable Verification Tasks
              </h3>
              {verificationTasks.map((t) => (
                <div key={t.id} className="p-3 bg-slate-950/60 rounded-lg border border-slate-800 text-xs space-y-1.5">
                  <div className="flex justify-between items-center">
                    <span className="font-semibold text-slate-200 capitalize font-mono">
                      {t.task_type.replace('_', ' ')}
                    </span>
                    <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-amber-950/60 text-amber-300 border border-amber-500/40">
                      {t.status}
                    </span>
                  </div>
                  <p className="text-slate-400">{t.instructions}</p>
                  {t.findings && (
                    <div className="mt-1 pt-1 text-emerald-400 font-mono text-[11px] border-t border-slate-800">
                      Findings: {t.findings}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right Column: Composite Risk Engine & Signals & Extracted Invoices */}
        <div className="lg:col-span-2 space-y-6">
          {/* Extracted Invoice Evidence Section (Phase 2 Ingestion) */}
          <div className="space-y-3">
            <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
              <Receipt className="h-5 w-5 text-indigo-400" />
              Ingested Invoice Documents & AI-Extracted Line Items
            </h3>
            {attachedInvoices.map((inv: any) => (
              <InvoiceEvidenceCard key={inv.id} invoice={inv} />
            ))}
          </div>

          {/* Deterministic Invoice Verification (Phase 3 Engine) */}
          <div className="space-y-3">
            {attachedInvoices.map((inv: any) => (
              <DeterministicVerificationPanel
                key={`verif-${inv.id}`}
                invoiceId={inv.id}
                caseScenarioId={caseItem.case_number}
              />
            ))}
          </div>

          {/* Installation Image Forensics & Telemetry (Phase 4 Engine) */}
          <div className="space-y-3">
            <ImageVerificationPanel
              caseId={caseItem.id}
              images={[]}
              caseScenarioId={caseItem.case_number}
            />
          </div>

          {/* Dealer Relationship & Entity-Link Analysis (Phase 7 Engine) */}
          <div className="space-y-3">
            <RelationshipPanel
              caseId={caseItem.id}
              caseScenarioId={caseItem.case_number}
            />
          </div>

          <RiskScoreCard
            caseId={caseItem.id}
            initialScore={riskScore}
            caseScenarioId={caseItem.case_number}
          />

          {/* Risk Signals / Anomalies */}
          <div className="space-y-3">
            <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
              <ShieldAlert className="h-5 w-5 text-rose-400" />
              Detected Risk Signals & Evidence Breakdowns
            </h3>

            {riskSignals.length === 0 ? (
              <div className="p-5 rounded-xl border border-slate-800 bg-slate-900/40 text-center text-slate-400 text-xs">
                No high-severity risk signals recorded for this case.
              </div>
            ) : (
              riskSignals.map((s) => <AlertCard key={s.id} signal={s} />)
            )}
          </div>

          {/* Evidence Repository */}
          <div className="space-y-3">
            <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
              <FileText className="h-5 w-5 text-indigo-400" />
              Supporting Telemetry & Photo Evidence
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {evidenceItems.length === 0 ? (
                <div className="col-span-2 p-5 rounded-xl border border-slate-800 bg-slate-900/40 text-center text-slate-400 text-xs">
                  No staged evidence documents attached.
                </div>
              ) : (
                evidenceItems.map((e) => <EvidenceCard key={e.id} item={e} />)
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
