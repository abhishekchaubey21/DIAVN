import React from 'react';
import Link from 'next/link';
import { 
  Settings, 
  Cpu, 
  ShieldCheck, 
  Bell, 
  Lock, 
  User, 
  CheckCircle2, 
  Sliders 
} from 'lucide-react';

export default function SettingsPage() {
  const riskWeights = [
    { rule: 'Duplicate Serial Number (Cross-Case / OEM Collision)', weight: 35, category: 'SERIAL_ASSET', severity: 'CRITICAL' },
    { rule: 'Image Perceptual Reuse (pHash Distance ≤ 10)', weight: 20, category: 'IMAGE_FORENSICS', severity: 'HIGH' },
    { rule: 'Deep Visual Similarity (Embedding Cosine Sim ≥ 0.85)', weight: 15, category: 'IMAGE_FORENSICS', severity: 'HIGH' },
    { rule: 'Invoice Price Variance (Exceeds Benchmark ±15%)', weight: 20, category: 'PRICE_BENCHMARK', severity: 'HIGH' },
    { rule: 'GPS EXIF Telemetry Mismatch (Distance ≥ 10 km)', weight: 12, category: 'GEO_TELEMETRY', severity: 'MEDIUM' },
    { rule: 'Required Evidence / Invoice Mismatch', weight: 8, category: 'DOCUMENT_INTEGRITY', severity: 'LOW' },
    { rule: 'Dealer Multi-Entity Correlation Overlap', weight: 0, category: 'RELATIONSHIP', severity: 'INFO (Zero Double-Count)' }
  ];

  const thresholds = [
    { name: 'pHash Hamming Distance Threshold', value: '≤ 10', description: 'Triggers perceptual image reuse anomaly' },
    { name: 'Embedding Cosine Similarity Threshold', value: '≥ 0.85', description: 'Triggers deep feature visual similarity flag' },
    { name: 'GPS Telemetry Variance Distance', value: '≥ 10.0 km', description: 'Triggers field verification requirement' },
    { name: 'Invoice Unit Rate Variance Tolerance', value: '± 15.0%', description: 'Triggers price inflation review' },
    { name: 'High Risk Threshold', value: '≥ 70 / 100', description: 'Requires mandatory physical field audit' },
    { name: 'Medium Risk Threshold', value: '40 – 69 / 100', description: 'Requires additional underwriter review' }
  ];

  return (
    <div className="space-y-6 max-w-[1600px] mx-auto pb-12">
      {/* Header */}
      <div className="rounded-2xl border border-[#E5E9F2] bg-white p-5 sm:p-6 shadow-xs flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <div className="h-7 w-7 rounded-lg bg-[#4F6EF7]/10 text-[#4F6EF7] flex items-center justify-center">
              <Settings className="h-4 w-4" />
            </div>
            <h1 className="text-xl font-extrabold text-[#182033]">
              Platform Configuration & Policy Rules
            </h1>
          </div>
          <p className="text-xs text-[#68738A] mt-1">
            Deterministic risk weights, verification engine thresholds, and webhook automation policies
          </p>
        </div>

        <div className="flex items-center gap-2 font-mono text-[10px] text-[#68738A] px-3 py-1.5 rounded-lg bg-[#F8FAFD] border border-[#E5E9F2]">
          <Sliders className="h-3.5 w-3.5 text-[#4F6EF7]" />
          <span>Policy: risk-v1 (Phase 6 Deterministic)</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Left: Risk Weights Policy Table (7 cols) */}
        <div className="lg:col-span-7 rounded-2xl border border-[#E5E9F2] bg-white p-5 shadow-xs space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-[#E5E9F2]">
            <div className="flex items-center gap-2">
              <Cpu className="h-4 w-4 text-[#4F6EF7]" />
              <h3 className="text-xs font-bold uppercase tracking-wider text-[#182033]">
                Phase 6 Risk Weight Configuration
              </h3>
            </div>
            <span className="text-[10px] text-[#8E99AD] font-mono">Max Group Cap = 25</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-[#E5E9F2] bg-[#F8FAFD] text-[10px] font-extrabold uppercase tracking-wider text-[#8E99AD]">
                  <th className="py-2.5 px-3">Rule Description</th>
                  <th className="py-2.5 px-3">Category</th>
                  <th className="py-2.5 px-3 text-right">Policy Weight</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#F1F4FA] text-xs">
                {riskWeights.map((r, i) => (
                  <tr key={i} className="hover:bg-[#F8FAFD] transition-colors">
                    <td className="py-3 px-3 font-medium text-[#182033]">
                      {r.rule}
                    </td>
                    <td className="py-3 px-3 font-mono text-[10px] text-[#68738A]">
                      {r.category}
                    </td>
                    <td className="py-3 px-3 text-right font-mono font-bold">
                      <span className={r.weight > 0 ? 'text-[#EF4444]' : 'text-[#8E99AD]'}>
                        +{r.weight}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right: Verification Thresholds & Webhooks (5 cols) */}
        <div className="lg:col-span-5 space-y-5">
          {/* Thresholds Card */}
          <div className="rounded-2xl border border-[#E5E9F2] bg-white p-5 shadow-xs space-y-3">
            <div className="flex items-center gap-2 pb-3 border-b border-[#E5E9F2]">
              <ShieldCheck className="h-4 w-4 text-[#10B981]" />
              <h3 className="text-xs font-bold uppercase tracking-wider text-[#182033]">
                Forensics & Price Thresholds
              </h3>
            </div>

            <div className="space-y-2 text-xs">
              {thresholds.map((t, idx) => (
                <div key={idx} className="p-2.5 rounded-xl border border-[#E5E9F2] bg-[#F8FAFD] flex items-center justify-between">
                  <div>
                    <div className="font-bold text-[#182033]">{t.name}</div>
                    <div className="text-[10px] text-[#68738A]">{t.description}</div>
                  </div>
                  <span className="font-mono font-bold text-xs text-[#4F6EF7] bg-white px-2 py-0.5 rounded border border-[#E5E9F2] shadow-2xs">
                    {t.value}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Webhook Security Card */}
          <div className="rounded-2xl border border-[#E5E9F2] bg-white p-5 shadow-xs space-y-3">
            <div className="flex items-center gap-2 pb-3 border-b border-[#E5E9F2]">
              <Lock className="h-4 w-4 text-[#5B4AEF]" />
              <h3 className="text-xs font-bold uppercase tracking-wider text-[#182033]">
                Phase 9 Webhook & Alert Security
              </h3>
            </div>

            <div className="space-y-1.5 text-xs text-[#68738A]">
              <div className="flex items-center justify-between">
                <span>HMAC Signature:</span>
                <span className="font-mono font-bold text-[#182033]">SHA-256 Enabled</span>
              </div>
              <div className="flex items-center justify-between">
                <span>Outbox Idempotency:</span>
                <span className="font-mono font-bold text-[#065F46]">Active</span>
              </div>
              <div className="flex items-center justify-between">
                <span>Retry Policy:</span>
                <span className="font-mono font-bold text-[#182033]">Bounded (5 Retries, Exp Backoff)</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
