'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { ShieldCheck, LayoutDashboard, FileCheck2, Building2, PlusCircle, ExternalLink } from 'lucide-react';

export const Navbar: React.FC = () => {
  const pathname = usePathname();

  const navItems = [
    { label: 'Dashboard', href: '/dashboard', icon: <LayoutDashboard className="h-4 w-4" /> },
    { label: 'Cases Queue', href: '/cases', icon: <FileCheck2 className="h-4 w-4" /> },
    { label: 'Dealer Registry', href: '/dealers', icon: <Building2 className="h-4 w-4" /> },
  ];

  return (
    <header className="sticky top-0 z-50 w-full border-b border-slate-800 bg-slate-950/80 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center gap-6">
          <Link href="/dashboard" className="flex items-center gap-2.5 group">
            <div className="p-2 rounded-lg bg-indigo-600/20 border border-indigo-500/40 text-indigo-400 group-hover:bg-indigo-600/30 transition-all">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <div>
              <span className="text-base font-extrabold tracking-tight text-white flex items-center gap-1.5">
                DIAVN
                <span className="text-[10px] font-mono font-medium px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                  LENDER OS
                </span>
              </span>
              <p className="text-[10px] text-slate-400 leading-none">Dealer Integrity & Asset Verification</p>
            </div>
          </Link>

          {/* Nav Links */}
          <nav className="hidden md:flex items-center gap-1">
            {navItems.map((item) => {
              const isActive = pathname === item.href || (item.href !== '/dashboard' && pathname.startsWith(item.href));
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-semibold transition-all ${
                    isActive
                      ? 'bg-slate-800 text-white border border-slate-700 shadow-sm'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
                  }`}
                >
                  {item.icon}
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Action Button & Backend Health */}
        <div className="flex items-center gap-3">
          <Link
            href="/cases/new"
            className="inline-flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold px-3.5 py-2 rounded-lg shadow-lg shadow-indigo-600/20 transition-all border border-indigo-400/30"
          >
            <PlusCircle className="h-4 w-4" />
            <span>New Verification Case</span>
          </Link>
        </div>
      </div>
    </header>
  );
};
