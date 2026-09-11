'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  Bell,
  PlusCircle,
  Sparkles,
  Activity,
  ChevronRight,
  ShieldCheck
} from 'lucide-react';
import { DemoScenarioDrawer } from './DemoScenarioDrawer';

export const TopBar: React.FC = () => {
  const pathname = usePathname();

  const getBreadcrumbs = () => {
    if (pathname === '/' || pathname === '/dashboard') {
      return { section: 'Intelligence OS', page: 'Underwriting Overview' };
    }
    if (pathname === '/cases') {
      return { section: 'Underwriting', page: 'Verification Queue' };
    }
    if (pathname === '/cases/new') {
      return { section: 'Underwriting', page: 'Submit New Case' };
    }
    if (pathname.startsWith('/cases/')) {
      const id = pathname.split('/')[2];
      return { section: 'Case Inspection', page: id || 'Detail' };
    }
    if (pathname === '/dealers') {
      return { section: 'Entity Intelligence', page: 'Dealer Registry' };
    }
    if (pathname.startsWith('/dealers/')) {
      const id = pathname.split('/')[2];
      return { section: 'Dealer Audit', page: id || 'Profile' };
    }
    return { section: 'DIAVN', page: 'Platform' };
  };

  const { section, page } = getBreadcrumbs();

  return (
    <header className="h-16 border-b border-[#E5E9F2] bg-white px-6 sm:px-8 flex items-center justify-between sticky top-0 z-30 shadow-xs">
      {/* Breadcrumb / Page Title */}
      <div className="flex items-center gap-2 text-xs">
        <span className="font-semibold text-[#8E99AD]">{section}</span>
        <ChevronRight className="h-3.5 w-3.5 text-[#8E99AD]" />
        <span className="font-bold text-[#182033]">{page}</span>
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-3">
        {/* Sandbox Status Pill */}
        <div className="hidden md:flex items-center gap-2 px-2.5 py-1 rounded-full bg-[#F6F8FC] border border-[#E5E9F2] text-[11px] font-medium text-[#68738A]">
          <span className="h-2 w-2 rounded-full bg-[#10B981]" />
          <span>Deterministic Node</span>
          <span className="text-[#8E99AD]">|</span>
          <span className="text-[#B45309] font-bold text-[10px] uppercase tracking-wider">Sandbox</span>
        </div>

        {/* Demo Scenario Drawer Component */}
        <DemoScenarioDrawer />

        {/* New Verification Action */}
        <Link
          href="/cases/new"
          className="hidden sm:inline-flex items-center gap-2 bg-[#4F6EF7] hover:bg-[#3E5DE6] text-white text-xs font-semibold px-3.5 py-2 rounded-xl shadow-xs transition-colors"
        >
          <PlusCircle className="h-4 w-4" />
          <span>New Case</span>
        </Link>
      </div>
    </header>
  );
};
