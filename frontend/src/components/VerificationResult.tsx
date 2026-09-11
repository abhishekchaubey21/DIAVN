import React from 'react';
import { Shield, ShieldAlert, CheckCircle, Clock, AlertTriangle, Play } from 'lucide-react';
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
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-5 backdrop-blur-md">
      <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <span className="text-xs uppercase font-mono tracking-wider text-slate-400">
            Case Verification Status
          </span>
          <div className="flex items-center gap-2 mt-1">
            <h3 className="text-xl font-bold text-slate-100 font-mono">{caseNumber}</h3>
            <StatusBadge type="case_status" value={status} />
          </div>
        </div>
        <div className="flex items-center gap-2">
          <StatusBadge type="risk" value={riskLevel} />
        </div>
      </div>

      <div className="mt-4 grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
        <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800">
          <div className="text-[11px] uppercase font-semibold text-slate-400">Invoice Extraction</div>
          <div className="text-xs font-mono mt-1 text-slate-300">Phase 1 Staged</div>
        </div>
        <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800">
          <div className="text-[11px] uppercase font-semibold text-slate-400">EXIF & Geo-Tag</div>
          <div className="text-xs font-mono mt-1 text-slate-300">Phase 1 Staged</div>
        </div>
        <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800">
          <div className="text-[11px] uppercase font-semibold text-slate-400">Serial Registry</div>
          <div className="text-xs font-mono mt-1 text-slate-300">Phase 1 Staged</div>
        </div>
        <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800">
          <div className="text-[11px] uppercase font-semibold text-slate-400">Price Benchmark</div>
          <div className="text-xs font-mono mt-1 text-slate-300">Phase 1 Staged</div>
        </div>
      </div>

      <div className="mt-4 flex items-center justify-between gap-3 p-3 bg-indigo-950/20 border border-indigo-500/20 rounded-lg text-xs text-indigo-300">
        <div className="flex items-center gap-2">
          <Clock className="h-4 w-4 text-indigo-400 shrink-0" />
          <span>
            Automated verification pipeline integration will run directly in subsequent phases via Free Gemini API and local CV.
          </span>
        </div>
      </div>
    </div>
  );
};
