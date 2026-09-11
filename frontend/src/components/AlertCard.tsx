import React from 'react';
import { RiskSignal } from '@/types';
import { AlertCircle, AlertTriangle, Info, CheckCircle2, ShieldAlert } from 'lucide-react';

interface AlertCardProps {
  signal: RiskSignal;
}

export const AlertCard: React.FC<AlertCardProps> = ({ signal }) => {
  const getSeverityStyle = (severity: string) => {
    switch (severity) {
      case 'critical':
        return {
          border: 'border-rose-500/50 bg-rose-950/30 text-rose-300',
          badge: 'bg-rose-900/60 text-rose-200 border-rose-500/40',
          icon: <ShieldAlert className="h-5 w-5 text-rose-400 shrink-0" />,
        };
      case 'high':
        return {
          border: 'border-orange-500/40 bg-orange-950/25 text-orange-300',
          badge: 'bg-orange-900/60 text-orange-200 border-orange-500/40',
          icon: <AlertTriangle className="h-5 w-5 text-orange-400 shrink-0" />,
        };
      case 'medium':
        return {
          border: 'border-amber-500/40 bg-amber-950/20 text-amber-300',
          badge: 'bg-amber-900/60 text-amber-200 border-amber-500/40',
          icon: <AlertCircle className="h-5 w-5 text-amber-400 shrink-0" />,
        };
      default:
        return {
          border: 'border-blue-500/30 bg-blue-950/20 text-blue-300',
          badge: 'bg-blue-900/60 text-blue-200 border-blue-500/30',
          icon: <Info className="h-5 w-5 text-blue-400 shrink-0" />,
        };
    }
  };

  const style = getSeverityStyle(signal.severity);

  return (
    <div className={`rounded-xl border p-4.5 transition-all ${style.border}`}>
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          {style.icon}
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h4 className="text-sm font-bold text-slate-100 font-mono">
                {signal.signal_name}
              </h4>
              <span className={`text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded border ${style.badge}`}>
                {signal.severity}
              </span>
              <span className="text-xs font-mono text-slate-400">
                Confidence: {signal.confidence_score}%
              </span>
            </div>
            <p className="mt-1.5 text-xs text-slate-300 leading-relaxed">
              {signal.description}
            </p>
          </div>
        </div>
      </div>

      {signal.evidence_payload && Object.keys(signal.evidence_payload).length > 0 && (
        <div className="mt-3.5 pt-3 border-t border-slate-800/80">
          <div className="text-[11px] uppercase tracking-wider font-semibold text-slate-400 mb-1.5 font-mono">
            Deterministic Evidence Payload
          </div>
          <div className="bg-slate-950/80 rounded-lg p-3 font-mono text-xs text-slate-300 overflow-x-auto border border-slate-800">
            <pre className="whitespace-pre-wrap">{JSON.stringify(signal.evidence_payload, null, 2)}</pre>
          </div>
        </div>
      )}
    </div>
  );
};
