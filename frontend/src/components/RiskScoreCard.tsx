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
    summary_reasoning: caseScenarioId === 'CAS-2026-007'
      ? 'Deterministic verification assessment (risk-v1): Overall score 92/100 [HIGH]. Active risk contributions: +35 Duplicate Serial, +20 Invoice Price Anomaly, +12 Gps Mismatch, +25 Image Reuse (capped from +35). Action: Field verification recommended.'
      : caseScenarioId === 'CAS-2026-005'
        ? 'Deterministic verification assessment (risk-v1): Overall score 25/100 [LOW]. Active risk contributions: +25 Image Reuse (pHash +20, Embedding +15 capped to 25). Action: Additional document/evidence review recommended.'
        : 'No active verification anomalies detected under policy risk-v1. Baseline evidence-based verification risk is LOW (0/100). Action: No immediate additional verification indicated by the configured DIAVN rules.',
    components: caseScenarioId === 'CAS-2026-007' ? [
      {
        signal_type: 'DUPLICATE_SERIAL',
        group: 'SERIAL',
        source: 'invoice_verification',
        severity: 'critical',
        policy_weight: 35,
        effective_contribution: 35,
        is_group_capped: false,
        description: 'Serial number MIC-2025-0019 already registered in case CAS-2026-001.',
        evidence: { serial_number: 'MIC-2025-0019', registered_case_id: 'CAS-2026-001' }
      },
      {
        signal_type: 'INVOICE_PRICE_ANOMALY',
        group: 'INVOICE_PRICE',
        source: 'invoice_verification',
        severity: 'medium',
        policy_weight: 20,
        effective_contribution: 20,
        is_group_capped: false,
        description: 'Invoice unit price exceeds benchmark model average by 26.0%.',
        evidence: { variance_pct: 26.0, benchmark_avg: 27000 }
      },
      {
        signal_type: 'IMAGE_PHASH_REUSE',
        group: 'IMAGE_REUSE',
        source: 'image_forensics',
        severity: 'high',
        policy_weight: 20,
        effective_contribution: 20,
        is_group_capped: true,
        group_cap_applied: 25,
        description: 'Exact perceptual image match detected with case CAS-2026-001.',
        evidence: { hamming_distance: 0, matching_case_id: 'CAS-2026-001' }
      },
      {
        signal_type: 'IMAGE_EMBEDDING_SIMILARITY',
        group: 'IMAGE_REUSE',
        source: 'deep_visual_embeddings',
        severity: 'high',
        policy_weight: 15,
        effective_contribution: 5,
        is_group_capped: true,
        group_cap_applied: 25,
        description: 'Deep visual feature similarity 0.9850 detected with case CAS-2026-001 (capped to remaining group budget).',
        evidence: { cosine_similarity: 0.9850, matching_case_id: 'CAS-2026-001' }
      },
      {
        signal_type: 'GPS_MISMATCH',
        group: 'LOCATION',
        source: 'image_forensics',
        severity: 'high',
        policy_weight: 12,
        effective_contribution: 12,
        is_group_capped: false,
        description: 'Installation photo GPS distance 45.2 km exceeds allowed threshold 1.0 km.',
        evidence: { distance_km: 45.2, threshold_km: 1.0 }
      }
    ] : [],
    calculated_at: new Date().toISOString()
  };

  const handleRecalculate = async () => {
    setLoading(true);
    try {
      const res = await calculateCaseRiskScore(caseId, 'risk-v1');
      if (res) {
        setScore(res);
      }
    } catch (err) {
      console.error('Error calculating risk score:', err);
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (value: number) => {
    if (value >= 70) return 'text-rose-400 bg-rose-950/50 border-rose-500/50 shadow-rose-950/50';
    if (value >= 40) return 'text-amber-400 bg-amber-950/50 border-amber-500/50 shadow-amber-950/50';
    return 'text-emerald-400 bg-emerald-950/50 border-emerald-500/50 shadow-emerald-950/50';
  };

  const getBandBadge = (band: string) => {
    switch (band) {
      case 'HIGH':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold font-mono text-rose-300 bg-rose-950/80 border border-rose-500/50 shadow animate-pulse">
            <AlertTriangle className="h-3.5 w-3.5 text-rose-400" />
            HIGH RISK (70–100)
          </span>
        );
      case 'MEDIUM':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold font-mono text-amber-300 bg-amber-950/80 border border-amber-500/50 shadow">
            <AlertTriangle className="h-3.5 w-3.5 text-amber-400" />
            MEDIUM RISK (40–69)
          </span>
        );
      case 'LOW':
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold font-mono text-emerald-300 bg-emerald-950/80 border border-emerald-500/50 shadow">
            <ShieldCheck className="h-3.5 w-3.5 text-emerald-400" />
            LOW RISK (0–39)
          </span>
        );
    }
  };

  const riskBand = currentScore.risk_band || (currentScore.overall_score >= 70 ? 'HIGH' : currentScore.overall_score >= 40 ? 'MEDIUM' : 'LOW');
  const components = currentScore.components || [];

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-6 shadow-xl shadow-black/40 backdrop-blur-md space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <Activity className="h-5 w-5 text-indigo-400" />
            <h3 className="text-lg font-bold text-slate-100">Explainable Deterministic Risk Assessment</h3>
            <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-indigo-300">
              {currentScore.policy_version || 'risk-v1'}
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Traceable evidence aggregation • Anti-double-counting group caps • 100% server-side deterministic
          </p>
        </div>

        <div className="flex items-center gap-3">
          {getBandBadge(riskBand)}
          <button
            onClick={handleRecalculate}
            disabled={loading}
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 text-white text-xs font-semibold shadow-md transition-colors"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>{loading ? 'Evaluating...' : 'Recalculate Score'}</span>
          </button>
        </div>
      </div>

      {/* Recommended Underwriting Action Banner */}
      <div className={`p-4 rounded-lg border text-xs flex items-start justify-between gap-3 ${
        riskBand === 'HIGH'
          ? 'bg-rose-950/30 border-rose-500/40 text-rose-200'
          : riskBand === 'MEDIUM'
            ? 'bg-amber-950/30 border-amber-500/40 text-amber-200'
            : 'bg-emerald-950/30 border-emerald-500/40 text-emerald-200'
      }`}>
        <div className="flex items-start gap-2.5">
          <Info className="h-4 w-4 shrink-0 mt-0.5" />
          <div>
            <span className="font-bold uppercase tracking-wider block font-mono text-[11px]">
              Recommended Underwriting Action:
            </span>
            <span className="text-sm font-semibold mt-0.5 block">
              {currentScore.recommended_action || 'No immediate additional verification indicated by the configured DIAVN rules.'}
            </span>
          </div>
        </div>
        <span className="text-[10px] font-mono uppercase text-slate-400 shrink-0 hidden sm:inline">
          Workflow Directive
        </span>
      </div>

      {/* Main Score & Multi-Category Gauges */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-6 items-center">
        {/* Main Composite Score Dial */}
        <div className="md:col-span-2 flex flex-col items-center justify-center p-5 rounded-lg border border-slate-800/80 bg-slate-950/70 shadow-inner">
          <div className={`w-32 h-32 rounded-full border-4 flex flex-col items-center justify-center shadow-lg transition-all ${getScoreColor(currentScore.overall_score)}`}>
            <span className="text-4xl font-extrabold tracking-tight font-mono">{currentScore.overall_score}</span>
            <span className="text-[10px] uppercase font-bold tracking-widest text-slate-400">/ 100 Index</span>
          </div>
          <div className="mt-3 text-center space-y-0.5">
            <span className="text-xs font-bold font-mono text-slate-200">
              {riskBand} RISK BAND
            </span>
            {currentScore.raw_score !== undefined && currentScore.raw_score > currentScore.overall_score && (
              <span className="text-[11px] text-slate-400 font-mono block">
                Raw: +{currentScore.raw_score} (Capped to {currentScore.overall_score})
              </span>
            )}
          </div>
        </div>

        {/* Subcategory Signal Bars */}
        <div className="md:col-span-3 space-y-3">
          <div>
            <div className="flex justify-between text-xs font-medium mb-1">
              <span className="flex items-center gap-1.5 text-slate-300">
                <Database className="h-3.5 w-3.5 text-blue-400" />
                Price Benchmark Variance
              </span>
              <span className="font-mono text-slate-200">{currentScore.price_anomaly_score}%</span>
            </div>
            <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
              <div
                className={`h-full transition-all duration-500 ${currentScore.price_anomaly_score > 60 ? 'bg-rose-500' : currentScore.price_anomaly_score > 30 ? 'bg-amber-500' : 'bg-emerald-500'}`}
                style={{ width: `${Math.min(currentScore.price_anomaly_score, 100)}%` }}
              />
            </div>
          </div>

          <div>
            <div className="flex justify-between text-xs font-medium mb-1">
              <span className="flex items-center gap-1.5 text-slate-300">
                <Hash className="h-3.5 w-3.5 text-purple-400" />
                Serial Number Duplication
              </span>
              <span className="font-mono text-slate-200">{currentScore.serial_anomaly_score}%</span>
            </div>
            <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
              <div
                className={`h-full transition-all duration-500 ${currentScore.serial_anomaly_score > 60 ? 'bg-rose-500' : currentScore.serial_anomaly_score > 30 ? 'bg-amber-500' : 'bg-emerald-500'}`}
                style={{ width: `${Math.min(currentScore.serial_anomaly_score, 100)}%` }}
              />
            </div>
          </div>

          <div>
            <div className="flex justify-between text-xs font-medium mb-1">
              <span className="flex items-center gap-1.5 text-slate-300">
                <Camera className="h-3.5 w-3.5 text-amber-400" />
                Image Forensics & Visual Reuse
              </span>
              <span className="font-mono text-slate-200">{currentScore.image_anomaly_score}%</span>
            </div>
            <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
              <div
                className={`h-full transition-all duration-500 ${currentScore.image_anomaly_score > 60 ? 'bg-rose-500' : currentScore.image_anomaly_score > 30 ? 'bg-amber-500' : 'bg-emerald-500'}`}
                style={{ width: `${Math.min(currentScore.image_anomaly_score, 100)}%` }}
              />
            </div>
          </div>

          <div>
            <div className="flex justify-between text-xs font-medium mb-1">
              <span className="flex items-center gap-1.5 text-slate-300">
                <Network className="h-3.5 w-3.5 text-cyan-400" />
                Dealer Relationship & Collusion
              </span>
              <span className="font-mono text-slate-200">{currentScore.dealer_network_score}%</span>
            </div>
            <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
              <div
                className={`h-full transition-all duration-500 ${currentScore.dealer_network_score > 60 ? 'bg-rose-500' : currentScore.dealer_network_score > 30 ? 'bg-amber-500' : 'bg-emerald-500'}`}
                style={{ width: `${Math.min(currentScore.dealer_network_score, 100)}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Explainable Traceable Breakdown Section */}
      <div className="space-y-3 pt-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Layers className="h-4 w-4 text-indigo-400" />
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200">
              Traceable Score Breakdown by Active Risk Signal
            </h4>
          </div>
          <span className="text-[11px] font-mono text-slate-400">
            {components.length} Active Contributing Anomalies
          </span>
        </div>

        {components.length === 0 ? (
          <div className="p-4 bg-slate-950/60 rounded-lg border border-slate-800 text-xs text-slate-400 text-center">
            ✓ Zero active anomalies detected. No policy risk contributions applied.
          </div>
        ) : (
          <div className="space-y-2">
            {components.map((comp, idx) => {
              const isExpanded = expandedIndex === idx;
              return (
                <div
                  key={idx}
                  className={`rounded-lg border transition-all ${
                    comp.severity === 'critical' || comp.severity === 'high'
                      ? 'border-rose-500/40 bg-rose-950/20'
                      : 'border-slate-800 bg-slate-950/50'
                  }`}
                >
                  <div
                    onClick={() => setExpandedIndex(isExpanded ? null : idx)}
                    className="p-3 flex items-center justify-between cursor-pointer select-none"
                  >
                    <div className="flex items-center gap-3">
                      <span className="font-mono font-bold text-xs px-2 py-0.5 rounded bg-indigo-950/80 border border-indigo-500/40 text-indigo-300">
                        +{comp.effective_contribution}
                      </span>
                      <div>
                        <div className="flex items-center gap-2">
                          <h5 className="text-xs font-bold text-slate-200 font-mono">
                            {comp.signal_type.replace('_', ' ')}
                          </h5>
                          <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-slate-800 text-slate-400">
                            {comp.group}
                          </span>
                          {comp.is_group_capped && (
                            <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-amber-950/80 text-amber-300 border border-amber-500/40">
                              Capped from +{comp.policy_weight} (Group Cap: {comp.group_cap_applied})
                            </span>
                          )}
                        </div>
                        <p className="text-[11px] text-slate-400 mt-0.5 line-clamp-1">
                          {comp.description}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <span className="text-[10px] uppercase font-mono text-slate-500 hidden sm:inline">
                        {comp.source}
                      </span>
                      {isExpanded ? (
                        <ChevronUp className="h-4 w-4 text-slate-400" />
                      ) : (
                        <ChevronDown className="h-4 w-4 text-slate-400" />
                      )}
                    </div>
                  </div>

                  {isExpanded && (
                    <div className="px-3 pb-3 pt-1 border-t border-slate-800/80 space-y-2 text-xs">
                      <div className="text-slate-300">{comp.description}</div>
                      {comp.evidence && Object.keys(comp.evidence).length > 0 && (
                        <div>
                          <span className="text-[10px] uppercase font-semibold text-slate-400 block font-mono mb-1">
                            Traceable Underlying Evidence:
                          </span>
                          <pre className="bg-slate-950 p-2.5 rounded border border-slate-800 font-mono text-[11px] text-slate-300 overflow-x-auto whitespace-pre-wrap">
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

      {/* Summary Reasoning Text Box */}
      <div className="rounded-lg border border-slate-800/80 bg-slate-950/60 p-4 space-y-1.5">
        <div className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
          <Activity className="h-3.5 w-3.5 text-indigo-400" />
          Deterministic Risk Synthesis
        </div>
        <p className="text-xs text-slate-300 leading-relaxed font-normal">
          {currentScore.summary_reasoning}
        </p>
      </div>

      {/* Mandatory Underwriting Disclaimers */}
      <div className="p-3 bg-slate-950/80 rounded-lg border border-slate-800 text-[11px] text-slate-400 space-y-1">
        <div className="flex items-start gap-2">
          <Info className="h-4 w-4 shrink-0 text-slate-500 mt-0.5" />
          <div>
            <span className="font-semibold text-slate-300">Underwriting Standards & Compliance Notice:</span> The DIAVN risk score is an explainable policy-based verification risk score, not a statistical probability of fraud. Risk weights and group caps are policy assumptions designed for risk-based workflow routing and do not constitute legal proof of fraud.
          </div>
        </div>
      </div>
    </div>
  );
};
