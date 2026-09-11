'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  ShieldCheck, 
  LayoutDashboard, 
  Building2, 
  FileText, 
  Camera, 
  Network, 
  Bell, 
  CheckSquare, 
  FolderCheck,
  Settings,
  Menu,
  X
} from 'lucide-react';

export const Sidebar: React.FC = () => {
  const pathname = usePathname();
  const [isMobileOpen, setIsMobileOpen] = useState(false);

  const navigationGroups = [
    {
      title: 'OVERVIEW',
      items: [
        { label: 'Dashboard', href: '/dashboard', icon: LayoutDashboard }
      ]
    },
    {
      title: 'OPERATIONS',
      items: [
        { label: 'Cases Queue', href: '/cases', icon: FolderCheck },
        { label: 'Verification Tasks', href: '/tasks', icon: CheckSquare },
        { label: 'Alerts', href: '/alerts', icon: Bell }
      ]
    },
    {
      title: 'INTELLIGENCE',
      items: [
        { label: 'Dealers', href: '/dealers', icon: Building2 },
        { label: 'Invoices', href: '/invoices', icon: FileText },
        { label: 'Image Forensics', href: '/forensics', icon: Camera },
        { label: 'Relationships', href: '/relationships', icon: Network }
      ]
    },
    {
      title: 'SYSTEM',
      items: [
        { label: 'Settings', href: '/settings', icon: Settings }
      ]
    }
  ];

  const isItemActive = (href: string) => {
    if (href === '/dashboard') {
      return pathname === '/dashboard' || pathname === '/';
    }
    if (href === '/cases') {
      return pathname === '/cases' || pathname.startsWith('/cases/new') || (pathname.startsWith('/cases/') && !['CAS-2026-001', 'CAS-2026-003', 'CAS-2026-007'].includes(pathname.split('/')[2]));
    }
    return pathname === href || pathname.startsWith(href);
  };

  const navContent = (
    <div className="flex flex-col h-full justify-between p-4 bg-white border-r border-[#E5E9F2]">
      {/* Brand & Navigation */}
      <div className="space-y-6">
        {/* Brand Header */}
        <Link href="/dashboard" className="flex items-center gap-3 px-2 py-1 group">
          <div className="h-9 w-9 rounded-xl bg-[#4F6EF7] flex items-center justify-center text-white shadow-xs group-hover:bg-[#3E5DE6] transition-colors shrink-0">
            <ShieldCheck className="h-5 w-5 stroke-[2.2]" />
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-1.5">
              <span className="font-extrabold text-base tracking-tight text-[#182033]">
                DIAVN
              </span>
              <span className="text-[9px] font-bold tracking-wider uppercase px-1.5 py-0.5 rounded bg-[#4F6EF7]/10 text-[#4F6EF7]">
                OS
              </span>
            </div>
            <p className="text-[10px] font-medium text-[#68738A] truncate">
              Dealer & Asset Verification
            </p>
          </div>
        </Link>

        {/* Categorized Navigation Groups */}
        <div className="space-y-4">
          {navigationGroups.map((group) => (
            <div key={group.title} className="space-y-1">
              <div className="px-2.5 pb-1 text-[9px] font-extrabold uppercase tracking-wider text-[#8E99AD]">
                {group.title}
              </div>
              {group.items.map((item) => {
                const Icon = item.icon;
                const active = isItemActive(item.href);
                return (
                  <Link
                    key={item.label}
                    href={item.href}
                    onClick={() => setIsMobileOpen(false)}
                    className={`flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-xs font-semibold transition-all ${
                      active
                        ? 'bg-[#4F6EF7]/10 text-[#4F6EF7] font-bold border-l-2 border-[#4F6EF7]'
                        : 'text-[#68738A] hover:text-[#182033] hover:bg-[#F8FAFD]'
                    }`}
                  >
                    <Icon className={`h-4 w-4 shrink-0 ${active ? 'text-[#4F6EF7]' : 'text-[#8E99AD]'}`} />
                    <span className="truncate">{item.label}</span>
                  </Link>
                );
              })}
            </div>
          ))}
        </div>
      </div>

      {/* Bottom User Card & Sandbox Indicator */}
      <div className="space-y-3 pt-3 border-t border-[#E5E9F2]">
        <div className="px-2.5 py-1.5 rounded-lg bg-[#F8FAFD] border border-[#E5E9F2] text-[10px] font-mono text-[#68738A] flex items-center justify-between">
          <span>SANDBOX MODE</span>
          <span className="h-1.5 w-1.5 rounded-full bg-[#10B981]" />
        </div>

        <div className="flex items-center gap-2.5 p-2 rounded-xl bg-[#F8FAFD] border border-[#E5E9F2]">
          <div className="h-7 w-7 rounded-lg bg-[#182033] text-white flex items-center justify-center font-bold text-[10px] shrink-0">
            UW
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-xs font-bold text-[#182033] truncate">Risk Officer</div>
            <div className="text-[10px] text-[#68738A] truncate">EquipLend Risk Ops</div>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <>
      {/* Mobile Top Header */}
      <div className="lg:hidden flex items-center justify-between p-3.5 bg-white border-b border-[#E5E9F2] sticky top-0 z-40">
        <Link href="/dashboard" className="flex items-center gap-2">
          <div className="h-7 w-7 rounded-lg bg-[#4F6EF7] flex items-center justify-center text-white">
            <ShieldCheck className="h-4 w-4" />
          </div>
          <span className="font-extrabold text-sm text-[#182033]">DIAVN</span>
        </Link>
        <button
          onClick={() => setIsMobileOpen(!isMobileOpen)}
          className="p-1.5 rounded-lg text-[#68738A] hover:bg-[#F8FAFD] border border-[#E5E9F2]"
          aria-label="Toggle Menu"
        >
          {isMobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>

      {/* Mobile Drawer */}
      {isMobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden flex">
          <div 
            className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs" 
            onClick={() => setIsMobileOpen(false)} 
          />
          <div className="relative w-64 max-w-[80vw] h-full shadow-2xl z-10">
            {navContent}
          </div>
        </div>
      )}

      {/* Desktop Persistent Sidebar (230px wide) */}
      <aside className="hidden lg:block w-56 shrink-0 h-screen sticky top-0">
        {navContent}
      </aside>
    </>
  );
};
