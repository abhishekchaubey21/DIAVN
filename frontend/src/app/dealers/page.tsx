import React from 'react';
import Link from 'next/link';
import { getDealers } from '@/lib/api';
import { StatusBadge } from '@/components/StatusBadge';
import { Building2, ArrowUpRight, MapPin, ShieldCheck, ShieldAlert, FileCheck2, UserCheck } from 'lucide-react';

export const dynamic = 'force-dynamic';

export default async function DealersPage() {
  const { dealers, isMock } = await getDealers();

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="rounded-2xl border border-[#E5E9F2] bg-white p-6 sm:p-8 shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
          <div className="space-y-2 max-w-2xl">
            <div className="flex items-center gap-2.5">
              <span className="text-[11px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-[#4F6EF7]/10 text-[#4F6EF7] border border-[#4F6EF7]/20">
                Dealer Network Intelligence
              </span>
              {isMock && <StatusBadge type="data_source" value="mock" size="sm" />}
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-[#182033]">
              Dealer Integrity Registry
            </h1>
            <p className="text-sm text-[#68738A] leading-relaxed">
              Authorized equipment dealer partners, risk tiering, historical loan volume, and multi-case entity link analysis.
            </p>
          </div>

          <div className="flex items-center gap-3 shrink-0">
            <div className="text-right">
              <div className="text-2xl font-extrabold text-[#182033] font-mono leading-none">
                {dealers.length}
              </div>
              <div className="text-[11px] font-bold uppercase text-[#8E99AD] tracking-wider mt-1">
                Monitored Networks
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Dealers Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {dealers.map((dealer) => {
          const isFlagged = dealer.status === 'flagged' || dealer.risk_tier === 'high';
          const isReview = dealer.status === 'under_review' || dealer.risk_tier === 'medium';

          return (
            <div
              key={dealer.id}
              className="rounded-2xl border border-[#E5E9F2] bg-white p-6 flex flex-col justify-between shadow-xs hover:shadow-md hover:border-[#D1D8E6] transition-all space-y-5"
            >
              <div className="space-y-4">
                {/* Dealer Header */}
                <div className="flex items-start justify-between gap-3 border-b border-[#E5E9F2] pb-4">
                  <div className="flex items-start gap-3">
                    <div className="h-10 w-10 rounded-xl bg-[#F6F8FC] border border-[#E5E9F2] text-[#4F6EF7] flex items-center justify-center font-bold shrink-0 mt-0.5 shadow-2xs">
                      <Building2 className="h-5 w-5" />
                    </div>
                    <div>
                      <h3 className="text-sm font-bold text-[#182033] leading-snug">
                        {dealer.name}
                      </h3>
                      <div className="text-[11px] font-mono text-[#8E99AD] mt-0.5">
                        {dealer.dealer_code}
                      </div>
                    </div>
                  </div>
                  <StatusBadge type="dealer_status" value={dealer.status} size="sm" />
                </div>

                {/* Metadata Details */}
                <div className="space-y-2.5 text-xs">
                  <div className="flex justify-between items-center">
                    <span className="text-[#68738A]">Risk Tier:</span>
                    <StatusBadge type="risk" value={dealer.risk_tier} size="sm" />
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-[#68738A]">GSTIN:</span>
                    <span className="font-mono font-semibold text-[#182033]">{dealer.gstin || 'N/A'}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-[#68738A]">PAN Identification:</span>
                    <span className="font-mono font-semibold text-[#182033]">{dealer.pan || 'N/A'}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-[#68738A]">Operating Hub:</span>
                    <span className="font-medium text-[#182033]">{dealer.city}, {dealer.state}</span>
                  </div>

                  <div className="pt-3 border-t border-[#E5E9F2] grid grid-cols-2 gap-2 text-center">
                    <div className="p-2 rounded-xl bg-[#F8FAFD] border border-[#E5E9F2]">
                      <div className="text-[10px] uppercase font-bold text-[#8E99AD]">Total Cases</div>
                      <div className="font-mono font-extrabold text-sm text-[#182033] mt-0.5">
                        {dealer.total_cases}
                      </div>
                    </div>
                    <div className="p-2 rounded-xl bg-[#FEF2F2]/60 border border-[#FECACA]">
                      <div className="text-[10px] uppercase font-bold text-[#991B1B]">Flagged Anomalies</div>
                      <div className="font-mono font-extrabold text-sm text-[#991B1B] mt-0.5">
                        {dealer.flagged_cases}
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Action Button */}
              <div className="pt-2">
                <Link
                  href={`/dealers/${dealer.id}`}
                  className="w-full flex items-center justify-center gap-1.5 bg-[#F8FAFD] hover:bg-[#4F6EF7] text-[#182033] hover:text-white text-xs font-bold py-2.5 rounded-xl border border-[#E5E9F2] hover:border-[#4F6EF7] transition-all shadow-2xs group"
                >
                  <span>View Dealer Profile</span>
                  <ArrowUpRight className="h-4 w-4 text-[#8E99AD] group-hover:text-white transition-colors" />
                </Link>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
