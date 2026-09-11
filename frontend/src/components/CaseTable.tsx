'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { Case } from '@/types';
import { StatusBadge } from './StatusBadge';
import { Search, Filter, ArrowUpRight, ShieldAlert, CheckCircle2 } from 'lucide-react';

interface CaseTableProps {
  cases: Case[];
  isMock?: boolean;
}

export const CaseTable: React.FC<CaseTableProps> = ({ cases, isMock = false }) => {
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [riskFilter, setRiskFilter] = useState<string>('all');

  const filteredCases = cases.filter((c) => {
    const matchesSearch =
      c.case_number.toLowerCase().includes(search.toLowerCase()) ||
      (c.dealer_name && c.dealer_name.toLowerCase().includes(search.toLowerCase())) ||
      (c.customer_name && c.customer_name.toLowerCase().includes(search.toLowerCase())) ||
      c.asset_type.toLowerCase().includes(search.toLowerCase());

    const matchesStatus = statusFilter === 'all' || c.status === statusFilter;
    const matchesRisk = riskFilter === 'all' || c.risk_level === riskFilter;

    return matchesSearch && matchesStatus && matchesRisk;
  });

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/70 shadow-xl backdrop-blur-sm overflow-hidden">
      {/* Table Header Controls */}
      <div className="p-4 sm:p-5 border-b border-slate-800 flex flex-col sm:flex-row gap-3 sm:items-center sm:justify-between bg-slate-950/40">
        <div className="flex items-center gap-3">
          <div className="relative flex-1 sm:w-80">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search case #, dealer, customer, asset..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-colors"
            />
          </div>
          {isMock && <StatusBadge type="data_source" value="mock" size="sm" />}
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          <select
            value={riskFilter}
            onChange={(e) => setRiskFilter(e.target.value)}
            aria-label="Filter by risk category"
            className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-300 focus:outline-none focus:border-indigo-500 font-medium"
          >
            <option value="all">All Risk Levels</option>
            <option value="critical">Critical Anomaly</option>
            <option value="high">High Risk</option>
            <option value="medium">Moderate Anomaly</option>
            <option value="low">Low Risk</option>
            <option value="requires_verification">Requires Verification</option>
          </select>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            aria-label="Filter by verification status"
            className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-300 focus:outline-none focus:border-indigo-500 font-medium"
          >
            <option value="all">All Statuses</option>
            <option value="submitted">Submitted</option>
            <option value="under_review">Under Review</option>
            <option value="flagged">Flagged for Audit</option>
            <option value="verified">Verified</option>
          </select>
        </div>
      </div>

      {/* Table Content */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm text-slate-300">
          <thead className="bg-slate-950/80 text-xs uppercase tracking-wider text-slate-400 font-semibold border-b border-slate-800">
            <tr>
              <th className="px-5 py-3.5">Case ID</th>
              <th className="px-5 py-3.5">Dealer</th>
              <th className="px-5 py-3.5">Customer</th>
              <th className="px-5 py-3.5">Asset Model</th>
              <th className="px-5 py-3.5 text-right">Loan Amount</th>
              <th className="px-5 py-3.5 text-center">Risk Level</th>
              <th className="px-5 py-3.5 text-center">Status</th>
              <th className="px-5 py-3.5 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/80">
            {filteredCases.length === 0 ? (
              <tr>
                <td colSpan={8} className="px-6 py-12 text-center text-slate-400">
                  No verification cases matched the filter criteria.
                </td>
              </tr>
            ) : (
              filteredCases.map((c) => (
                <tr key={c.id} className="hover:bg-slate-800/40 transition-colors">
                  <td className="px-5 py-4 font-mono font-medium text-indigo-300 whitespace-nowrap">
                    {c.case_number}
                  </td>
                  <td className="px-5 py-4">
                    <div className="font-medium text-slate-200 max-w-[200px] truncate">
                      {c.dealer_name || c.dealer_id}
                    </div>
                  </td>
                  <td className="px-5 py-4">
                    <div className="text-slate-300 max-w-[160px] truncate">
                      {c.customer_name || c.customer_id}
                    </div>
                  </td>
                  <td className="px-5 py-4">
                    <span className="inline-block bg-slate-800/70 border border-slate-700/60 rounded px-2 py-0.5 text-xs font-mono text-slate-300">
                      {c.asset_type}
                    </span>
                  </td>
                  <td className="px-5 py-4 text-right font-mono font-medium text-slate-200">
                    ₹{c.loan_amount.toLocaleString('en-IN')}
                  </td>
                  <td className="px-5 py-4 text-center">
                    <StatusBadge type="risk" value={c.risk_level} size="sm" />
                  </td>
                  <td className="px-5 py-4 text-center">
                    <StatusBadge type="case_status" value={c.status} size="sm" />
                  </td>
                  <td className="px-5 py-4 text-right">
                    <Link
                      href={`/cases/${c.id}`}
                      className="inline-flex items-center gap-1 text-xs font-medium text-indigo-400 hover:text-indigo-300 bg-indigo-950/40 hover:bg-indigo-900/60 border border-indigo-500/30 px-2.5 py-1 rounded transition-colors"
                    >
                      Review
                      <ArrowUpRight className="h-3.5 w-3.5" />
                    </Link>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Footer Summary */}
      <div className="px-5 py-3 border-t border-slate-800 text-xs text-slate-500 flex justify-between items-center bg-slate-950/30">
        <span>Showing {filteredCases.length} of {cases.length} verification cases</span>
        <span>DIAVN Lender Risk Engine v0.1.0</span>
      </div>
    </div>
  );
};
