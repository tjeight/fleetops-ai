import React from "react";
import { IncidentStatus, IncidentSeverity, PolicyOutcome } from "@/lib/types";

export function StatusBadge({ status }: { status: IncidentStatus | string }) {
  const styles: Record<string, string> = {
    OPEN: "bg-blue-500/10 text-blue-400 border-blue-500/30",
    INVESTIGATING: "bg-purple-500/10 text-purple-400 border-purple-500/30 animate-pulse",
    AWAITING_APPROVAL: "bg-amber-500/10 text-amber-400 border-amber-500/30",
    RESOLVED: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
    BLOCKED: "bg-rose-500/10 text-rose-400 border-rose-500/30",
    ERROR: "bg-red-500/10 text-red-400 border-red-500/30",
  };

  const style = styles[status] || "bg-slate-500/10 text-slate-400 border-slate-500/30";

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-mono font-medium border ${style}`}
    >
      {status.replace(/_/g, " ")}
    </span>
  );
}

export function SeverityBadge({ severity }: { severity: IncidentSeverity | string }) {
  const styles: Record<string, string> = {
    LOW: "bg-slate-500/10 text-slate-400 border-slate-500/30",
    MEDIUM: "bg-amber-500/10 text-amber-400 border-amber-500/30",
    HIGH: "bg-orange-500/10 text-orange-400 border-orange-500/30",
    CRITICAL: "bg-rose-500/20 text-rose-400 border-rose-500/40 font-bold",
  };

  const style = styles[severity] || styles.LOW;

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-mono border ${style}`}
    >
      {severity}
    </span>
  );
}

export function PolicyPill({ outcome }: { outcome: PolicyOutcome | string }) {
  const styles: Record<string, { bg: string; text: string; border: string }> = {
    ALLOW: { bg: "bg-emerald-500/10", text: "text-emerald-400", border: "border-emerald-500/30" },
    BLOCK: { bg: "bg-rose-500/10", text: "text-rose-400", border: "border-rose-500/30" },
    REQUIRES_APPROVAL: { bg: "bg-amber-500/10", text: "text-amber-400", border: "border-amber-500/30" },
    INSUFFICIENT_EVIDENCE: { bg: "bg-purple-500/10", text: "text-purple-400", border: "border-purple-500/30" },
  };

  const item = styles[outcome] || { bg: "bg-slate-500/10", text: "text-slate-400", border: "border-slate-500/30" };

  return (
    <span
      className={`inline-flex items-center px-2.5 py-1 rounded text-xs font-mono font-bold tracking-wide border ${item.bg} ${item.text} ${item.border}`}
    >
      GATE: {outcome.replace(/_/g, " ")}
    </span>
  );
}
