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
  caseNumber: string;
  caseId: string;
  title: string;
  expectedScore: number;
  expectedBand: 'LOW' | 'MEDIUM' | 'HIGH';
  keyEvidence: string;
  icon: any;
  badgeColor: string;
}

const DEMO_SCENARIOS: ScenarioItem[] = [
  {
    id: 'clean',
    caseNumber: 'CAS-2026-001',
    caseId: '55555555-5555-5555-5555-555555555501',
    title: 'Scenario 1: Clean Verification',
    expectedScore: 0,
    expectedBand: 'LOW',
    keyEvidence: 'All OCR line items, serials, and installation GPS match expected benchmarks.',
    icon: ShieldCheck,
    badgeColor: 'bg-emerald-950/80 text-emerald-300 border-emerald-500/40'
  },
  {
    id: 'price',
    caseNumber: 'CAS-2026-002',
    caseId: '55555555-5555-5555-5555-555555555502',
    title: 'Scenario 2: Invoice Price Anomaly',
    expectedScore: 20,
    expectedBand: 'LOW',
    keyEvidence: 'Invoice unit price ₹55,000 exceeds regional benchmark average (+22.2%).',
    icon: DollarSign,
    badgeColor: 'bg-indigo-950/80 text-indigo-300 border-indigo-500/40'
  },
  {
    id: 'gps',
    caseNumber: 'CAS-2026-003',
    caseId: '55555555-5555-5555-5555-555555555503',
    title: 'Scenario 3: Installation GPS Mismatch',
    expectedScore: 12,
    expectedBand: 'LOW',
    keyEvidence: 'Installation photo geotag is 234.8 km from claimed farm site (>1.0 km limit).',
    icon: MapPin,
    badgeColor: 'bg-amber-950/80 text-amber-300 border-amber-500/40'
  },
  {
    id: 'image_reuse',
    caseNumber: 'CAS-2026-005',
    caseId: '55555555-5555-5555-5555-555555555505',
    title: 'Scenario 4: Visual Image Reuse',
    expectedScore: 25,
    expectedBand: 'LOW',
    keyEvidence: 'pHash exact match (dist 0) + ResNet embedding similarity 0.9945 (Capped at 25).',
    icon: Copy,
    badgeColor: 'bg-indigo-950/80 text-indigo-300 border-indigo-500/40'
  },
  {
    id: 'high_risk_stack',
    caseNumber: 'CAS-2026-007',
    caseId: '55555555-5555-5555-5555-555555555507',
    title: 'Scenario 5: Multiple Anomalies Stack',
    expectedScore: 92,
    expectedBand: 'HIGH',
    keyEvidence: 'Duplicate serial (35) + Price (+20) + GPS (+12) + Image reuse (25) -> Field Task & n8n Alert.',
    icon: AlertOctagon,
    badgeColor: 'bg-rose-950/80 text-rose-300 border-rose-500/40'
  }
];

export function DemoScenarioDrawer() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="relative">
      {/* Floating Demo Scenarios Trigger */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="inline-flex items-center gap-2 px-3.5 py-2 text-xs font-semibold rounded-lg bg-gradient-to-r from-indigo-600 to-cyan-600 text-white shadow-lg shadow-indigo-500/20 hover:from-indigo-500 hover:to-cyan-500 transition-all border border-indigo-400/30"
      >
        <Sparkles className="h-4 w-4 text-amber-300" />
        <span>Judge Demo Scenarios (1 - 5)</span>
      </button>

      {/* Slide-out Modal / Drawer */}
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="w-full max-w-2xl bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl p-6 space-y-5">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-lg bg-indigo-950/60 border border-indigo-500/30 text-indigo-400">
                  <Layers className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white">DIAVN Hackathon Demo Scenarios</h3>
                  <p className="text-xs text-slate-400">
                    Deterministic seed cases demonstrating end-to-end evidence evaluation and risk scoring.
                  </p>
                </div>
              </div>
              <button
                onClick={() => setIsOpen(false)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="space-y-3 max-h-[60vh] overflow-y-auto pr-1">
              {DEMO_SCENARIOS.map((scenario) => {
                const Icon = scenario.icon;
                return (
                  <Link
                    key={scenario.id}
                    href={`/cases/${scenario.caseNumber}`}
                    onClick={() => setIsOpen(false)}
                    className="block p-4 rounded-xl bg-slate-950/60 hover:bg-slate-800/60 border border-slate-800 hover:border-indigo-500/40 transition-all group"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-start gap-3">
                        <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-700/60 text-indigo-400 shrink-0 mt-0.5">
                          <Icon className="h-4 w-4" />
                        </div>
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-xs text-white group-hover:text-indigo-300 transition-colors">
                              {scenario.title}
                            </span>
                            <span className="font-mono text-[10px] text-slate-400">
                              ({scenario.caseNumber})
                            </span>
                          </div>
                          <p className="text-xs text-slate-400 leading-relaxed">
                            {scenario.keyEvidence}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center gap-2 shrink-0">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold border uppercase ${scenario.badgeColor}`}>
                          Score: {scenario.expectedScore} ({scenario.expectedBand})
                        </span>
                        <ChevronRight className="h-4 w-4 text-slate-500 group-hover:text-indigo-400 group-hover:translate-x-0.5 transition-all" />
                      </div>
                    </div>
                  </Link>
                );
              })}
            </div>

            <div className="pt-3 border-t border-slate-800 text-[11px] text-slate-500 flex items-start gap-2">
              <Info className="h-4 w-4 text-slate-400 shrink-0 mt-0.5" />
              <p className="leading-relaxed">
                All scenarios invoke the actual DIAVN deterministic engine. Synthetic seed data is clearly labeled and does not contain live borrower or lender records.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
