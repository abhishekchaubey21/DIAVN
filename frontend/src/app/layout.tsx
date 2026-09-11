import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { Sidebar } from '@/components/Sidebar';
import { TopBar } from '@/components/TopBar';

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
    <html lang="en">
      <body className={`${inter.className} bg-[#F6F8FC] text-[#182033] min-h-screen antialiased flex flex-col lg:flex-row`}>
        {/* Persistent Enterprise Sidebar */}
        <Sidebar />

        {/* Main Content Area */}
        <div className="flex-1 flex flex-col min-w-0">
          {/* Persistent Top Navigation Bar */}
          <TopBar />

          {/* Page Body */}
          <main className="flex-1 max-w-[1600px] w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
            {children}
          </main>

          {/* Minimal Enterprise Footer */}
          <footer className="border-t border-[#E5E9F2] bg-white py-4 text-xs text-[#8E99AD]">
            <div className="max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <span className="font-bold text-[#182033]">DIAVN Platform</span>
                <span>•</span>
                <span>Deterministic Underwriting & Asset Integrity</span>
              </div>
              <div className="flex items-center gap-3 font-mono text-[11px]">
                <span>Phase 10 Hardened MVP</span>
                <span>•</span>
                <span className="text-[#B45309] font-bold">Sandbox Mode</span>
              </div>
            </div>
          </footer>
        </div>
      </body>
    </html>
  );
}
