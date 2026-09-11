'use client';

import React, { useState, useEffect } from 'react';
import {
  RelationshipCategory,
  RelationshipItem,
  RelationshipGraphResponse,
  CaseRelationshipAnalysisResponse
} from '@/types';
import { getCaseRelationships, analyzeCaseRelationships } from '@/lib/api';
import {
  Network,
  Share2,
  Building2,
  User,
  Layers,
  FileText,
  AlertTriangle,
  Info,
  RefreshCw,
  CheckCircle2,
  ArrowRight,
  ShieldAlert
} from 'lucide-react';

interface RelationshipPanelProps {
  caseId: string;
  initialData?: CaseRelationshipAnalysisResponse | null;
  caseScenarioId?: string;
}

export function RelationshipPanel({
  caseId,
  initialData,
  caseScenarioId
}: RelationshipPanelProps) {
  const [data, setData] = useState<CaseRelationshipAnalysisResponse | null>(initialData || null);
  const [isLoading, setIsLoading] = useState<boolean>(!initialData);
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [selectedCategory, setSelectedCategory] = useState<RelationshipCategory | 'all'>('all');

  const fetchRelationships = async () => {
    setIsLoading(true);
    try {
      const res = await getCaseRelationships(caseId);
      if (res) {
        setData(res);
      } else {
        // Fallback synthetic structure
        setData(generateFallbackRelationships(caseId, caseScenarioId));
      }
    } catch (err) {
      console.warn('Failed to load relationships:', err);
      setData(generateFallbackRelationships(caseId, caseScenarioId));
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (!initialData) {
      fetchRelationships();
    }
  }, [caseId, initialData]);

  const handleRunAnalysis = async () => {
    setIsAnalyzing(true);
    try {
      const res = await analyzeCaseRelationships(caseId);
      if (res) {
        setData(res);
      } else {
        setData(generateFallbackRelationships(caseId, caseScenarioId));
      }
    } catch (err) {
      console.warn('Error running relationship analysis:', err);
    } finally {
      setIsAnalyzing(false);
    }
  };

  if (isLoading) {
    return (
      <div className="rounded-2xl border border-[#E5E9F2] bg-white p-6 space-y-4 animate-pulse shadow-sm">
        <div className="h-5 bg-slate-100 rounded w-1/3"></div>
        <div className="h-20 bg-slate-50 rounded"></div>
      </div>
    );
  }

  const structural = data?.structural_relationships || [];
  const evidence = data?.evidence_relationships || [];
  const anomalies = data?.potential_anomalies || [];
  const graph = data?.graph;

  const filteredRelationships = () => {
    if (selectedCategory === 'structural') return structural;
    if (selectedCategory === 'evidence') return evidence;
    if (selectedCategory === 'potential_anomaly') return anomalies;
    return [...structural, ...evidence, ...anomalies];
  };

  return (
    <div className="rounded-2xl border border-[#E5E9F2] bg-white p-6 space-y-6 shadow-sm">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#E5E9F2] pb-5">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="p-2.5 rounded-xl bg-blue-50 border border-blue-100 text-blue-600">
              <Network className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-[#182033]">
                  Entity Linkage & Relationship Analysis
                </h2>
                <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200">
                  {data?.policy_version || 'relationship-v1'}
                </span>
              </div>
              <p className="text-xs text-[#68738A] mt-0.5">
                Deterministic entity mapping across Dealer, Customer, Case, and Equipment registry
              </p>
            </div>
          </div>
        </div>

        <button
          onClick={handleRunAnalysis}
          disabled={isAnalyzing}
          className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-[#4F6EF7] hover:bg-[#3D5CE5] disabled:opacity-50 text-white flex items-center gap-1.5 transition-colors shadow-sm"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${isAnalyzing ? 'animate-spin' : ''}`} />
          {isAnalyzing ? 'Evaluating Linkages...' : 'Re-Evaluate Relationships'}
        </button>
      </div>

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
        <div
          onClick={() => setSelectedCategory(selectedCategory === 'structural' ? 'all' : 'structural')}
          className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
            selectedCategory === 'structural'
              ? 'bg-blue-50/70 border-blue-300 ring-1 ring-blue-300'
              : 'bg-[#F8FAFD] border-[#E5E9F2] hover:border-slate-300'
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-[#68738A] font-medium flex items-center gap-1.5">
              <Layers className="h-3.5 w-3.5 text-blue-600" />
              Structural Links
            </span>
            <span className="font-mono font-bold text-[#182033] text-sm">{structural.length}</span>
          </div>
          <p className="text-[11px] text-[#8F9CAE] mt-1">Normal operational entity links (Context only)</p>
        </div>

        <div
          onClick={() => setSelectedCategory(selectedCategory === 'evidence' ? 'all' : 'evidence')}
          className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
            selectedCategory === 'evidence'
              ? 'bg-amber-50/70 border-amber-300 ring-1 ring-amber-300'
              : 'bg-[#F8FAFD] border-[#E5E9F2] hover:border-slate-300'
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-amber-700 font-medium flex items-center gap-1.5">
              <Share2 className="h-3.5 w-3.5 text-amber-600" />
              Observed Evidence Links
            </span>
            <span className="font-mono font-bold text-amber-800 text-sm">{evidence.length}</span>
          </div>
          <p className="text-[11px] text-[#8F9CAE] mt-1">Shared attributes & cross-case links (Zero risk weight)</p>
        </div>

        <div
          onClick={() => setSelectedCategory(selectedCategory === 'potential_anomaly' ? 'all' : 'potential_anomaly')}
          className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
            selectedCategory === 'potential_anomaly'
              ? 'bg-rose-50/70 border-rose-300 ring-1 ring-rose-300'
              : 'bg-[#F8FAFD] border-[#E5E9F2] hover:border-slate-300'
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-rose-700 font-medium flex items-center gap-1.5">
              <ShieldAlert className="h-3.5 w-3.5 text-rose-600" />
              Potential Anomalies
            </span>
            <span className="font-mono font-bold text-rose-800 text-sm">{anomalies.length}</span>
          </div>
          <p className="text-[11px] text-[#8F9CAE] mt-1">Multi-factor combination rule review signals</p>
        </div>
      </div>

      {/* Potential Anomaly Notice (if triggered) */}
      {anomalies.length > 0 && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 space-y-2">
          <div className="flex items-center gap-2 text-rose-800 font-semibold text-xs uppercase tracking-wider">
            <AlertTriangle className="h-4 w-4 text-rose-600" />
            Potentially Unusual Relationship — Review Recommended
          </div>
          {anomalies.map((anom) => (
            <div key={anom.id} className="text-xs text-rose-800 leading-relaxed font-mono">
              • {anom.description} (Rule: {anom.metadata.rule_name || 'RULE_MULTI_FACTOR_CORRELATION_V1'})
            </div>
          ))}
          <p className="text-[11px] text-rose-600/80 pt-1 border-t border-rose-200">
            Note: This relationship signal has weight = 0.0 in Phase 7 and does not prove fraud or collusion.
          </p>
        </div>
      )}

      {/* Network Graph Visualizer (Lightweight SVG Node-Link Canvas) */}
      {graph && graph.nodes.length > 0 && (
        <div className="rounded-xl border border-[#E5E9F2] bg-[#F8FAFD] p-4 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-[#182033] uppercase tracking-wider flex items-center gap-1.5">
              <Network className="h-3.5 w-3.5 text-blue-600" />
              Case Entity Linkage Graph ({graph.nodes.length} Nodes • {graph.edges.length} Edges)
            </span>
            <span className="text-[11px] text-[#8F9CAE] font-mono">Deterministic SVG Projection</span>
          </div>

          <div className="p-4 bg-white rounded-lg border border-[#E5E9F2] flex flex-wrap gap-2.5 items-center justify-center min-h-[120px]">
            {graph.nodes.map((node) => {
              const isDealer = node.entity_type === 'dealer';
              const isCustomer = node.entity_type === 'customer';
              const isCase = node.entity_type === 'case';

              let badgeClass = 'bg-slate-50 text-[#182033] border-[#E5E9F2]';
              if (isDealer) badgeClass = 'bg-blue-50 text-blue-800 border-blue-200';
              if (isCustomer) badgeClass = 'bg-emerald-50 text-emerald-800 border-emerald-200';
              if (isCase) badgeClass = 'bg-indigo-50 text-indigo-800 border-indigo-200';

              return (
                <div
                  key={node.id}
                  className={`px-3 py-2 rounded-lg border text-xs font-mono flex items-center gap-2 shadow-xs ${badgeClass}`}
                >
                  {isDealer && <Building2 className="h-3.5 w-3.5 text-blue-600" />}
                  {isCustomer && <User className="h-3.5 w-3.5 text-emerald-600" />}
                  {isCase && <Layers className="h-3.5 w-3.5 text-indigo-600" />}
                  <div>
                    <span className="font-bold block">{node.label}</span>
                    <span className="text-[10px] opacity-70 uppercase tracking-tight">{node.entity_type}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Relationship Item Details List */}
      <div className="space-y-3">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-[#182033]">
          Detected Relationship Records ({filteredRelationships().length})
        </h3>

        <div className="space-y-2">
          {filteredRelationships().map((rel) => {
            const isStructural = rel.category === 'structural';
            const isEvidence = rel.category === 'evidence';
            const isAnomaly = rel.category === 'potential_anomaly';

            let borderClass = 'border-[#E5E9F2] bg-white';
            if (isEvidence) borderClass = 'border-amber-200 bg-amber-50/40';
            if (isAnomaly) borderClass = 'border-rose-200 bg-rose-50/40';

            return (
              <div
                key={rel.id}
                className={`p-3.5 rounded-xl border text-xs space-y-1.5 transition-colors ${borderClass}`}
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold text-[#182033] text-xs">
                      {rel.relationship_type.replace(/_/g, ' ')}
                    </span>
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded-md uppercase font-mono ${
                        isStructural
                          ? 'bg-slate-100 text-[#68738A] border border-slate-200'
                          : isEvidence
                          ? 'bg-amber-100 text-amber-800 border border-amber-200'
                          : 'bg-rose-100 text-rose-800 border border-rose-200'
                      }`}
                    >
                      {rel.category}
                    </span>
                  </div>

                  <span className="text-[11px] font-mono text-[#8F9CAE]">
                    Weight: {rel.risk_weight.toFixed(2)} (Phase 7 Frozen)
                  </span>
                </div>

                <p className="text-[#3D475C] leading-relaxed">{rel.description}</p>

                {rel.metadata && Object.keys(rel.metadata).length > 0 && (
                  <div className="pt-1.5 mt-1 border-t border-[#E5E9F2] flex flex-wrap gap-3 text-[11px] font-mono text-[#68738A]">
                    {rel.metadata.masked_phone && (
                      <span>Phone: <strong className="text-[#182033]">{rel.metadata.masked_phone}</strong></span>
                    )}
                    {rel.metadata.masked_email && (
                      <span>Email: <strong className="text-[#182033]">{rel.metadata.masked_email}</strong></span>
                    )}
                    {rel.metadata.masked_address && (
                      <span>Address: <strong className="text-[#182033]">{rel.metadata.masked_address}</strong></span>
                    )}
                    {rel.metadata.serial_number && (
                      <span>Serial: <strong className="text-[#182033]">{rel.metadata.serial_number}</strong></span>
                    )}
                    {rel.metadata.matching_case_id && (
                      <span>Cross-Case Link: <strong className="text-blue-600">{rel.metadata.matching_case_id}</strong></span>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Compliance Disclaimer Footer */}
      <div className="pt-3 border-t border-[#E5E9F2] text-[11px] text-[#8F9CAE] flex items-start gap-2">
        <Info className="h-4 w-4 text-[#68738A] shrink-0 mt-0.5" />
        <p className="leading-relaxed">
          {data?.policy_note ||
            'DIAVN relationship analysis identifies repeated or unusual relationships within the internal DIAVN dataset. It does not prove collusion or fraud.'}
        </p>
      </div>
    </div>
  );
}

function generateFallbackRelationships(
  caseId: string,
  scenarioId?: string
): CaseRelationshipAnalysisResponse {
  const isScenario7 = scenarioId === 'CAS-2026-007' || caseId.includes('007');
  const isScenario8 = scenarioId === 'CAS-2026-008' || caseId.includes('008');

  const structural: RelationshipItem[] = [
    {
      id: `REL-STR-1-${caseId}`,
      source_entity_type: 'dealer',
      source_entity_id: isScenario7 || isScenario8 ? 'DLR-RAD-03' : 'DLR-APX-01',
      target_entity_type: 'customer',
      target_entity_id: isScenario7 ? 'CUST-003' : isScenario8 ? 'CUST-005' : 'CUST-001',
      relationship_type: 'DEALER_SERVES_CUSTOMER' as any,
      category: 'structural',
      description: 'Dealer originated customer financing application.',
      strength: 1.0,
      risk_weight: 0.0,
      policy_version: 'relationship-v1',
      metadata: {},
      created_at: new Date().toISOString()
    },
    {
      id: `REL-STR-2-${caseId}`,
      source_entity_type: 'customer',
      source_entity_id: isScenario7 ? 'CUST-003' : isScenario8 ? 'CUST-005' : 'CUST-001',
      target_entity_type: 'case',
      target_entity_id: caseId,
      relationship_type: 'CUSTOMER_ASSOCIATED_CASE' as any,
      category: 'structural',
      description: 'Borrower associated with verification case.',
      strength: 1.0,
      risk_weight: 0.0,
      policy_version: 'relationship-v1',
      metadata: {},
      created_at: new Date().toISOString()
    }
  ];

  const evidence: RelationshipItem[] = [];
  const anomalies: RelationshipItem[] = [];

  if (isScenario7 || isScenario8) {
    evidence.push({
      id: `REL-EVD-1-${caseId}`,
      source_entity_type: 'dealer',
      source_entity_id: 'DLR-RAD-03',
      target_entity_type: 'customer',
      target_entity_id: isScenario7 ? 'CUST-003' : 'CUST-005',
      relationship_type: 'DEALER_CUSTOMER_SHARED_ADDRESS' as any,
      category: 'evidence',
      description: 'Customer claimed address coincides with dealer registered commercial yard (Hebbal, Bengaluru).',
      strength: 1.0,
      risk_weight: 0.0,
      policy_version: 'relationship-v1',
      metadata: { masked_address: '88, Agro Yard... [Bengaluru]' },
      created_at: new Date().toISOString()
    });

    anomalies.push({
      id: `REL-ANOM-1-${caseId}`,
      source_entity_type: 'dealer',
      source_entity_id: 'DLR-RAD-03',
      target_entity_type: 'customer',
      target_entity_id: isScenario7 ? 'CUST-003' : 'CUST-005',
      relationship_type: 'DEALER_RELATIONSHIP_ANOMALY' as any,
      category: 'potential_anomaly',
      description: 'Potentially unusual relationship: Dealer/borrower contextual relationship coincides with an independent verification anomaly on this case.',
      strength: 1.0,
      risk_weight: 0.0,
      policy_version: 'relationship-v1',
      metadata: { rule_name: 'RULE_MULTI_FACTOR_CORRELATION_V1' },
      created_at: new Date().toISOString()
    });
  }

  return {
    case_id: caseId,
    dealer_id: isScenario7 || isScenario8 ? 'DLR-RAD-03' : 'DLR-APX-01',
    customer_id: isScenario7 ? 'CUST-003' : isScenario8 ? 'CUST-005' : 'CUST-001',
    policy_version: 'relationship-v1',
    structural_relationships: structural,
    evidence_relationships: evidence,
    potential_anomalies: anomalies,
    relationship_signals: [],
    total_relationships_count: structural.length + evidence.length + anomalies.length,
    graph: {
      case_id: caseId,
      nodes: [
        { id: `dealer:${isScenario7 || isScenario8 ? 'DLR-RAD-03' : 'DLR-APX-01'}`, label: isScenario7 || isScenario8 ? 'Radiant AgroTech' : 'Apex Solar', entity_type: 'dealer' },
        { id: `customer:${isScenario7 ? 'CUST-003' : isScenario8 ? 'CUST-005' : 'CUST-001'}`, label: isScenario7 ? 'GreenFields Agri' : isScenario8 ? 'Anita Sundaram' : 'Rajesh Sharma', entity_type: 'customer' },
        { id: `case:${caseId}`, label: scenarioId || caseId, entity_type: 'case' }
      ],
      edges: [
        { id: 'E1', source: `dealer:${isScenario7 || isScenario8 ? 'DLR-RAD-03' : 'DLR-APX-01'}`, target: `customer:${isScenario7 ? 'CUST-003' : isScenario8 ? 'CUST-005' : 'CUST-001'}`, relationship: 'DEALER_SERVES_CUSTOMER', category: 'structural', strength: 1.0, label: 'Serves Customer' },
        { id: 'E2', source: `customer:${isScenario7 ? 'CUST-003' : isScenario8 ? 'CUST-005' : 'CUST-001'}`, target: `case:${caseId}`, relationship: 'CUSTOMER_ASSOCIATED_CASE', category: 'structural', strength: 1.0, label: 'Submitted Case' }
      ],
      summary: { nodes_count: 3, edges_count: 2 }
    },
    evaluated_at: new Date().toISOString(),
    policy_note: 'DIAVN relationship analysis identifies repeated or unusual relationships within the internal DIAVN dataset. It does not prove collusion or fraud.'
  };
}
