import React from 'react';
import { RiskSignal } from '@/types';
import { AlertCircle, AlertTriangle, Info, ShieldAlert } from 'lucide-react';

interface AlertCardProps {
  signal: RiskSignal;
}

export const AlertCard: React.FC<AlertCardProps> = ({ signal }) => {
  const getSeverityStyle = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical':
      case 'high':
        return {
          border: 'border-[#FECACA] bg-[#FEF2F2]/40',
          badge: 'bg-[#FEF2F2] text-[#991B1B] border-[#FECACA]',
          icon: <ShieldAlert className="h-5 w-5 text-[#EF4444] shrink-0" />,
        };
      case 'medium':
        return {
          border: 'border-[#FDE68A] bg-[#FFFBEB]/40',
          badge: 'bg-[#FFFBEB] text-[#92400E] border-[#FDE68A]',
          icon: <AlertTriangle className="h-5 w-5 text-[#F59E0B] shrink-0" />,
        };
      default:
        return {
          border: 'border-[#E5E9F2] bg-white',
          badge: 'bg-[#F6F8FC] text-[#4F6EF7] border-[#E5E9F2]',
          icon: <Info className="h-5 w-5 text-[#4F6EF7] shrink-0" />,
        };
    }
  };

  const style = getSeverityStyle(signal.severity);

  return (
    <div className={`rounded-2xl border p-5 shadow-xs transition-all space-y-3 ${style.border}`}>
      <div className="flex items-start gap-3.5">
        {style.icon}
        <div className="space-y-1 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h4 className="text-xs font-bold text-[#182033] font-mono">
              {signal.signal_name}
            </h4>
            <span className={`text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-md border ${style.badge}`}>
              {signal.severity}
            </span>
            <span className="text-[11px] font-mono font-semibold text-[#8E99AD]">
              Confidence: {signal.confidence_score}%
            </span>
          </div>
          <p className="text-xs text-[#68738A] leading-relaxed">
            {signal.description}
          </p>
        </div>
      </div>

      {signal.evidence_payload && Object.keys(signal.evidence_payload).length > 0 && (
        <div className="pt-3 border-t border-[#E5E9F2]">
          <div className="text-[10px] uppercase tracking-wider font-bold text-[#8E99AD] mb-1.5 font-mono">
            Deterministic Evidence Payload
          </div>
          <div className="bg-[#F8FAFD] rounded-xl p-3 font-mono text-[11px] text-[#182033] overflow-x-auto border border-[#E5E9F2]">
            <pre className="whitespace-pre-wrap">{JSON.stringify(signal.evidence_payload, null, 2)}</pre>
          </div>
        </div>
      )}
    </div>
  );
};
