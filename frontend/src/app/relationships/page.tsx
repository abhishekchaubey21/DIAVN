import React from 'react';
import Link from 'next/link';
import { getCases, getDealers, getCaseRelationships } from '@/lib/api';
import { VerificationNetworkGraph } from '@/components/VerificationNetworkGraph';
import { 
  Network, 
  Building2, 
  User, 
  Layers, 
  Cpu, 
  ShieldAlert, 
  Info,
  ArrowRight
} from 'lucide-react';

export const dynamic = 'force-dynamic';

export default async function RelationshipsPage() {
  const [{ cases, isMock: casesAreMock }, { dealers, isMock: dealersAreMock }] = await Promise.all([
    getCases(),
    getDealers()
  ]);

  // Fetch spotlight relationship data for CAS-2026-007
  const relationshipData = await getCaseRelationships('CAS-2026-007');

  return (
    <div className="space-y-6 max-w-[1600px] mx-auto pb-12">
      {/* Header */}
      <div className="rounded-2xl border border-[#E5E9F2] bg-white p-5 sm:p-6 shadow-xs flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <div className="h-7 w-7 rounded-lg bg-[#5B4AEF]/10 text-[#5B4AEF] flex items-center justify-center">
              <Network className="h-4 w-4" />
            </div>
            <h1 className="text-xl font-extrabold text-[#182033]">
              Entity Linkage & Relationship Investigation Workspace
            </h1>
          </div>
          <p className="text-xs text-[#68738A] mt-1">
            Multi-entity correlation mapping across Dealer Networks, Borrowers, Verification Cases, and Equipment Registries
          </p>
        </div>

        <div className="flex items-center gap-2 font-mono text-[10px] text-[#68738A] px-3 py-1.5 rounded-lg bg-[#F8FAFD] border border-[#E5E9F2]">
          <Info className="h-3.5 w-3.5 text-[#5B4AEF]" />
          <span>Phase 7 Network Analysis Engine • Weight: 0.0</span>
        </div>
      </div>

      {/* Network Investigation Graph */}
      <div>
        <VerificationNetworkGraph 
          relationshipData={relationshipData}
          cases={cases}
          dealers={dealers}
          isOffline={casesAreMock}
        />
      </div>
    </div>
  );
}
