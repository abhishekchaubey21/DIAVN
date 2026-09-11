export type DataMode = 'live' | 'demo';

export interface DataModeState {
  mode: DataMode;
  label: string;
  badgeText: string;
  description: string;
  isSynthetic: boolean;
}

export const DATA_MODES: Record<DataMode, DataModeState> = {
  live: {
    mode: 'live',
    label: 'LIVE DATABASE',
    badgeText: 'LIVE DATABASE • Supabase',
    description: 'Direct production pipeline connection to active loan cases in database.',
    isSynthetic: false
  },
  demo: {
    mode: 'demo',
    label: 'DEMO DATASET',
    badgeText: 'DEMO DATASET • Synthetic Benchmark',
    description: 'Pre-seeded multi-stage fraud scenarios and verified equipment cases (CAS-2026-001 to CAS-2026-010).',
    isSynthetic: true
  }
};
