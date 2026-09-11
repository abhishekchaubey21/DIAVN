'use client';

import React from 'react';
import Link from 'next/link';
import { Case, ScoreComponentItem } from '@/types';
import { 
  ShieldAlert, 
  CheckCircle2, 
  AlertTriangle, 
  ArrowUpRight, 
  Activity, 
  Layers,
  Sparkles,
  Info
} from 'lucide-react';

interface RiskGaugeMeterProps {
  spotlightCase: Case | null;
  riskScore: number;
  riskBand: 'LOW' | 'MEDIUM' | 'HIGH';
  recommendedAction: string;
  summaryReasoning: string;
  policyVersion?: string;
  isLiveEngine?: boolean;
  components?: ScoreComponentItem[];
}

export function RiskGaugeMeter({
  spotlightCase,
  riskScore = 0,
  riskBand = 'LOW',
  recommendedAction = 'No immediate additional verification indicated by the configured DIAVN rules.',
  summaryReasoning,
  policyVersion = 'risk-v1',
  isLiveEngine = true,
  components = []
}: RiskGaugeMeterProps) {
  // Radial Gauge Calculations
  const clampedScore = Math.max(0, Math.min(100, riskScore));
  const radius = 80;
  const strokeWidth = 14;
  const circumference = Math.PI * radius; // Half-circle circumference
  const strokeDashoffset = circumference - (clampedScore / 100) * circumference;

  // Needle angle from -90deg (at 0 score) to +90deg (at 100 score)
  const needleAngle = -90 + (clampedScore / 100) * 180;

  const isHigh = riskBand === 'HIGH' || clampedScore >= 70;
  const isMed = riskBand === 'MEDIUM' || (clampedScore >= 40 && clampedScore < 70);

  const theme = isHigh
    ? {
        border: 'border-[#FECACA]',
        bg: 'bg-white',
        text: 'text-[#991B1B]',
        badgeBg: 'bg-[#FEF2F2]',
        badgeBorder: 'border-[#FECACA]',
        badgeText: 'text-[#991B1B]',
        arcColor: '#EF4444',
        btnBg: 'bg-[#991B1B] hover:bg-[#7F1D1D]'
      }
    : isMed
    ? {
        border: 'border-[#FDE68A]',
        bg: 'bg-white',
        text: 'text-[#92400E]',
        badgeBg: 'bg-[#FFFBEB]',
        badgeBorder: 'border-[#FDE68A]',
        badgeText: 'text-[#92400E]',
        arcColor: '#F59E0B',
        btnBg: 'bg-[#92400E] hover:bg-[#78350F]'
      }
    : {
        border: 'border-[#A7F3D0]',
        bg: 'bg-white',
        text: 'text-[#065F46]',
        badgeBg: 'bg-[#ECFDF5]',
        badgeBorder: 'border-[#A7F3D0]',
        badgeText: 'text-[#065F46]',
        arcColor: '#10B981',
        btnBg: 'bg-[#065F46] hover:bg-[#044E37]'
      };

  return (
    <div className={`rounded-2xl border ${theme.border} bg-white p-6 shadow-xs flex flex-col justify-between space-y-5`}>
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-[#E5E9F2]">
        <div className="flex items-center gap-2">
          <div className={`h-8 w-8 rounded-xl ${theme.badgeBg} ${theme.text} flex items-center justify-center`}>
            <Activity className="h-4 w-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-xs font-bold uppercase tracking-wider text-[#182033]">
                Verification Risk Engine
              </h3>
              <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-slate-100 text-[#68738A]">
                {policyVersion}
              </span>
            </div>
            <span className="text-[11px] text-[#68738A]">
              {isLiveEngine ? (
                <span className="text-emerald-700 font-semibold">● Phase 6 Authoritative Assessment</span>
              ) : (
                <span className="text-amber-700 font-semibold">● Sandbox / Benchmark Fixture</span>
              )}
            </span>
          </div>
        </div>

        <span className={`px-2.5 py-1 rounded-full text-[10px] font-extrabold uppercase tracking-wider border ${theme.badgeBg} ${theme.badgeBorder} ${theme.badgeText}`}>
          {riskBand} RISK BAND
        </span>
      </div>

      {/* Semi-Circular Radial Arc Gauge */}
      <div className="flex flex-col items-center justify-center py-2 relative">
        <div className="relative w-[210px] h-[115px]">
          <svg viewBox="0 0 200 110" className="w-full h-full overflow-visible">
            <defs>
              <linearGradient id="gaugeTrackGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#10B981" />
                <stop offset="40%" stopColor="#F59E0B" />
                <stop offset="70%" stopColor="#EF4444" />
              </linearGradient>
            </defs>

            {/* Background Arc Track (0 - 100) */}
            <path
              d="M 20 100 A 80 80 0 0 1 180 100"
              fill="none"
              stroke="#F1F4FA"
              strokeWidth={strokeWidth}
              strokeLinecap="round"
            />

            {/* Active Colored Score Arc */}
            <path
              d="M 20 100 A 80 80 0 0 1 180 100"
              fill="none"
              stroke="url(#gaugeTrackGrad)"
              strokeWidth={strokeWidth}
              strokeDasharray={circumference}
              strokeDashoffset={strokeDashoffset}
              strokeLinecap="round"
              className="transition-all duration-700 ease-out"
            />

            {/* Pointer / Needle Hub */}
            <circle cx="100" cy="100" r="7" fill="#182033" />
            <circle cx="100" cy="100" r="3" fill="#FFFFFF" />

            {/* Pointer / Needle Indicator Line */}
            <g transform={`rotate(${needleAngle}, 100, 100)`} className="transition-transform duration-700 ease-out">
              <line
                x1="100"
                y1="100"
                x2="100"
                y2="34"
                stroke="#182033"
                strokeWidth="3.5"
                strokeLinecap="round"
              />
            </g>

            {/* Scale Tick Labels */}
            <text x="16" y="110" fontSize="9" fill="#8E99AD" fontFamily="monospace" fontWeight="bold">0</text>
            <text x="96" y="15" fontSize="9" fill="#8E99AD" fontFamily="monospace" fontWeight="bold">50</text>
            <text x="172" y="110" fontSize="9" fill="#8E99AD" fontFamily="monospace" fontWeight="bold">100</text>
          </svg>
        </div>

        {/* Center Score Readout */}
        <div className="text-center mt-1">
          <div className="text-4xl font-extrabold font-mono tracking-tight text-[#182033] leading-none">
            {clampedScore} <span className="text-base font-normal text-[#8E99AD]">/ 100</span>
          </div>
          <p className="text-[11px] font-bold text-[#68738A] uppercase tracking-wider mt-1">
            Deterministic Composite Score
          </p>
        </div>
      </div>

      {/* Spotlight Case Header */}
      {spotlightCase && (
        <div className="p-3.5 bg-[#F8FAFD] rounded-xl border border-[#E5E9F2] space-y-1.5 text-xs">
          <div className="flex items-center justify-between">
            <span className="font-mono font-bold text-[#182033] text-sm">
              {spotlightCase.case_number}
            </span>
            <span className="text-[11px] font-semibold text-[#4F6EF7]">
              ₹{spotlightCase.loan_amount.toLocaleString('en-IN')}
            </span>
          </div>
          <div className="text-[#68738A] flex items-center justify-between text-[11px]">
            <span>Dealer: <strong className="text-[#182033]">{spotlightCase.dealer_name || spotlightCase.dealer_id}</strong></span>
            <span>Asset: <strong className="text-[#182033]">{spotlightCase.asset_type}</strong></span>
          </div>
        </div>
      )}

      {/* Active Signal Contributions Breakdown */}
      <div className="space-y-2">
        <span className="text-[10px] font-bold uppercase tracking-wider text-[#8E99AD] block">
          Contributing Verification Signals ({components.length})
        </span>

        {components.length === 0 ? (
          <div className="p-2.5 bg-[#F8FAFD] rounded-lg border border-[#E5E9F2] text-center text-[11px] text-[#68738A]">
            ✓ Zero active anomaly signals. No policy risk weights applied.
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs font-mono">
            {components.map((comp, idx) => (
              <div
                key={idx}
                className="p-2 bg-white rounded-lg border border-[#E5E9F2] flex items-center justify-between gap-1 shadow-2xs"
              >
                <div className="flex items-center gap-1.5 overflow-hidden">
                  <span className="h-1.5 w-1.5 rounded-full bg-[#EF4444] shrink-0" />
                  <span className="text-[11px] text-[#182033] truncate" title={comp.description}>
                    {comp.signal_type.replace(/_/g, ' ')}
                  </span>
                </div>
                <span className="text-[11px] font-bold text-[#EF4444] shrink-0">
                  +{comp.effective_contribution}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Prescribed Action & CTA */}
      <div className="space-y-3 pt-1">
        <div className={`p-3 rounded-xl border flex items-start gap-2 text-xs ${isHigh ? 'bg-[#FEF2F2] border-[#FECACA] text-[#991B1B]' : isMed ? 'bg-[#FFFBEB] border-[#FDE68A] text-[#92400E]' : 'bg-[#ECFDF5] border-[#A7F3D0] text-[#065F46]'}`}>
          {isHigh ? <ShieldAlert className="h-4 w-4 shrink-0 mt-0.5" /> : <CheckCircle2 className="h-4 w-4 shrink-0 mt-0.5" />}
          <div>
            <strong className="block font-bold">Policy-Prescribed Action:</strong>
            <p className="text-[11px] leading-relaxed mt-0.5">{recommendedAction}</p>
          </div>
        </div>

        {spotlightCase && (
          <Link
            href={`/cases/${spotlightCase.id}`}
            className={`w-full py-2.5 px-4 rounded-xl text-white text-xs font-bold flex items-center justify-center gap-1.5 shadow-xs transition-colors ${theme.btnBg}`}
          >
            <span>Review Full Case Inspection</span>
            <ArrowUpRight className="h-4 w-4" />
          </Link>
        )}
      </div>

      {/* Underwriting Disclaimer */}
      <div className="pt-2 border-t border-[#E5E9F2] text-[10px] text-[#8E99AD] flex items-start gap-1.5">
        <Info className="h-3.5 w-3.5 shrink-0 mt-0.5 text-[#68738A]" />
        <p className="leading-relaxed">
          DIAVN risk score represents deterministic evidence inconsistency under Phase 6 rules. Zero statistical fraud probability claims.
        </p>
      </div>
    </div>
  );
}
