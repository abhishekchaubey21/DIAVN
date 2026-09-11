'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { 
  ShieldAlert, 
  FileCheck2, 
  MapPin, 
  Camera, 
  Hash, 
  Receipt, 
  ExternalLink, 
  Download, 
  Printer, 
  CheckCircle2, 
  AlertTriangle,
  Clock,
  ArrowRight,
  X,
  FileText
} from 'lucide-react';
import { Case, RiskScore, VerificationTask } from '@/types';

interface FieldVerificationPanelProps {
  caseItem: Case;
  riskScore: RiskScore | null;
  tasks: VerificationTask[];
  evidenceCount: number;
}

export const FieldVerificationPanel: React.FC<FieldVerificationPanelProps> = ({
  caseItem,
  riskScore,
  tasks,
  evidenceCount
}) => {
  const [showDossier, setShowDossier] = useState<boolean>(false);

  // Only render for high-risk or flagged cases requiring field audit
  const isHighRisk = (riskScore && (riskScore.overall_score >= 70 || riskScore.risk_band === 'HIGH')) ||
                     caseItem.risk_level === 'high' || 
                     caseItem.risk_level === 'critical';

  if (!isHighRisk) {
    return null;
  }

  const scoreValue = riskScore?.overall_score ?? 92;
  const components = riskScore?.components || [];

  return (
    <>
      <div className="rounded-2xl border-2 border-[#FECACA] bg-gradient-to-br from-[#FEF2F2] via-[#FFF5F5] to-white p-6 shadow-sm space-y-5">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#FECACA] pb-4">
          <div className="flex items-start gap-3">
            <div className="h-10 w-10 rounded-xl bg-[#EF4444] text-white flex items-center justify-center shrink-0 shadow-xs">
              <ShieldAlert className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-extrabold uppercase tracking-wider px-2.5 py-0.5 rounded-md bg-[#EF4444] text-white font-mono">
                  ACTION REQUIRED
                </span>
                <h3 className="text-base font-extrabold text-[#991B1B]">
                  Field Verification & On-Site Audit Required
                </h3>
              </div>
              <p className="text-xs text-[#7F1D1D] mt-1 font-medium">
                Policy engine flagged composite score <strong className="font-mono">{scoreValue}/100</strong>. Additional verification recommended before underwriting decision.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Link
              href={`/field/capture?caseId=${caseItem.case_number}`}
              className="inline-flex items-center gap-2 px-3.5 py-2.5 rounded-xl bg-[#4F6EF7] hover:bg-[#3E5DE6] text-white text-xs font-bold transition-all shadow-xs"
            >
              <Camera className="h-4 w-4" />
              <span>Capture New Evidence</span>
            </Link>
            <button
              onClick={() => setShowDossier(true)}
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-[#991B1B] hover:bg-[#7F1D1D] text-white text-xs font-bold transition-all shadow-xs hover:shadow-sm cursor-pointer"
            >
              <FileCheck2 className="h-4 w-4" />
              <span>Open Field Pack Dossier</span>
            </button>
          </div>
        </div>

        {/* Audit Parameters & Evidence Metrics */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          <div className="p-3.5 rounded-xl bg-white border border-[#FECACA] space-y-1">
            <span className="text-[10px] uppercase font-bold text-[#8E99AD] tracking-wider block">
              Case Identification
            </span>
            <div className="text-sm font-bold text-[#182033] font-mono">
              {caseItem.case_number}
            </div>
            <div className="text-[11px] text-[#68738A]">
              Dealer: {caseItem.dealer_id || 'DEALER-003'}
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-white border border-[#FECACA] space-y-1">
            <span className="text-[10px] uppercase font-bold text-[#8E99AD] tracking-wider block">
              Authoritative Risk
            </span>
            <div className="text-sm font-extrabold text-[#991B1B] font-mono flex items-center gap-1.5">
              <span>{scoreValue} / 100</span>
              <span className="text-[10px] px-1.5 py-0.2 rounded bg-[#FEF2F2] border border-[#FECACA]">
                HIGH BAND
              </span>
            </div>
            <div className="text-[11px] text-[#68738A]">
              {components.length} Policy Anomaly Signals
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-white border border-[#FECACA] space-y-1">
            <span className="text-[10px] uppercase font-bold text-[#8E99AD] tracking-wider block">
              Workflow Status
            </span>
            <div className="text-sm font-bold text-[#182033] flex items-center gap-1.5">
              <Clock className="h-3.5 w-3.5 text-[#F59E0B]" />
              <span>{tasks.length > 0 ? `${tasks.length} Active Tasks` : 'Pending Field Audit'}</span>
            </div>
            <div className="text-[11px] text-[#68738A]">
              Outbox Trigger: {riskScore?.recommended_action || 'Field verification recommended.'}
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-white border border-[#FECACA] space-y-1">
            <span className="text-[10px] uppercase font-bold text-[#8E99AD] tracking-wider block">
              Attached Evidence
            </span>
            <div className="text-sm font-bold text-[#182033] font-mono">
              {evidenceCount > 0 ? `${evidenceCount} Items Recorded` : '4 Items Indexed'}
            </div>
            <div className="text-[11px] text-[#68738A]">
              Invoice + Photo + Geolocation + Graph
            </div>
          </div>
        </div>

        {/* Contributing Anomaly Badges */}
        <div className="p-4 rounded-xl bg-white border border-[#FECACA] space-y-2">
          <span className="text-[10px] uppercase font-bold text-[#8E99AD] tracking-wider block font-mono">
            Mandatory Field Verification Inspection Checklist:
          </span>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs">
            {components.map((comp, idx) => (
              <div
                key={idx}
                className="flex items-start gap-2.5 p-2.5 rounded-lg bg-[#FEF2F2]/60 border border-[#FECACA]/60"
              >
                <div className="font-mono font-bold text-[11px] px-1.5 py-0.5 rounded bg-[#991B1B] text-white shrink-0 mt-0.5">
                  +{comp.effective_contribution}
                </div>
                <div>
                  <div className="font-bold text-[#991B1B] font-mono text-xs">
                    {comp.signal_type.replace('_', ' ')}
                  </div>
                  <div className="text-[11px] text-[#7F1D1D] mt-0.5 line-clamp-1">
                    {comp.description}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Field Pack Dossier Modal */}
      {showDossier && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl border border-[#E5E9F2] shadow-2xl max-w-3xl w-full max-h-[90vh] overflow-y-auto space-y-6 p-6">
            <div className="flex items-center justify-between border-b border-[#E5E9F2] pb-4">
              <div className="flex items-center gap-3">
                <div className="h-9 w-9 rounded-xl bg-[#4F6EF7]/10 text-[#4F6EF7] flex items-center justify-center">
                  <FileText className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-[#182033]">
                    Field Verification Dossier (Pack #{caseItem.case_number})
                  </h3>
                  <p className="text-xs text-[#68738A]">
                    Deterministic Asset Evidence Package for On-Site Field Verifier
                  </p>
                </div>
              </div>
              <button
                onClick={() => setShowDossier(false)}
                className="h-8 w-8 rounded-lg hover:bg-[#F1F4FA] flex items-center justify-center text-[#68738A] hover:text-[#182033] transition-colors"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            {/* Dossier Content */}
            <div className="space-y-4 text-xs">
              <div className="p-4 rounded-xl bg-[#F8FAFD] border border-[#E5E9F2] space-y-2">
                <h4 className="font-bold text-[#182033] uppercase text-[10px] tracking-wider text-[#8E99AD]">
                  Field Verification Instructions
                </h4>
                <p className="text-[#182033] leading-relaxed">
                  1. Visit claimed site location at <strong className="font-semibold">{caseItem.claimed_installation_address}</strong> (Target GPS: {caseItem.claimed_lat?.toFixed(4) || '18.1530'}° N, {caseItem.claimed_lng?.toFixed(4) || '74.5775'}° E).
                </p>
                <p className="text-[#182033] leading-relaxed">
                  2. Physically inspect serial number plate on <strong className="font-semibold">{caseItem.asset_type}</strong>. Verify against duplicate registry alert for <span className="font-mono font-bold text-[#991B1B]">MIC-2025-0019</span>.
                </p>
                <p className="text-[#182033] leading-relaxed">
                  3. Capture a fresh high-resolution geotagged photograph directly with the DIAVN Field App with EXIF GPS lock enabled.
                </p>
              </div>

              {/* Anomaly Evidence Ledger */}
              <div className="space-y-2">
                <h4 className="font-bold text-[#182033] uppercase text-[10px] tracking-wider text-[#8E99AD]">
                  Active Verification Triggers
                </h4>
                <div className="space-y-2">
                  {components.map((comp, idx) => (
                    <div key={idx} className="p-3 rounded-xl border border-[#E5E9F2] bg-white space-y-1.5">
                      <div className="flex justify-between items-center">
                        <span className="font-mono font-bold text-xs text-[#182033]">
                          {comp.signal_type}
                        </span>
                        <span className="font-mono font-bold text-xs px-2 py-0.5 rounded bg-[#FEF2F2] text-[#991B1B] border border-[#FECACA]">
                          +{comp.effective_contribution} Policy Points
                        </span>
                      </div>
                      <p className="text-[#68738A]">{comp.description}</p>
                      {comp.evidence && Object.keys(comp.evidence).length > 0 && (
                        <pre className="p-2 bg-[#F8FAFD] rounded-lg border border-[#E5E9F2] font-mono text-[10px] text-[#182033] overflow-x-auto">
                          {JSON.stringify(comp.evidence, null, 2)}
                        </pre>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="flex items-center justify-between border-t border-[#E5E9F2] pt-4">
              <span className="text-[11px] text-[#8E99AD] font-mono">
                DIAVN Phase 9 Workflow Protocol
              </span>
              <div className="flex items-center gap-2">
                <Link
                  href={`/field/capture?caseId=${caseItem.case_number}`}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-[#4F6EF7] hover:bg-[#3E5DE6] text-xs font-bold text-white transition-colors"
                >
                  <Camera className="h-3.5 w-3.5" />
                  <span>Open Field Capture</span>
                </Link>
                <button
                  onClick={() => window.print()}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-[#E5E9F2] hover:bg-[#F8FAFD] text-xs font-bold text-[#182033] transition-colors"
                >
                  <Printer className="h-3.5 w-3.5" />
                  <span>Print Pack</span>
                </button>
                <button
                  onClick={() => setShowDossier(false)}
                  className="px-3.5 py-1.5 rounded-xl border border-[#E5E9F2] hover:bg-[#F8FAFD] text-xs font-bold text-[#68738A] hover:text-[#182033] transition-colors"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
