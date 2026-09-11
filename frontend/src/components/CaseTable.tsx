'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { Case } from '@/types';
import { StatusBadge } from './StatusBadge';
import { Search, ArrowUpRight } from 'lucide-react';

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
    <div className="rounded-2xl border border-[#E5E9F2] bg-white shadow-xs overflow-hidden">
      {/* Table Header Controls */}
      <div className="p-4 sm:p-5 border-b border-[#E5E9F2] flex flex-col sm:flex-row gap-3 sm:items-center sm:justify-between bg-white">
        <div className="flex items-center gap-3">
          <div className="relative flex-1 sm:w-80">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#8E99AD]" />
            <input
              type="text"
              placeholder="Search case #, dealer, customer, asset..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-2 bg-[#F8FAFD] border border-[#E5E9F2] rounded-xl text-xs text-[#182033] placeholder-[#8E99AD] focus:outline-none focus:border-[#4F6EF7] focus:bg-white transition-colors"
            />
          </div>
          {isMock && <StatusBadge type="data_source" value="mock" size="sm" />}
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          <select
            value={riskFilter}
            onChange={(e) => setRiskFilter(e.target.value)}
            aria-label="Filter by risk category"
            className="bg-[#F8FAFD] border border-[#E5E9F2] rounded-xl px-3 py-2 text-xs text-[#182033] focus:outline-none focus:border-[#4F6EF7] font-semibold"
          >
            <option value="all">All Risk Levels</option>
            <option value="high">High Risk</option>
            <option value="medium">Medium Risk</option>
            <option value="low">Low Risk</option>
            <option value="requires_verification">Requires Review</option>
          </select>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            aria-label="Filter by verification status"
            className="bg-[#F8FAFD] border border-[#E5E9F2] rounded-xl px-3 py-2 text-xs text-[#182033] focus:outline-none focus:border-[#4F6EF7] font-semibold"
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
        <table className="w-full text-left text-xs text-[#182033]">
          <thead className="bg-[#F8FAFD] text-[11px] uppercase tracking-wider text-[#68738A] font-bold border-b border-[#E5E9F2]">
            <tr>
              <th className="px-5 py-3.5">Case ID</th>
              <th className="px-5 py-3.5">Dealer</th>
              <th className="px-5 py-3.5">Customer</th>
              <th className="px-5 py-3.5">Asset Model</th>
              <th className="px-5 py-3.5 text-right">Loan Exposure</th>
              <th className="px-5 py-3.5 text-center">Risk Level</th>
              <th className="px-5 py-3.5 text-center">Status</th>
              <th className="px-5 py-3.5 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#E5E9F2]">
            {filteredCases.length === 0 ? (
              <tr>
                <td colSpan={8} className="px-6 py-12 text-center text-[#68738A]">
                  No verification cases match the selected filter criteria.
                </td>
              </tr>
            ) : (
              filteredCases.map((c) => (
                <tr key={c.id} className="hover:bg-[#F8FAFD] transition-colors">
                  <td className="px-5 py-4 font-mono font-bold text-[#4F6EF7] whitespace-nowrap">
                    {c.case_number}
                  </td>
                  <td className="px-5 py-4">
                    <div className="font-semibold text-[#182033] max-w-[200px] truncate">
                      {c.dealer_name || c.dealer_id}
                    </div>
                  </td>
                  <td className="px-5 py-4">
                    <div className="text-[#68738A] max-w-[160px] truncate">
                      {c.customer_name || c.customer_id}
                    </div>
                  </td>
                  <td className="px-5 py-4">
                    <span className="inline-block bg-[#F1F4FA] border border-[#E5E9F2] rounded-md px-2 py-0.5 text-[11px] font-semibold text-[#182033]">
                      {c.asset_type}
                    </span>
                  </td>
                  <td className="px-5 py-4 text-right font-mono font-bold text-[#182033]">
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
                      className="inline-flex items-center gap-1 text-xs font-bold text-[#4F6EF7] hover:text-[#3E5DE6] bg-[#4F6EF7]/10 hover:bg-[#4F6EF7]/15 px-3 py-1.5 rounded-lg transition-colors"
                    >
                      <span>Review</span>
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
      <div className="px-5 py-3 border-t border-[#E5E9F2] text-[11px] text-[#8E99AD] flex justify-between items-center bg-[#F8FAFD]">
        <span>Showing {filteredCases.length} of {cases.length} verification cases</span>
        <span>DIAVN Deterministic Lender OS</span>
      </div>
    </div>
  );
};
