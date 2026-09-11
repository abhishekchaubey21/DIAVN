import React from 'react';
import { Shield, ShieldAlert, CheckCircle, Clock, AlertTriangle, Layers } from 'lucide-react';
import { StatusBadge } from './StatusBadge';

interface VerificationResultProps {
  status: string;
  riskLevel: string;
  caseNumber: string;
}

export const VerificationResult: React.FC<VerificationResultProps> = ({
  status,
  riskLevel,
  caseNumber,
}) => {
  const isHigh = riskLevel === 'high' || riskLevel === 'critical';
  const isMed = riskLevel === 'medium';

  return (
    <div className="rounded-2xl border border-[#E5E9F2] bg-white p-6 sm:p-7 shadow-xs space-y-6">
      {/* Header Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-5 border-b border-[#E5E9F2]">
        <div>
          <span className="text-[10px] font-bold uppercase tracking-wider text-[#8E99AD] block">
            Underwriting Case Status
          </span>
          <div className="flex items-center gap-3 mt-1">
            <h2 className="text-2xl font-extrabold text-[#182033] font-mono tracking-tight">{caseNumber}</h2>
            <StatusBadge type="case_status" value={status} />
          </div>
        </div>
        <div className="flex items-center gap-3">
          <StatusBadge type="risk" value={riskLevel} size="md" />
        </div>
      </div>

      {/* 4 Pipeline Stage Badges */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
        <div className="p-3.5 rounded-xl bg-[#F8FAFD] border border-[#E5E9F2]">
          <div className="text-[10px] uppercase font-bold text-[#8E99AD] tracking-wider">Invoice OCR & Pricing</div>
          <div className="text-xs font-mono font-bold mt-1 text-[#182033]">Phase 2 & 3 Verified</div>
        </div>
        <div className="p-3.5 rounded-xl bg-[#F8FAFD] border border-[#E5E9F2]">
          <div className="text-[10px] uppercase font-bold text-[#8E99AD] tracking-wider">EXIF & Geo-Tag</div>
          <div className="text-xs font-mono font-bold mt-1 text-[#182033]">Phase 4 Audited</div>
        </div>
        <div className="p-3.5 rounded-xl bg-[#F8FAFD] border border-[#E5E9F2]">
          <div className="text-[10px] uppercase font-bold text-[#8E99AD] tracking-wider">Visual Embeddings</div>
          <div className="text-xs font-mono font-bold mt-1 text-[#182033]">Phase 5 Similarity</div>
        </div>
        <div className="p-3.5 rounded-xl bg-[#F8FAFD] border border-[#E5E9F2]">
          <div className="text-[10px] uppercase font-bold text-[#8E99AD] tracking-wider">Entity Link Graph</div>
          <div className="text-xs font-mono font-bold mt-1 text-[#182033]">Phase 7 Analyzed</div>
        </div>
      </div>

      {/* Orchestration Status Bar */}
      <div className="flex items-center gap-2.5 p-3.5 bg-[#F6F8FC] border border-[#E5E9F2] rounded-xl text-xs text-[#68738A]">
        <Clock className="h-4 w-4 text-[#4F6EF7] shrink-0" />
        <span>
          Automated multi-factor underwriting pipeline executing deterministic verification across OCR, perceptual hash, visual similarity, and entity link graphs.
        </span>
      </div>
    </div>
  );
};
