import React from 'react';
import Link from 'next/link';
import { getCases } from '@/lib/api';
import { CaseTable } from '@/components/CaseTable';
import { StatusBadge } from '@/components/StatusBadge';
import { FileCheck2, PlusCircle, ShieldAlert } from 'lucide-react';

export const dynamic = 'force-dynamic';

export default async function CasesPage() {
  const { cases, isMock } = await getCases();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
              <FileCheck2 className="h-6 w-6 text-indigo-400" />
              Verification Cases Queue
            </h1>
            {isMock && <StatusBadge type="data_source" value="mock" />}
          </div>
          <p className="mt-1 text-sm text-slate-400">
            Lender asset verification queue with risk signal classification, invoice audits, and serial validation.
          </p>
        </div>

        <Link
          href="/cases/new"
          className="inline-flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold px-4 py-2.5 rounded-lg shadow-lg shadow-indigo-600/20 transition-all border border-indigo-400/30"
        >
          <PlusCircle className="h-4 w-4" />
          <span>New Verification Case</span>
        </Link>
      </div>

      {/* Main Table */}
      <CaseTable cases={cases} isMock={isMock} />
    </div>
  );
}
