import React from 'react';
import Link from 'next/link';
import { getDealers } from '@/lib/api';
import { StatusBadge } from '@/components/StatusBadge';
import { Building2, ArrowUpRight, ShieldCheck, ShieldAlert, AlertTriangle } from 'lucide-react';

export const dynamic = 'force-dynamic';

export default async function DealersPage() {
  const { dealers, isMock } = await getDealers();

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
              <Building2 className="h-6 w-6 text-cyan-400" />
              Dealer Network Integrity Registry
            </h1>
            {isMock && <StatusBadge type="data_source" value="mock" />}
          </div>
          <p className="mt-1 text-sm text-slate-400">
            Authorized dealer partners, risk tiering, historical case volume, and network anomaly flags.
          </p>
        </div>
      </div>

      {/* Dealers Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {dealers.map((dealer) => (
          <div
            key={dealer.id}
            className="rounded-xl border border-slate-800 bg-slate-900/70 p-6 flex flex-col justify-between shadow-xl backdrop-blur-sm transition-all hover:border-slate-700"
          >
            <div>
              <div className="flex items-start justify-between gap-3 border-b border-slate-800 pb-4">
                <div>
                  <h3 className="text-base font-bold text-slate-100">{dealer.name}</h3>
                  <div className="text-xs font-mono text-cyan-400 mt-0.5">{dealer.dealer_code}</div>
                </div>
                <StatusBadge type="dealer_status" value={dealer.status} size="sm" />
              </div>

              <div className="mt-4 space-y-2.5 text-xs">
                <div className="flex justify-between">
                  <span className="text-slate-400">Risk Tier:</span>
                  <StatusBadge type="risk" value={dealer.risk_tier} size="sm" />
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">GSTIN:</span>
                  <span className="font-mono text-slate-200">{dealer.gstin || 'N/A'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">PAN:</span>
                  <span className="font-mono text-slate-200">{dealer.pan || 'N/A'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Operating City:</span>
                  <span className="text-slate-200">{dealer.city}, {dealer.state}</span>
                </div>
                <div className="flex justify-between pt-2 border-t border-slate-800/80">
                  <span className="text-slate-400">Total Cases:</span>
                  <span className="font-mono font-medium text-slate-200">{dealer.total_cases}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Flagged Anomalies:</span>
                  <span className="font-mono font-bold text-rose-400">{dealer.flagged_cases}</span>
                </div>
              </div>
            </div>

            <div className="mt-6 pt-4 border-t border-slate-800">
              <Link
                href={`/dealers/${dealer.id}`}
                className="w-full flex items-center justify-center gap-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold py-2 rounded-lg border border-slate-700 transition-colors"
              >
                View Dealer Profile
                <ArrowUpRight className="h-4 w-4 text-slate-400" />
              </Link>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
