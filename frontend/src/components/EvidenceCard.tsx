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
        return <FileText className="h-4 w-4 text-[#4F6EF7]" />;
      case 'image':
        return <ImageIcon className="h-4 w-4 text-[#5B4AEF]" />;
      case 'geo':
        return <MapPin className="h-4 w-4 text-[#10B981]" />;
      case 'serial_check':
        return <Hash className="h-4 w-4 text-[#F59E0B]" />;
      default:
        return <FileText className="h-4 w-4 text-[#8E99AD]" />;
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'verified':
        return (
          <span className="flex items-center gap-1 text-[11px] text-[#065F46] font-bold px-2 py-0.5 rounded-md bg-[#ECFDF5] border border-[#A7F3D0]">
            <CheckCircle2 className="h-3 w-3" />
            Verified Clean
          </span>
        );
      case 'suspicious':
      case 'flagged':
        return (
          <span className="flex items-center gap-1 text-[11px] text-[#991B1B] font-bold px-2 py-0.5 rounded-md bg-[#FEF2F2] border border-[#FECACA]">
            <AlertTriangle className="h-3 w-3" />
            Anomaly Flagged
          </span>
        );
      case 'pending':
      default:
        return (
          <span className="flex items-center gap-1 text-[11px] text-[#92400E] font-bold px-2 py-0.5 rounded-md bg-[#FFFBEB] border border-[#FDE68A]">
            <Clock className="h-3 w-3" />
            Pending Verification
          </span>
        );
    }
  };

  return (
    <div className="rounded-2xl border border-[#E5E9F2] bg-white p-5 shadow-xs hover:border-[#D1D8E6] transition-all space-y-3">
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-[#F6F8FC] border border-[#E5E9F2]">
            {getIcon(item.type)}
          </div>
          <div>
            <h4 className="text-xs font-bold text-[#182033]">{item.title}</h4>
            <span className="text-[10px] text-[#8E99AD] uppercase font-bold tracking-wider capitalize">
              {item.type.replace('_', ' ')} Telemetry
            </span>
          </div>
        </div>
        <div>{getStatusIcon(item.status)}</div>
      </div>

      <p className="text-xs text-[#68738A] leading-relaxed bg-[#F8FAFD] p-3 rounded-xl border border-[#E5E9F2]">
        {item.details}
      </p>

      <div className="flex justify-between items-center text-[10px] text-[#8E99AD] font-medium pt-1">
        <span>Recorded: {new Date(item.created_at).toLocaleDateString()}</span>
        <span className="font-mono">{item.id}</span>
      </div>
    </div>
  );
};
