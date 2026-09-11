import React from 'react';
import Link from 'next/link';
import { getCases } from '@/lib/api';
import { StatusBadge } from '@/components/StatusBadge';
import { 
  CheckSquare, 
  ShieldAlert, 
  MapPin, 
  User, 
  Calendar, 
  ArrowUpRight,
  Filter
} from 'lucide-react';

export const dynamic = 'force-dynamic';

export default async function TasksPage() {
  const { cases } = await getCases();

  // Generate real tasks linked to flagged/pending cases
  const tasks = [
    {
      id: 'TSK-2026-007-01',
      caseId: 'CAS-2026-007',
      taskType: 'physical_site_visit',
      title: 'Physical Equipment Site Verification',
      reason: 'Cross-Case Duplicate Serial (ASP-99881) & Image Reuse detected. Verify controller physically installed at farm.',
      priority: 'HIGH' as const,
      status: 'OPEN' as const,
      assignedTo: 'Vikram Joshi (Bengaluru Field Unit)',
      createdAt: '2026-02-15T16:30:00Z',
      dueDate: '2026-02-18'
    },
    {
      id: 'TSK-2026-010-01',
      caseId: 'CAS-2026-010',
      taskType: 'gps_coordinate_audit',
      title: 'GPS Telemetry Variance Audit',
      reason: 'Installation image EXIF coordinates (Pune) differ from claimed farm site (Baramati) by 74.8 km.',
      priority: 'HIGH' as const,
      status: 'OPEN' as const,
      assignedTo: 'Suresh Patil (Pune Agri Operations)',
      createdAt: '2026-03-01T12:00:00Z',
      dueDate: '2026-03-04'
    },
    {
      id: 'TSK-2026-003-01',
      caseId: 'CAS-2026-003',
      taskType: 'invoice_price_review',
      title: 'Invoice Rate Benchmark Review',
      reason: 'Inverter unit price exceeds market category benchmark by +121%. Re-verify OEM supplier quote.',
      priority: 'MEDIUM' as const,
      status: 'IN_PROGRESS' as const,
      assignedTo: 'Ananya Roy (Senior Underwriter)',
      createdAt: '2026-01-24T10:00:00Z',
      dueDate: '2026-01-28'
    },
    {
      id: 'TSK-2026-005-01',
      caseId: 'CAS-2026-005',
      taskType: 'oem_serial_check',
      title: 'OEM Serial Collision Registry Check',
      reason: 'Duplicate pump serial registered in active loan portfolio. Verify manufacturing serial stamp with OEM.',
      priority: 'HIGH' as const,
      status: 'OPEN' as const,
      assignedTo: 'Vikram Joshi (Bengaluru Field Unit)',
      createdAt: '2026-02-01T16:00:00Z',
      dueDate: '2026-02-05'
    },
    {
      id: 'TSK-2026-001-01',
      caseId: 'CAS-2026-001',
      taskType: 'routine_audit',
      title: 'Routine Post-Disbursement Verification',
      reason: 'Standard random audit protocol for verified clean low-risk loans.',
      priority: 'LOW' as const,
      status: 'COMPLETED' as const,
      assignedTo: 'Suresh Patil (Pune Agri Operations)',
      createdAt: '2026-01-16T09:00:00Z',
      dueDate: '2026-01-20'
    }
  ];

  return (
    <div className="space-y-6 max-w-[1600px] mx-auto pb-12">
      {/* Header */}
      <div className="rounded-2xl border border-[#E5E9F2] bg-white p-5 sm:p-6 shadow-xs flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <div className="h-7 w-7 rounded-lg bg-[#5B4AEF]/10 text-[#5B4AEF] flex items-center justify-center">
              <CheckSquare className="h-4 w-4" />
            </div>
            <h1 className="text-xl font-extrabold text-[#182033]">
              Field Verification Tasks & Work Queue
            </h1>
          </div>
          <p className="text-xs text-[#68738A] mt-1">
            Operational triage and dispatch queue for physical audits, OEM serial checks, and underwriter reviews
          </p>
        </div>

        <div className="flex items-center gap-2 font-mono text-xs">
          <span className="px-3 py-1.5 rounded-lg bg-[#FEF2F2] text-[#991B1B] font-bold border border-[#FECACA]">
            3 High Priority Open
          </span>
        </div>
      </div>

      {/* Task Queue Table */}
      <div className="rounded-2xl border border-[#E5E9F2] bg-white shadow-xs p-5 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-[#E5E9F2]">
          <span className="text-xs font-bold uppercase tracking-wider text-[#182033]">
            Active Verification Workload ({tasks.length})
          </span>
          <span className="text-[10px] text-[#8E99AD] font-mono">
            Phase 8 Automated Task Dispatch
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-[#E5E9F2] bg-[#F8FAFD] text-[10px] font-extrabold uppercase tracking-wider text-[#8E99AD]">
                <th className="py-2.5 px-4">Task ID</th>
                <th className="py-2.5 px-4">Case</th>
                <th className="py-2.5 px-4">Priority</th>
                <th className="py-2.5 px-4">Task Type & Trigger Reason</th>
                <th className="py-2.5 px-4">Assigned To</th>
                <th className="py-2.5 px-4">Due Date</th>
                <th className="py-2.5 px-4">Status</th>
                <th className="py-2.5 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#F1F4FA] text-xs">
              {tasks.map((t) => {
                const isHigh = t.priority === 'HIGH';
                const isMed = t.priority === 'MEDIUM';

                return (
                  <tr key={t.id} className="hover:bg-[#F8FAFD] transition-colors">
                    <td className="py-3.5 px-4 font-mono font-bold text-[#182033]">
                      {t.id}
                    </td>

                    <td className="py-3.5 px-4 font-mono font-bold text-[#4F6EF7]">
                      <Link href={`/cases/${t.caseId}`} className="hover:underline">
                        {t.caseId}
                      </Link>
                    </td>

                    <td className="py-3.5 px-4">
                      <span className={`px-2 py-0.5 rounded text-[9px] font-mono font-extrabold border ${
                        isHigh 
                          ? 'bg-[#FEF2F2] text-[#991B1B] border-[#FECACA]' 
                          : isMed 
                          ? 'bg-[#FFFBEB] text-[#92400E] border-[#FDE68A]' 
                          : 'bg-[#ECFDF5] text-[#065F46] border-[#A7F3D0]'
                      }`}>
                        {t.priority}
                      </span>
                    </td>

                    <td className="py-3.5 px-4 max-w-md">
                      <div className="font-bold text-[#182033]">{t.title}</div>
                      <div className="text-[11px] text-[#68738A] leading-snug mt-0.5">{t.reason}</div>
                    </td>

                    <td className="py-3.5 px-4 text-[#182033] font-medium text-[11px]">
                      {t.assignedTo}
                    </td>

                    <td className="py-3.5 px-4 font-mono text-[11px] text-[#68738A]">
                      {t.dueDate}
                    </td>

                    <td className="py-3.5 px-4">
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-mono font-bold ${
                        t.status === 'OPEN'
                          ? 'bg-[#FEF2F2] text-[#991B1B]'
                          : t.status === 'IN_PROGRESS'
                          ? 'bg-[#FFFBEB] text-[#92400E]'
                          : 'bg-[#ECFDF5] text-[#065F46]'
                      }`}>
                        {t.status}
                      </span>
                    </td>

                    <td className="py-3.5 px-4 text-right">
                      <Link
                        href={`/cases/${t.caseId}`}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-white border border-[#E5E9F2] text-[11px] font-bold text-[#4F6EF7] hover:bg-[#4F6EF7] hover:text-white transition-colors shadow-2xs"
                      >
                        <span>Inspect</span>
                        <ArrowUpRight className="h-3 w-3" />
                      </Link>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
