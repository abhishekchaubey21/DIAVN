'use client';

import React, { useState } from 'react';
import { RiskScore, ScoreComponentItem } from '@/types';
import { StatusBadge } from './StatusBadge';
import {
  AlertTriangle,
  ShieldCheck,
  Activity,
  Database,
  Camera,
  Network,
  Hash,
  RefreshCw,
  Layers,
  ChevronDown,
  ChevronUp,
  Info,
  CheckCircle2,
  Cpu,
  FileCheck
} from 'lucide-react';
import { calculateCaseRiskScore } from '@/lib/api';

interface RiskScoreCardProps {
  caseId: string;
  initialScore?: RiskScore | null;
  caseScenarioId?: string;
}

export const RiskScoreCard: React.FC<RiskScoreCardProps> = ({
  caseId,
  initialScore,
  caseScenarioId
}) => {
  const [score, setScore] = useState<RiskScore | null>(initialScore || null);
  const [loading, setLoading] = useState<boolean>(false);
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  // Fallback synthetic score calculation for demo if backend not yet queried
  const currentScore: RiskScore = score || {
    id: `RSK-${caseId}`,
    case_id: caseId,
    overall_score: caseScenarioId === 'CAS-2026-007' ? 92 : caseScenarioId === 'CAS-2026-005' ? 25 : caseScenarioId === 'CAS-2026-003' ? 12 : caseScenarioId === 'CAS-2026-002' ? 20 : 0,
    raw_score: caseScenarioId === 'CAS-2026-007' ? 102 : caseScenarioId === 'CAS-2026-005' ? 35 : caseScenarioId === 'CAS-2026-003' ? 12 : caseScenarioId === 'CAS-2026-002' ? 20 : 0,
    risk_level: caseScenarioId === 'CAS-2026-007' ? 'high' : 'low',
    risk_band: caseScenarioId === 'CAS-2026-007' ? 'HIGH' : 'LOW',
    policy_version: 'risk-v1',
    recommended_action: caseScenarioId === 'CAS-2026-007' ? 'Field verification recommended.' : caseScenarioId === 'CAS-2026-005' ? 'Additional document/evidence review recommended.' : 'No immediate additional verification indicated by the configured DIAVN rules.',
    price_anomaly_score: caseScenarioId === 'CAS-2026-002' || caseScenarioId === 'CAS-2026-007' ? 80 : 0,
    serial_anomaly_score: caseScenarioId === 'CAS-2026-007' ? 100 : 0,
    image_anomaly_score: caseScenarioId === 'CAS-2026-005' || caseScenarioId === 'CAS-2026-007' ? 100 : caseScenarioId === 'CAS-2026-003' ? 48 : 0,
    dealer_network_score: 0,
    calculated_at: new Date().toISOString(),
    summary_reasoning: caseScenarioId === 'CAS-2026-007'
      ? 'Deterministic verification assessment (risk-v1): Overall score 92/100 [HIGH]. Active risk contributions: +35 Duplicate Serial, +20 Invoice Price Anomaly, +12 Gps Mismatch, +25 Image Reuse (capped from +35). Action: Field verification recommended.'
      : caseScenarioId === 'CAS-2026-005'
        ? 'Deterministic verification assessment (risk-v1): Overall score 25/100 [LOW]. Active risk contributions: +25 Image Reuse (pHash +20, Embedding +15 capped to 25). Action: Additional document/evidence review recommended.'
        : 'No active verification anomalies detected under policy risk-v1. Baseline evidence-based verification risk is LOW (0/100). Action: No immediate additional verification indicated by the configured DIAVN rules.',
    components: caseScenarioId === 'CAS-2026-007' ? [
      {
        signal_type: 'DUPLICATE_SERIAL_NUMBER',
        group: 'SERIAL',
        source: 'SERIAL_ENGINE',
        severity: 'critical',
        policy_weight: 35,
        effective_contribution: 35,
        is_group_capped: false,
        group_cap_applied: undefined,
        description: 'Pump serial ASP-2025-99881 matches an active operational loan.',
        evidence: { duplicate_case_id: 'CAS-2026-001', matching_serial: 'ASP-2025-99881' }
      },
      {
        signal_type: 'INVOICE_PRICE_ANOMALY',
        group: 'PRICE',
        source: 'INVOICE_ENGINE',
        severity: 'high',
        policy_weight: 20,
        effective_contribution: 20,
        is_group_capped: false,
        group_cap_applied: undefined,
        description: 'Invoice unit price ₹75,000 exceeds regional market benchmark by +44.2%.',
        evidence: { invoiced_unit_price: 75000, category_avg_price: 52000, variance_pct: 44.2 }
      },
      {
        signal_type: 'GPS_MISMATCH',
        group: 'IMAGE',
        source: 'IMAGE_FORENSICS',
        severity: 'medium',
        policy_weight: 12,
        effective_contribution: 12,
        is_group_capped: false,
        group_cap_applied: undefined,
        description: 'Installation photo location (234.8 km) exceeds 1.0 km threshold from claimed address.',
        evidence: { distance_km: 234.8, threshold_km: 1.0 }
      },
      {
        signal_type: 'PHASH_EXACT_MATCH',
        group: 'IMAGE',
        source: 'IMAGE_FORENSICS',
        severity: 'high',
        policy_weight: 20,
        effective_contribution: 13,
        is_group_capped: true,
        group_cap_applied: 25,
        description: 'Perceptual pHash exact match (hamming distance 0) against existing case CAS-2026-001.',
        evidence: { matching_image_id: 'IMG-001', hamming_distance: 0 }
      },
      {
        signal_type: 'VISUAL_SIMILARITY_MATCH',
        group: 'IMAGE',
        source: 'IMAGE_EMBEDDINGS',
        severity: 'high',
        policy_weight: 15,
        effective_contribution: 12,
        is_group_capped: true,
        group_cap_applied: 25,
        description: 'ResNet-50 visual embedding cosine similarity 0.9945 matches prior installation photos.',
        evidence: { cosine_similarity: 0.9945, similarity_threshold: 0.90 }
      }
    ] : []
  };

  const handleRecalculate = async () => {
    setLoading(true);
    try {
      const res = await calculateCaseRiskScore(caseId);
      if (res) {
        setScore(res);
      }
    } catch (err) {
      console.warn('Backend recalculate failed:', err);
    } finally {
      setLoading(false);
    }
  };

  const isHigh = currentScore.risk_band === 'HIGH' || currentScore.overall_score >= 70;
  const isMed = currentScore.risk_band === 'MEDIUM' || (currentScore.overall_score >= 30 && currentScore.overall_score < 70);

  const heroTheme = isHigh
    ? {
        border: 'border-[#FECACA]',
        bg: 'bg-gradient-to-br from-[#FEF2F2] via-white to-white',
        scoreColor: 'text-[#991B1B]',
        badge: 'bg-[#FEF2F2] text-[#991B1B] border-[#FECACA]',
        bandText: 'HIGH RISK BAND'
      }
    : isMed
    ? {
        border: 'border-[#FDE68A]',
        bg: 'bg-gradient-to-br from-[#FFFBEB] via-white to-white',
        scoreColor: 'text-[#92400E]',
        badge: 'bg-[#FFFBEB] text-[#92400E] border-[#FDE68A]',
        bandText: 'MEDIUM RISK BAND'
      }
    : {
        border: 'border-[#A7F3D0]',
        bg: 'bg-gradient-to-br from-[#ECFDF5] via-white to-white',
        scoreColor: 'text-[#065F46]',
        badge: 'bg-[#ECFDF5] text-[#065F46] border-[#A7F3D0]',
        bandText: 'LOW RISK BAND'
      };

  const components: ScoreComponentItem[] = (currentScore as any).components || [];

  return (
    <div className="rounded-2xl border border-[#E5E9F2] bg-white p-6 sm:p-7 shadow-xs space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#E5E9F2] pb-5">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-[#4F6EF7]/10 border border-[#4F6EF7]/20 text-[#4F6EF7] flex items-center justify-center">
            <Cpu className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-[#182033]">
                Phase 6 Risk Scoring Engine
              </h3>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-md bg-[#F1F4FA] text-[#4F6EF7] border border-[#E5E9F2] font-bold">
                {currentScore.policy_version || 'risk-v1'}
              </span>
            </div>
            <p className="text-xs text-[#68738A]">
              Deterministic explainable risk assessment derived strictly from active signals.
            </p>
          </div>
        </div>

        <button
          onClick={handleRecalculate}
          disabled={loading}
          className="inline-flex items-center gap-1.5 px-3.5 py-2 text-xs font-bold rounded-xl bg-[#F8FAFD] hover:bg-[#4F6EF7] text-[#182033] hover:text-white border border-[#E5E9F2] hover:border-[#4F6EF7] transition-all disabled:opacity-50"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>{loading ? 'Evaluating...' : 'Re-Evaluate Risk'}</span>
        </button>
      </div>

      {/* Main Score & Action Hero */}
      <div className={`p-6 rounded-2xl border ${heroTheme.border} ${heroTheme.bg} space-y-4 shadow-xs`}>
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          {/* Score & Band */}
          <div className="flex items-center gap-5">
            <div className="text-center sm:text-left">
              <div className="text-4xl sm:text-5xl font-extrabold font-mono tracking-tight leading-none">
                <span className={heroTheme.scoreColor}>{currentScore.overall_score}</span>
                <span className="text-lg font-normal text-[#8E99AD]"> / 100</span>
              </div>
              <div className="text-[11px] font-bold uppercase tracking-wider text-[#8E99AD] mt-1">
                Composite Risk Score
              </div>
            </div>

            <div className="h-12 w-px bg-[#E5E9F2] hidden sm:block" />

            <div className="space-y-1">
              <span className={`inline-block px-3 py-1 rounded-lg text-xs font-extrabold border uppercase tracking-wider ${heroTheme.badge}`}>
                {heroTheme.bandText}
              </span>
              <div className="text-xs text-[#68738A] font-mono">
                Raw Score Sum: {currentScore.raw_score ?? currentScore.overall_score}
              </div>
            </div>
          </div>

          {/* Recommended Action Box */}
          <div className="p-4 rounded-xl bg-white border border-[#E5E9F2] md:max-w-md shadow-2xs">
            <span className="text-[10px] uppercase font-bold text-[#8E99AD] tracking-wider block mb-1">
              Policy-Prescribed Action
            </span>
            <div className="text-xs font-bold text-[#182033] leading-relaxed flex items-start gap-2">
              <CheckCircle2 className="h-4 w-4 text-[#4F6EF7] shrink-0 mt-0.5" />
              <span>{currentScore.recommended_action || 'Review active anomalies in accordance with lending policy.'}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Risk Category Distribution Progress Bars */}
      <div className="space-y-3">
        <h4 className="text-xs font-bold uppercase tracking-wider text-[#8E99AD]">
          Risk Category Dimensions
        </h4>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          <div className="p-3.5 rounded-xl bg-[#F8FAFD] border border-[#E5E9F2] space-y-2">
            <div className="flex justify-between text-xs">
              <span className="font-semibold text-[#182033] flex items-center gap-1.5">
                <Database className="h-3.5 w-3.5 text-[#4F6EF7]" />
                Invoice Pricing
              </span>
              <span className="font-mono font-bold text-[#182033]">{currentScore.price_anomaly_score}%</span>
            </div>
            <div className="h-1.5 w-full bg-[#E5E9F2] rounded-full overflow-hidden">
              <div
                className={`h-full transition-all ${currentScore.price_anomaly_score > 60 ? 'bg-[#EF4444]' : currentScore.price_anomaly_score > 30 ? 'bg-[#F59E0B]' : 'bg-[#10B981]'}`}
                style={{ width: `${Math.min(currentScore.price_anomaly_score, 100)}%` }}
              />
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-[#F8FAFD] border border-[#E5E9F2] space-y-2">
            <div className="flex justify-between text-xs">
              <span className="font-semibold text-[#182033] flex items-center gap-1.5">
                <Camera className="h-3.5 w-3.5 text-[#5B4AEF]" />
                Image Forensics
              </span>
              <span className="font-mono font-bold text-[#182033]">{currentScore.image_anomaly_score}%</span>
            </div>
            <div className="h-1.5 w-full bg-[#E5E9F2] rounded-full overflow-hidden">
              <div
                className={`h-full transition-all ${currentScore.image_anomaly_score > 60 ? 'bg-[#EF4444]' : currentScore.image_anomaly_score > 30 ? 'bg-[#F59E0B]' : 'bg-[#10B981]'}`}
                style={{ width: `${Math.min(currentScore.image_anomaly_score, 100)}%` }}
              />
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-[#F8FAFD] border border-[#E5E9F2] space-y-2">
            <div className="flex justify-between text-xs">
              <span className="font-semibold text-[#182033] flex items-center gap-1.5">
                <Hash className="h-3.5 w-3.5 text-[#F59E0B]" />
                Serial Registry
              </span>
              <span className="font-mono font-bold text-[#182033]">{currentScore.serial_anomaly_score}%</span>
            </div>
            <div className="h-1.5 w-full bg-[#E5E9F2] rounded-full overflow-hidden">
              <div
                className={`h-full transition-all ${currentScore.serial_anomaly_score > 60 ? 'bg-[#EF4444]' : currentScore.serial_anomaly_score > 30 ? 'bg-[#F59E0B]' : 'bg-[#10B981]'}`}
                style={{ width: `${Math.min(currentScore.serial_anomaly_score, 100)}%` }}
              />
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-[#F8FAFD] border border-[#E5E9F2] space-y-2">
            <div className="flex justify-between text-xs">
              <span className="font-semibold text-[#182033] flex items-center gap-1.5">
                <Network className="h-3.5 w-3.5 text-[#10B981]" />
                Dealer Links
              </span>
              <span className="font-mono font-bold text-[#182033]">{currentScore.dealer_network_score}%</span>
            </div>
            <div className="h-1.5 w-full bg-[#E5E9F2] rounded-full overflow-hidden">
              <div
                className={`h-full transition-all ${currentScore.dealer_network_score > 60 ? 'bg-[#EF4444]' : currentScore.dealer_network_score > 30 ? 'bg-[#F59E0B]' : 'bg-[#10B981]'}`}
                style={{ width: `${Math.min(currentScore.dealer_network_score, 100)}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Traceable Score Breakdown */}
      <div className="space-y-3 pt-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Layers className="h-4 w-4 text-[#4F6EF7]" />
            <h4 className="text-xs font-bold uppercase tracking-wider text-[#182033]">
              Traceable Score Breakdown by Active Risk Signal
            </h4>
          </div>
          <span className="text-[11px] font-mono text-[#8E99AD]">
            {components.length} Contributing Anomalies
          </span>
        </div>

        {components.length === 0 ? (
          <div className="p-4 bg-[#F8FAFD] rounded-xl border border-[#E5E9F2] text-xs text-[#68738A] text-center">
            ✓ Zero active anomalies detected. No policy risk weights applied.
          </div>
        ) : (
          <div className="space-y-2">
            {components.map((comp, idx) => {
              const isExpanded = expandedIndex === idx;
              return (
                <div
                  key={idx}
                  className="rounded-xl border border-[#E5E9F2] bg-white hover:border-[#D1D8E6] transition-all overflow-hidden"
                >
                  <div
                    onClick={() => setExpandedIndex(isExpanded ? null : idx)}
                    className="p-3.5 flex items-center justify-between cursor-pointer select-none hover:bg-[#F8FAFD]"
                  >
                    <div className="flex items-center gap-3">
                      <span className="font-mono font-bold text-xs px-2.5 py-1 rounded-lg bg-[#4F6EF7]/10 text-[#4F6EF7] border border-[#4F6EF7]/20">
                        +{comp.effective_contribution}
                      </span>
                      <div>
                        <div className="flex items-center gap-2">
                          <h5 className="text-xs font-bold text-[#182033] font-mono">
                            {comp.signal_type.replace('_', ' ')}
                          </h5>
                          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[#F1F4FA] text-[#68738A]">
                            {comp.group}
                          </span>
                          {comp.is_group_capped && (
                            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[#FFFBEB] text-[#92400E] border border-[#FDE68A]">
                              Capped (Cap: {comp.group_cap_applied})
                            </span>
                          )}
                        </div>
                        <p className="text-[11px] text-[#68738A] mt-0.5 line-clamp-1">
                          {comp.description}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <span className="text-[10px] uppercase font-mono text-[#8E99AD] hidden sm:inline">
                        {comp.source}
                      </span>
                      {isExpanded ? (
                        <ChevronUp className="h-4 w-4 text-[#8E99AD]" />
                      ) : (
                        <ChevronDown className="h-4 w-4 text-[#8E99AD]" />
                      )}
                    </div>
                  </div>

                  {isExpanded && (
                    <div className="px-4 pb-4 pt-2 border-t border-[#E5E9F2] bg-[#F8FAFD] space-y-2 text-xs">
                      <div className="text-[#182033] leading-relaxed">{comp.description}</div>
                      {comp.evidence && Object.keys(comp.evidence).length > 0 && (
                        <div>
                          <span className="text-[10px] uppercase font-bold text-[#8E99AD] block font-mono mb-1">
                            Traceable Underlying Evidence:
                          </span>
                          <pre className="bg-white p-3 rounded-xl border border-[#E5E9F2] font-mono text-[11px] text-[#182033] overflow-x-auto whitespace-pre-wrap">
                            {JSON.stringify(comp.evidence, null, 2)}
                          </pre>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Summary Reasoning */}
      <div className="rounded-xl border border-[#E5E9F2] bg-[#F8FAFD] p-4 space-y-1.5">
        <div className="text-xs font-bold text-[#182033] uppercase tracking-wider flex items-center gap-1.5">
          <Activity className="h-3.5 w-3.5 text-[#4F6EF7]" />
          <span>Deterministic Risk Synthesis</span>
        </div>
        <p className="text-xs text-[#68738A] leading-relaxed">
          {currentScore.summary_reasoning}
        </p>
      </div>

      {/* Underwriting Standards Notice */}
      <div className="p-3.5 bg-[#F6F8FC] rounded-xl border border-[#E5E9F2] text-[11px] text-[#8E99AD] space-y-1">
        <div className="flex items-start gap-2">
          <Info className="h-4 w-4 shrink-0 text-[#4F6EF7] mt-0.5" />
          <p className="leading-relaxed">
            <strong className="text-[#182033]">Underwriting Compliance Notice:</strong> DIAVN risk score is an explainable verification risk assessment calculated from deterministic policy weights. It does not constitute legal proof of fraud.
          </p>
        </div>
      </div>
    </div>
  );
};
