import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { Navbar } from '@/components/Navbar';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'DIAVN - Dealer Integrity & Asset Verification Network',
  description: 'Enterprise Lender Verification & Equipment Integrity OS',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} bg-slate-950 text-slate-100 min-h-screen antialiased flex flex-col`}>
        {/* Hackathon MVP / Synthetic Benchmark Mode Banner */}
        <div className="bg-gradient-to-r from-amber-500/10 via-sky-500/10 to-indigo-500/10 border-b border-amber-500/20 px-4 py-1.5 text-xs text-slate-300 flex items-center justify-between">
          <div className="flex items-center gap-2 max-w-7xl mx-auto w-full">
            <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-400 font-semibold text-[10px] tracking-wide uppercase">
              Sandbox Mode
            </span>
            <span>DIAVN Verification Sandbox — Security Hardened Hackathon MVP (Synthetic Benchmark Data)</span>
          </div>
        </div>
        <Navbar />
        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {children}
        </main>
        <footer className="border-t border-slate-800/80 bg-slate-950/60 py-6 text-center text-xs text-slate-500">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-2">
            <span>DIAVN Verification Platform • Phase 10 Hardened MVP</span>
            <span>Deterministic Underwriting & Integrity Verification</span>
          </div>
        </footer>
      </body>
    </html>
  );
}
