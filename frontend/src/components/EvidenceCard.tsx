import React from 'react';
import { EvidenceItem } from '@/types';
import { FileText, Image as ImageIcon, MapPin, Hash, CheckCircle2, AlertTriangle, Clock } from 'lucide-react';

interface EvidenceCardProps {
  item: EvidenceItem;
}

export const EvidenceCard: React.FC<EvidenceCardProps> = ({ item }) => {
  const getIcon = (type: string) => {
    switch (type) {
      case 'invoice':
        return <FileText className="h-4 w-4 text-blue-400" />;
      case 'image':
        return <ImageIcon className="h-4 w-4 text-purple-400" />;
      case 'geo':
        return <MapPin className="h-4 w-4 text-emerald-400" />;
      case 'serial_check':
        return <Hash className="h-4 w-4 text-amber-400" />;
      default:
        return <FileText className="h-4 w-4 text-slate-400" />;
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'verified':
        return (
          <span className="flex items-center gap-1 text-xs text-emerald-400 font-medium">
            <CheckCircle2 className="h-3.5 w-3.5" />
            Verified Clean
          </span>
        );
      case 'suspicious':
        return (
          <span className="flex items-center gap-1 text-xs text-rose-400 font-medium">
            <AlertTriangle className="h-3.5 w-3.5" />
            Anomaly Flagged
          </span>
        );
      case 'pending':
      default:
        return (
          <span className="flex items-center gap-1 text-xs text-slate-400 font-medium">
            <Clock className="h-3.5 w-3.5" />
            Pending Verification
          </span>
        );
    }
  };

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 transition-all hover:border-slate-700">
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <div className="p-2 rounded-lg bg-slate-800/80 border border-slate-700/60">
            {getIcon(item.type)}
          </div>
          <div>
            <h4 className="text-sm font-semibold text-slate-200">{item.title}</h4>
            <span className="text-[11px] text-slate-500 capitalize">{item.type.replace('_', ' ')} Evidence</span>
          </div>
        </div>
        <div>{getStatusIcon(item.status)}</div>
      </div>

      <p className="mt-3 text-xs text-slate-300 leading-relaxed font-normal bg-slate-950/40 p-2.5 rounded-lg border border-slate-800/60">
        {item.details}
      </p>

      <div className="mt-2.5 flex justify-between items-center text-[11px] text-slate-500">
        <span>Recorded: {new Date(item.created_at).toLocaleDateString()}</span>
        <span className="font-mono">{item.id}</span>
      </div>
    </div>
  );
};
