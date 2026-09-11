'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { 
  Sparkles, 
  ShieldCheck, 
  DollarSign, 
  MapPin, 
  Copy, 
  AlertOctagon, 
  ChevronRight, 
  X,
  Info,
  Layers
} from 'lucide-react';

interface ScenarioItem {
  id: string;
  stepNumber: string;
  caseNumber: string;
  caseId: string;
  title: string;
  category: string;
  expectedScore: number;
  expectedBand: 'LOW' | 'MEDIUM' | 'HIGH';
  keyEvidence: string;
  icon: any;
}

const DEMO_SCENARIOS: ScenarioItem[] = [
  {
    id: 'clean',
    stepNumber: '01',
    caseNumber: 'CAS-2026-001',
    caseId: '55555555-5555-5555-5555-555555555501',
    title: 'Clean Equipment Baseline',
    category: 'Clean Case',
    expectedScore: 0,
    expectedBand: 'LOW',
    keyEvidence: 'All OCR invoice line items, serial numbers, and installation GPS match market benchmarks perfectly.',
    icon: ShieldCheck,
  },
  {
    id: 'price',
    stepNumber: '02',
    caseNumber: 'CAS-2026-002',
    caseId: '55555555-5555-5555-5555-555555555502',
    title: 'Invoice Unit Price Variance',
    category: 'Price Anomaly',
    expectedScore: 20,
    expectedBand: 'LOW',
    keyEvidence: 'Invoice unit price ₹55,000 exceeds regional benchmark average (+22.2% variance > 15% tolerance).',
    icon: DollarSign,
  },
  {
    id: 'gps',
    stepNumber: '03',
    caseNumber: 'CAS-2026-003',
    caseId: '55555555-5555-5555-5555-555555555503',
    title: 'Installation Site Geofence Mismatch',
    category: 'GPS Mismatch',
    expectedScore: 12,
    expectedBand: 'LOW',
    keyEvidence: 'Installation photo EXIF geotag is 234.8 km from claimed installation farm address (>1.0 km threshold).',
    icon: MapPin,
  },
  {
    id: 'image_reuse',
    stepNumber: '04',
    caseNumber: 'CAS-2026-005',
    caseId: '55555555-5555-5555-5555-555555555505',
    title: 'Cross-Case Image Duplication',
    category: 'Image Reuse',
    expectedScore: 25,
    expectedBand: 'LOW',
    keyEvidence: 'Perceptual pHash exact match (dist 0) and ResNet embedding similarity 0.9945 against existing case.',
    icon: Copy,
  },
  {
    id: 'high_risk_stack',
    stepNumber: '05',
    caseNumber: 'CAS-2026-007',
    caseId: '55555555-5555-5555-5555-555555555507',
    title: 'Multi-Anomaly High-Risk Stack',
    category: 'Multi-Anomaly Stack',
    expectedScore: 92,
    expectedBand: 'HIGH',
    keyEvidence: 'Duplicate serial (35) + Price (+20) + GPS (+12) + Image reuse (25) -> Triggers Field Audit & n8n Alert.',
    icon: AlertOctagon,
  }
];

export function DemoScenarioDrawer() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="relative">
      {/* Demo Scenario Trigger Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="inline-flex items-center gap-2 px-3.5 py-2 text-xs font-semibold rounded-xl bg-white hover:bg-[#F6F8FC] text-[#182033] border border-[#E5E9F2] shadow-xs transition-colors group"
      >
        <Sparkles className="h-4 w-4 text-[#4F6EF7] group-hover:scale-110 transition-transform" />
        <span>Judge Demo Scenarios (1–5)</span>
      </button>

      {/* Modal / Drawer Overlay */}
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-slate-900/50 backdrop-blur-xs animate-in fade-in duration-150">
          <div className="w-full max-w-2xl bg-white border border-[#E5E9F2] rounded-2xl shadow-2xl p-6 sm:p-7 space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between border-b border-[#E5E9F2] pb-4">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-xl bg-[#4F6EF7]/10 border border-[#4F6EF7]/20 flex items-center justify-center text-[#4F6EF7]">
                  <Layers className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-[#182033]">DIAVN Demo Scenarios</h3>
                  <p className="text-xs text-[#68738A]">
                    Deterministic seed cases demonstrating end-to-end evidence evaluation & risk scoring.
                  </p>
                </div>
              </div>
              <button
                onClick={() => setIsOpen(false)}
                className="p-1.5 rounded-lg text-[#8E99AD] hover:text-[#182033] hover:bg-[#F6F8FC] transition-colors"
                aria-label="Close"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Scenario List */}
            <div className="space-y-3 max-h-[60vh] overflow-y-auto pr-1">
              {DEMO_SCENARIOS.map((scenario) => {
                const Icon = scenario.icon;
                const isHigh = scenario.expectedBand === 'HIGH';
                const isMed = scenario.expectedBand === 'MEDIUM';

                const bandBadge = isHigh
                  ? 'bg-[#FEF2F2] text-[#991B1B] border-[#FECACA]'
                  : isMed
                  ? 'bg-[#FFFBEB] text-[#92400E] border-[#FDE68A]'
                  : 'bg-[#ECFDF5] text-[#065F46] border-[#A7F3D0]';

                return (
                  <Link
                    key={scenario.id}
                    href={`/cases/${scenario.caseNumber}`}
                    onClick={() => setIsOpen(false)}
                    className="block p-4 rounded-xl bg-[#F8FAFD] hover:bg-white border border-[#E5E9F2] hover:border-[#4F6EF7]/50 hover:shadow-xs transition-all group"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-start gap-3.5">
                        <div className="h-9 w-9 rounded-xl bg-white border border-[#E5E9F2] text-[#4F6EF7] flex items-center justify-center font-mono font-bold text-xs shrink-0 mt-0.5 shadow-2xs">
                          {scenario.stepNumber}
                        </div>
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-xs text-[#182033] group-hover:text-[#4F6EF7] transition-colors">
                              {scenario.title}
                            </span>
                            <span className="font-mono text-[11px] font-semibold text-[#8E99AD]">
                              [{scenario.caseNumber}]
                            </span>
                          </div>
                          <p className="text-xs text-[#68738A] leading-relaxed">
                            {scenario.keyEvidence}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center gap-2.5 shrink-0">
                        <span className={`px-2.5 py-1 rounded-lg text-[10px] font-bold border uppercase tracking-wider ${bandBadge}`}>
                          Score: {scenario.expectedScore} ({scenario.expectedBand})
                        </span>
                        <ChevronRight className="h-4 w-4 text-[#8E99AD] group-hover:text-[#4F6EF7] group-hover:translate-x-0.5 transition-all" />
                      </div>
                    </div>
                  </Link>
                );
              })}
            </div>

            {/* Footer Notice */}
            <div className="pt-3 border-t border-[#E5E9F2] text-[11px] text-[#68738A] flex items-start gap-2">
              <Info className="h-4 w-4 text-[#4F6EF7] shrink-0 mt-0.5" />
              <p className="leading-relaxed">
                Selecting a scenario executes the live verification pipeline on existing seeded records. Synthetic demonstration data only.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
