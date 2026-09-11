import React from 'react';
import Link from 'next/link';
import { getCases } from '@/lib/api';
import { 
  Camera, 
  CheckCircle2, 
  AlertTriangle, 
  MapPin, 
  Fingerprint, 
  ArrowUpRight,
  ShieldCheck
} from 'lucide-react';

export const dynamic = 'force-dynamic';

export default async function ForensicsPage() {
  const { cases } = await getCases();

  const forensicItems = [
    {
      imageId: 'IMG-2026-001-A',
      caseId: 'CAS-2026-001',
      assetType: 'Solar Water Pump 5HP',
      exifStatus: 'PASS' as const,
      timestampStatus: 'PASS' as const,
      phashStatus: 'PASS' as const,
      phashScore: 'Dist: 18 (Unique)',
      embeddingStatus: 'PASS' as const,
      embeddingScore: 'Sim: 0.12',
      gpsStatus: 'PASS' as const,
      gpsVariance: '0.4 km',
      overallStatus: 'PASS' as const
    },
    {
      imageId: 'IMG-2026-007-A',
      caseId: 'CAS-2026-007',
      assetType: 'Micro-Irrigation Controller',
      exifStatus: 'PASS' as const,
      timestampStatus: 'PASS' as const,
      phashStatus: 'ANOMALY' as const,
      phashScore: 'Dist: 4 (Match)',
      embeddingStatus: 'ANOMALY' as const,
      embeddingScore: 'Sim: 0.94 (Duplicate)',
      gpsStatus: 'ANOMALY' as const,
      gpsVariance: 'Coincides with dealer yard',
      overallStatus: 'ANOMALY' as const
    },
    {
      imageId: 'IMG-2026-010-A',
      caseId: 'CAS-2026-010',
      assetType: 'Solar Water Pump 5HP',
      exifStatus: 'PASS' as const,
      timestampStatus: 'PASS' as const,
      phashStatus: 'PASS' as const,
      phashScore: 'Dist: 21 (Unique)',
      embeddingStatus: 'PASS' as const,
      embeddingScore: 'Sim: 0.18',
      gpsStatus: 'ANOMALY' as const,
      gpsVariance: '74.8 km EXIF Mismatch',
      overallStatus: 'ANOMALY' as const
    }
  ];

  return (
    <div className="space-y-6 max-w-[1600px] mx-auto pb-12">
      {/* Header */}
      <div className="rounded-2xl border border-[#E5E9F2] bg-white p-5 sm:p-6 shadow-xs flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <div className="h-7 w-7 rounded-lg bg-[#5B4AEF]/10 text-[#5B4AEF] flex items-center justify-center">
              <Camera className="h-4 w-4" />
            </div>
            <h1 className="text-xl font-extrabold text-[#182033]">
              Image Forensics & Visual Verification Workspace
            </h1>
          </div>
          <p className="text-xs text-[#68738A] mt-1">
            EXIF metadata tampering inspection, perceptual pHash reuse detection, deep visual embedding similarity, and GPS telemetry verification
          </p>
        </div>

        <div className="flex items-center gap-2 font-mono text-[10px] text-[#68738A] px-3 py-1.5 rounded-lg bg-[#F8FAFD] border border-[#E5E9F2]">
          <Fingerprint className="h-3.5 w-3.5 text-[#5B4AEF]" />
          <span>Phases 4 & 5 Forensic Engines Active</span>
        </div>
      </div>

      {/* Forensic Inspection Table */}
      <div className="rounded-2xl border border-[#E5E9F2] bg-white shadow-xs p-5 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-[#E5E9F2]">
          <span className="text-xs font-bold uppercase tracking-wider text-[#182033]">
            Installation Image Forensic Audits ({forensicItems.length})
          </span>
          <span className="text-[10px] text-[#8E99AD] font-mono">
            Thresholds: pHash &le; 10, Embedding Sim &ge; 0.85, GPS &ge; 10 km
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-[#E5E9F2] bg-[#F8FAFD] text-[10px] font-extrabold uppercase tracking-wider text-[#8E99AD]">
                <th className="py-2.5 px-4">Image ID</th>
                <th className="py-2.5 px-4">Case</th>
                <th className="py-2.5 px-4">Asset</th>
                <th className="py-2.5 px-4">EXIF & Timestamp</th>
                <th className="py-2.5 px-4">pHash Deduplication</th>
                <th className="py-2.5 px-4">Visual Embedding (Sim)</th>
                <th className="py-2.5 px-4">GPS Telemetry Check</th>
                <th className="py-2.5 px-4">Forensic Outcome</th>
                <th className="py-2.5 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#F1F4FA] text-xs">
              {forensicItems.map((item) => {
                const isAnomaly = item.overallStatus === 'ANOMALY';

                return (
                  <tr key={item.imageId} className="hover:bg-[#F8FAFD] transition-colors">
                    <td className="py-3.5 px-4 font-mono font-bold text-[#182033]">
                      {item.imageId}
                    </td>

                    <td className="py-3.5 px-4 font-mono font-bold text-[#4F6EF7]">
                      <Link href={`/cases/${item.caseId}`} className="hover:underline">
                        {item.caseId}
                      </Link>
                    </td>

                    <td className="py-3.5 px-4 text-[#182033] font-medium">
                      {item.assetType}
                    </td>

                    <td className="py-3.5 px-4">
                      <span className="text-[#065F46] font-semibold flex items-center gap-1">
                        <CheckCircle2 className="h-3 w-3 text-[#10B981]" />
                        <span>Valid EXIF</span>
                      </span>
                    </td>

                    <td className="py-3.5 px-4">
                      {item.phashStatus === 'PASS' ? (
                        <span className="text-[#065F46] font-mono font-semibold flex items-center gap-1">
                          <CheckCircle2 className="h-3 w-3 text-[#10B981]" />
                          <span>{item.phashScore}</span>
                        </span>
                      ) : (
                        <span className="text-[#991B1B] font-mono font-bold flex items-center gap-1">
                          <AlertTriangle className="h-3 w-3 text-[#EF4444]" />
                          <span>{item.phashScore}</span>
                        </span>
                      )}
                    </td>

                    <td className="py-3.5 px-4">
                      {item.embeddingStatus === 'PASS' ? (
                        <span className="text-[#065F46] font-mono font-semibold flex items-center gap-1">
                          <CheckCircle2 className="h-3 w-3 text-[#10B981]" />
                          <span>{item.embeddingScore}</span>
                        </span>
                      ) : (
                        <span className="text-[#991B1B] font-mono font-bold flex items-center gap-1">
                          <AlertTriangle className="h-3 w-3 text-[#EF4444]" />
                          <span>{item.embeddingScore}</span>
                        </span>
                      )}
                    </td>

                    <td className="py-3.5 px-4">
                      {item.gpsStatus === 'PASS' ? (
                        <span className="text-[#065F46] font-mono font-semibold flex items-center gap-1">
                          <CheckCircle2 className="h-3 w-3 text-[#10B981]" />
                          <span>{item.gpsVariance}</span>
                        </span>
                      ) : (
                        <span className="text-[#991B1B] font-mono font-bold flex items-center gap-1">
                          <MapPin className="h-3 w-3 text-[#EF4444]" />
                          <span>{item.gpsVariance}</span>
                        </span>
                      )}
                    </td>

                    <td className="py-3.5 px-4">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                        item.overallStatus === 'PASS'
                          ? 'bg-[#ECFDF5] text-[#065F46] border border-[#A7F3D0]'
                          : 'bg-[#FEF2F2] text-[#991B1B] border border-[#FECACA]'
                      }`}>
                        {item.overallStatus}
                      </span>
                    </td>

                    <td className="py-3.5 px-4 text-right">
                      <Link
                        href={`/cases/${item.caseId}`}
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
