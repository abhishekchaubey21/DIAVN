import React from 'react';
import Link from 'next/link';
import { getCases } from '@/lib/api';
import { 
  FileText, 
  CheckCircle2, 
  AlertTriangle, 
  ArrowUpRight, 
  Receipt,
  Sparkles,
  Info
} from 'lucide-react';

export const dynamic = 'force-dynamic';

export default async function InvoicesPage() {
  const { cases } = await getCases();

  const invoiceRecords = [
    {
      invoiceNumber: 'INV-2026-001',
      caseId: 'CAS-2026-001',
      dealer: 'Apex Solar Equipment Pvt Ltd',
      customer: 'Rajesh Sharma',
      amount: 195000,
      benchmarkCheck: 'PASS' as const,
      arithmeticCheck: 'PASS' as const,
      serialCheck: 'PASS' as const,
      entityCheck: 'PASS' as const,
      status: 'VERIFIED' as const,
      extractedBy: 'Gemini 2.5 Flash'
    },
    {
      invoiceNumber: 'INV-2026-003',
      caseId: 'CAS-2026-003',
      dealer: 'SunPower Retail & Infra Solutions',
      customer: 'Meera Patel',
      amount: 390000,
      benchmarkCheck: 'ANOMALY' as const,
      benchmarkNote: '+121% Unit Rate Variance',
      arithmeticCheck: 'PASS' as const,
      serialCheck: 'PASS' as const,
      entityCheck: 'PASS' as const,
      status: 'FLAGGED' as const,
      extractedBy: 'Gemini 2.5 Flash'
    },
    {
      invoiceNumber: 'INV-2026-005',
      caseId: 'CAS-2026-005',
      dealer: 'Radiant AgroTech Distributions',
      customer: 'GreenFields Agri Enterprises',
      amount: 190000,
      benchmarkCheck: 'PASS' as const,
      arithmeticCheck: 'PASS' as const,
      serialCheck: 'ANOMALY' as const,
      serialNote: 'Duplicate Serial ASP-99881',
      entityCheck: 'PASS' as const,
      status: 'FLAGGED' as const,
      extractedBy: 'Gemini 2.5 Flash'
    },
    {
      invoiceNumber: 'INV-2026-007',
      caseId: 'CAS-2026-007',
      dealer: 'Radiant AgroTech Distributions',
      customer: 'GreenFields Agri Enterprises',
      amount: 34000,
      benchmarkCheck: 'ANOMALY' as const,
      benchmarkNote: 'Inflated Controller Rate',
      arithmeticCheck: 'PASS' as const,
      serialCheck: 'ANOMALY' as const,
      serialNote: 'Serial registered elsewhere',
      entityCheck: 'ANOMALY' as const,
      entityNote: 'Address matches dealer yard',
      status: 'FLAGGED' as const,
      extractedBy: 'Gemini 2.5 Flash'
    }
  ];

  return (
    <div className="space-y-6 max-w-[1600px] mx-auto pb-12">
      {/* Header */}
      <div className="rounded-2xl border border-[#E5E9F2] bg-white p-5 sm:p-6 shadow-xs flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <div className="h-7 w-7 rounded-lg bg-[#4F6EF7]/10 text-[#4F6EF7] flex items-center justify-center">
              <FileText className="h-4 w-4" />
            </div>
            <h1 className="text-xl font-extrabold text-[#182033]">
              Invoice Intelligence & Document Audits
            </h1>
          </div>
          <p className="text-xs text-[#68738A] mt-1">
            Multimodal OCR extraction, arithmetic integrity verification, and unit price market benchmarking
          </p>
        </div>

        <div className="flex items-center gap-2 font-mono text-[10px] text-[#68738A] px-3 py-1.5 rounded-lg bg-[#F8FAFD] border border-[#E5E9F2]">
          <Sparkles className="h-3.5 w-3.5 text-[#4F6EF7]" />
          <span>AI-extracted evidence — Verified by Phase 3 Rules</span>
        </div>
      </div>

      {/* Invoice Table */}
      <div className="rounded-2xl border border-[#E5E9F2] bg-white shadow-xs p-5 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-[#E5E9F2]">
          <span className="text-xs font-bold uppercase tracking-wider text-[#182033]">
            Verified Invoice Records ({invoiceRecords.length})
          </span>
          <span className="text-[10px] text-[#8E99AD] font-mono">
            Deterministic Rate Benchmarks (±15% Tolerance)
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-[#E5E9F2] bg-[#F8FAFD] text-[10px] font-extrabold uppercase tracking-wider text-[#8E99AD]">
                <th className="py-2.5 px-4">Invoice #</th>
                <th className="py-2.5 px-4">Case ID</th>
                <th className="py-2.5 px-4">Dealer</th>
                <th className="py-2.5 px-4">Amount</th>
                <th className="py-2.5 px-4">Price Benchmark</th>
                <th className="py-2.5 px-4">Arithmetic Check</th>
                <th className="py-2.5 px-4">Serial Integrity</th>
                <th className="py-2.5 px-4">Status</th>
                <th className="py-2.5 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#F1F4FA] text-xs">
              {invoiceRecords.map((inv) => (
                <tr key={inv.invoiceNumber} className="hover:bg-[#F8FAFD] transition-colors">
                  <td className="py-3.5 px-4 font-mono font-bold text-[#182033]">
                    {inv.invoiceNumber}
                  </td>
                  <td className="py-3.5 px-4 font-mono font-bold text-[#4F6EF7]">
                    <Link href={`/cases/${inv.caseId}`} className="hover:underline">
                      {inv.caseId}
                    </Link>
                  </td>
                  <td className="py-3.5 px-4 text-[#182033] font-medium truncate max-w-[160px]">
                    {inv.dealer}
                  </td>
                  <td className="py-3.5 px-4 font-mono font-bold text-[#182033]">
                    ₹{(inv.amount / 100000).toFixed(2)}L
                  </td>
                  <td className="py-3.5 px-4">
                    {inv.benchmarkCheck === 'PASS' ? (
                      <span className="text-[#065F46] font-semibold flex items-center gap-1">
                        <CheckCircle2 className="h-3 w-3 text-[#10B981]" />
                        <span>Pass</span>
                      </span>
                    ) : (
                      <span className="text-[#991B1B] font-semibold flex items-center gap-1 font-mono text-[11px]">
                        <AlertTriangle className="h-3 w-3 text-[#EF4444]" />
                        <span>{inv.benchmarkNote || 'Anomaly'}</span>
                      </span>
                    )}
                  </td>
                  <td className="py-3.5 px-4">
                    <span className="text-[#065F46] font-semibold flex items-center gap-1">
                      <CheckCircle2 className="h-3 w-3 text-[#10B981]" />
                      <span>Valid</span>
                    </span>
                  </td>
                  <td className="py-3.5 px-4">
                    {inv.serialCheck === 'PASS' ? (
                      <span className="text-[#065F46] font-semibold flex items-center gap-1">
                        <CheckCircle2 className="h-3 w-3 text-[#10B981]" />
                        <span>Unique</span>
                      </span>
                    ) : (
                      <span className="text-[#991B1B] font-semibold flex items-center gap-1 font-mono text-[11px]">
                        <AlertTriangle className="h-3 w-3 text-[#EF4444]" />
                        <span>{inv.serialNote || 'Collision'}</span>
                      </span>
                    )}
                  </td>
                  <td className="py-3.5 px-4">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                      inv.status === 'VERIFIED'
                        ? 'bg-[#ECFDF5] text-[#065F46] border border-[#A7F3D0]'
                        : 'bg-[#FEF2F2] text-[#991B1B] border border-[#FECACA]'
                    }`}>
                      {inv.status}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-right">
                    <Link
                      href={`/cases/${inv.caseId}`}
                      className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-white border border-[#E5E9F2] text-[11px] font-bold text-[#4F6EF7] hover:bg-[#4F6EF7] hover:text-white transition-colors shadow-2xs"
                    >
                      <span>Inspect</span>
                      <ArrowUpRight className="h-3 w-3" />
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
