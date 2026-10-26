"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Shield, Plane, AlertTriangle, Layers, PlayCircle, Terminal, Activity } from "lucide-react";

export function Navbar() {
  const pathname = usePathname();

  const navItems = [
    { href: "/", label: "Operations Dashboard", icon: Activity },
    { href: "/incidents", label: "Incidents", icon: AlertTriangle },
    { href: "/scenarios", label: "Scenario Replay", icon: PlayCircle },
  ];

  return (
    <header className="sticky top-0 z-50 border-b border-surfaceBorder bg-background/95 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center space-x-3">
            <Link href="/" className="flex items-center space-x-2 group">
              <div className="w-9 h-9 rounded-lg bg-blue-500/10 border border-blue-500/30 flex items-center justify-center text-accent-blue group-hover:border-blue-400 transition-colors">
                <Plane className="w-5 h-5" />
              </div>
              <div className="flex flex-col">
                <span className="font-bold text-base tracking-tight text-white flex items-center gap-1.5">
                  FleetOps <span className="text-accent-blue font-extrabold">AI</span>
                </span>
                <span className="text-[10px] uppercase font-mono text-slate-400 tracking-wider">
                  Autonomous Drone Safety
                </span>
              </div>
            </Link>

            <nav className="hidden md:flex ml-8 space-x-1">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = pathname === item.href;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`flex items-center px-3.5 py-2 text-sm font-medium rounded-md transition-all ${
                      isActive
                        ? "bg-surface text-accent-blue border border-surfaceBorder"
                        : "text-slate-300 hover:text-white hover:bg-surface/50"
                    }`}
                  >
                    <Icon className="w-4 h-4 mr-2" />
                    {item.label}
                  </Link>
                );
              })}
            </nav>
          </div>

          <div className="flex items-center space-x-3">
            <div className="hidden sm:flex items-center space-x-2 text-xs font-mono px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span>SAFETY GATE: ARMED</span>
            </div>
            <div className="text-xs font-mono text-slate-400 border border-surfaceBorder bg-surface px-2.5 py-1 rounded">
              SIMULATOR MODE
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
