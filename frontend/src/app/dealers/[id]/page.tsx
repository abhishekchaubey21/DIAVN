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
  ChevronRight
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
    <div className="space-y-8 max-w-6xl mx-auto">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-xs text-[#8E99AD]">
        <Link href="/dealers" className="hover:text-[#182033] flex items-center gap-1 font-semibold transition-colors">
          <ArrowLeft className="h-3.5 w-3.5" />
          <span>Dealer Registry</span>
        </Link>
        <ChevronRight className="h-3.5 w-3.5" />
        <span className="text-[#182033] font-bold">{dealer.name}</span>
      </div>

      {/* Dealer Header Card */}
      <div className="rounded-2xl border border-[#E5E9F2] bg-white p-6 sm:p-8 shadow-xs space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#E5E9F2] pb-6">
          <div className="flex items-start gap-4">
            <div className="h-14 w-14 rounded-2xl bg-[#4F6EF7]/10 border border-[#4F6EF7]/20 text-[#4F6EF7] flex items-center justify-center font-bold text-xl shrink-0 shadow-2xs">
              <Building2 className="h-7 w-7" />
            </div>
            <div>
              <div className="flex items-center gap-2.5">
                <h1 className="text-xl sm:text-2xl font-extrabold text-[#182033]">{dealer.name}</h1>
                <StatusBadge type="dealer_status" value={dealer.status} />
              </div>
              <div className="text-xs font-mono text-[#8E99AD] mt-1">
                Code: <strong className="text-[#4F6EF7]">{dealer.dealer_code}</strong> • Business Name: <strong className="text-[#182033]">{dealer.business_name}</strong>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <StatusBadge type="risk" value={dealer.risk_tier} size="md" />
            {dealerIsMock && <StatusBadge type="data_source" value="mock" size="sm" />}
          </div>
        </div>

        {/* 4 Stat Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
          <div className="p-4 bg-[#F8FAFD] rounded-xl border border-[#E5E9F2]">
            <span className="text-[#8E99AD] font-bold uppercase text-[10px] tracking-wider block">GSTIN Identification</span>
            <span className="font-mono text-[#182033] font-bold text-sm mt-1 block">{dealer.gstin || 'N/A'}</span>
          </div>
          <div className="p-4 bg-[#F8FAFD] rounded-xl border border-[#E5E9F2]">
            <span className="text-[#8E99AD] font-bold uppercase text-[10px] tracking-wider block">PAN Identification</span>
            <span className="font-mono text-[#182033] font-bold text-sm mt-1 block">{dealer.pan || 'N/A'}</span>
          </div>
          <div className="p-4 bg-[#F8FAFD] rounded-xl border border-[#E5E9F2]">
            <span className="text-[#8E99AD] font-bold uppercase text-[10px] tracking-wider block">Portfolio Volume</span>
            <span className="font-mono text-[#182033] font-bold text-sm mt-1 block">{dealer.total_cases} cases</span>
          </div>
          <div className="p-4 bg-[#FEF2F2]/60 rounded-xl border border-[#FECACA]">
            <span className="text-[#991B1B] font-bold uppercase text-[10px] tracking-wider block">Anomaly Rate</span>
            <span className="font-mono text-[#991B1B] font-bold text-sm mt-1 block">
              {dealer.total_cases > 0 ? `${((dealer.flagged_cases / dealer.total_cases) * 100).toFixed(0)}%` : '0%'} ({dealer.flagged_cases} flagged)
            </span>
          </div>
        </div>

        {/* Contact Info Footer */}
        <div className="pt-4 border-t border-[#E5E9F2] flex flex-wrap gap-6 text-xs text-[#68738A]">
          <span className="flex items-center gap-1.5">
            <MapPin className="h-4 w-4 text-[#8E99AD]" />
            <span>{dealer.address}, {dealer.city}, {dealer.state} - {dealer.pincode}</span>
          </span>
          <span className="flex items-center gap-1.5">
            <Mail className="h-4 w-4 text-[#8E99AD]" />
            <span>{dealer.contact_email}</span>
          </span>
          <span className="flex items-center gap-1.5">
            <Phone className="h-4 w-4 text-[#8E99AD]" />
            <span>{dealer.contact_phone}</span>
          </span>
        </div>
      </div>

      {/* Associated Cases Queue */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-bold text-[#182033] flex items-center gap-2">
            <FileCheck2 className="h-5 w-5 text-[#4F6EF7]" />
            <span>Associated Verification Submissions ({dealerCases.length})</span>
          </h2>
        </div>
        <CaseTable cases={dealerCases} isMock={dealerIsMock} />
      </div>
    </div>
  );
}
