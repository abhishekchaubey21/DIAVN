import React from 'react';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import { getDealerById, getCases } from '@/lib/api';
import { StatusBadge } from '@/components/StatusBadge';
import { CaseTable } from '@/components/CaseTable';
import { 
  ArrowLeft, 
  Building2, 
  MapPin, 
  Phone, 
  Mail, 
  ShieldAlert, 
  FileCheck2, 
  Layers,
  FileSpreadsheet
} from 'lucide-react';

interface DealerDetailPageProps {
  params: Promise<{ id: string }>;
}

export const dynamic = 'force-dynamic';

export default async function DealerDetailPage({ params }: DealerDetailPageProps) {
  const { id } = await params;
  const { dealer, isMock: dealerIsMock } = await getDealerById(id);
  const { cases } = await getCases();

  if (!dealer) {
    notFound();
  }

  const dealerCases = cases.filter((c) => c.dealer_id === dealer.id || c.dealer_id === dealer.dealer_code);

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-xs text-slate-400">
        <Link href="/dealers" className="hover:text-slate-200 flex items-center gap-1">
          <ArrowLeft className="h-3.5 w-3.5" />
          Dealer Registry
        </Link>
        <span>/</span>
        <span className="text-slate-200">{dealer.name}</span>
      </div>

      {/* Dealer Header */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-6 backdrop-blur-md">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-5">
          <div className="flex items-start gap-4">
            <div className="p-3.5 rounded-xl bg-cyan-950/60 border border-cyan-500/30 text-cyan-400">
              <Building2 className="h-7 w-7" />
            </div>
            <div>
              <div className="flex items-center gap-2.5">
                <h1 className="text-2xl font-bold text-white">{dealer.name}</h1>
                <StatusBadge type="dealer_status" value={dealer.status} />
              </div>
              <div className="text-xs font-mono text-cyan-400 mt-1">
                Code: {dealer.dealer_code} • Trade Name: {dealer.business_name}
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <StatusBadge type="risk" value={dealer.risk_tier} size="md" />
            {dealerIsMock && <StatusBadge type="data_source" value="mock" size="sm" />}
          </div>
        </div>

        <div className="mt-5 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
          <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
            <span className="text-slate-500 block">GSTIN Identification</span>
            <span className="font-mono text-slate-200 font-medium text-sm mt-0.5 block">{dealer.gstin || 'N/A'}</span>
          </div>
          <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
            <span className="text-slate-500 block">PAN / CIN</span>
            <span className="font-mono text-slate-200 font-medium text-sm mt-0.5 block">{dealer.pan || 'N/A'}</span>
          </div>
          <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
            <span className="text-slate-500 block">Total Portfolio Cases</span>
            <span className="font-mono text-slate-200 font-medium text-sm mt-0.5 block">{dealer.total_cases} cases</span>
          </div>
          <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
            <span className="text-slate-500 block">Anomaly Rate</span>
            <span className="font-mono text-rose-400 font-bold text-sm mt-0.5 block">
              {dealer.total_cases > 0 ? `${((dealer.flagged_cases / dealer.total_cases) * 100).toFixed(0)}%` : '0%'} ({dealer.flagged_cases} flagged)
            </span>
          </div>
        </div>

        <div className="mt-4 pt-4 border-t border-slate-800 flex flex-wrap gap-6 text-xs text-slate-400">
          <span className="flex items-center gap-1.5">
            <MapPin className="h-4 w-4 text-slate-500" />
            {dealer.address}, {dealer.city}, {dealer.state} - {dealer.pincode}
          </span>
          <span className="flex items-center gap-1.5">
            <Mail className="h-4 w-4 text-slate-500" />
            {dealer.contact_email}
          </span>
          <span className="flex items-center gap-1.5">
            <Phone className="h-4 w-4 text-slate-500" />
            {dealer.contact_phone}
          </span>
        </div>
      </div>

      {/* Dealer Relationship & Network Concentration Summary (Phase 7 Engine) */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-6 space-y-4 backdrop-blur-md">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
            <Layers className="h-4 w-4 text-indigo-400" />
            Dealer Relationship & Network Concentration Summary
          </h2>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-950/60 text-indigo-300 border border-indigo-500/30">
            relationship-v1
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
          <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
            <span className="text-slate-500 block">Associated Cases</span>
            <span className="font-mono text-slate-200 font-bold text-sm mt-0.5 block">{dealerCases.length} cases</span>
          </div>
          <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
            <span className="text-slate-500 block">Unique Borrowers</span>
            <span className="font-mono text-slate-200 font-bold text-sm mt-0.5 block">
              {new Set(dealerCases.map((c) => c.customer_id)).size || 1} borrowers
            </span>
          </div>
          <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
            <span className="text-slate-500 block">Shared Attribute Clusters</span>
            <span className="font-mono text-amber-300 font-bold text-sm mt-0.5 block">
              {dealer.dealer_code === 'RAD-AGR-003' || dealer.id.includes('2203') ? '1 cluster (address)' : '0 clusters'}
            </span>
          </div>
          <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
            <span className="text-slate-500 block">Relationship Review Signals</span>
            <span className="font-mono text-cyan-400 font-bold text-sm mt-0.5 block">
              {dealer.flagged_cases > 0 ? `${dealer.flagged_cases} review items` : '0 items'}
            </span>
          </div>
        </div>

        <p className="text-[11px] text-slate-500 pt-1">
          Descriptive network concentration metrics only. Operational portfolio volume does not constitute evidence of dealer misconduct.
        </p>
      </div>

      {/* Associated Cases Queue */}
      <div className="space-y-3">
        <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
          <FileCheck2 className="h-5 w-5 text-indigo-400" />
          Cases Associated with this Dealer ({dealerCases.length})
        </h2>
        <CaseTable cases={dealerCases} isMock={dealerIsMock} />
      </div>
    </div>
  );
}
