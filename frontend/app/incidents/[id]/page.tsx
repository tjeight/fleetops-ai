"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  AlertTriangle,
  ArrowLeft,
  Shield,
  ShieldCheck,
  ShieldAlert,
  Clock,
  BookOpen,
  Cpu,
  Activity,
  CheckCircle2,
  XCircle,
  RefreshCw,
  Terminal,
  UserCheck,
  HelpCircle,
  Radio,
  FileText
} from "lucide-react";
import { api } from "@/lib/api";
import { Incident } from "@/lib/types";
import { StatusBadge, SeverityBadge, PolicyPill } from "@/components/StatusBadge";

export default function IncidentDetailPage() {
  const params = useParams();
  const incidentId = params.id as string;

  const [incident, setIncident] = useState<Incident | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Operator Approval Form State
  const [operatorRole, setOperatorRole] = useState<string>("demo_operator");
  const [rejectionReason, setRejectionReason] = useState<string>("");
  const [approvalError, setApprovalError] = useState<string | null>(null);

  const fetchIncident = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getIncident(incidentId);
      setIncident(data);
    } catch (err: any) {
      setError(err.message || "Failed to load incident.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (incidentId) {
      fetchIncident();
    }
  }, [incidentId]);

  const handleRunInvestigation = async (simulateTimeout = false) => {
    try {
      setActionLoading(true);
      const updated = await api.triggerInvestigation(incidentId, simulateTimeout);
      setIncident(updated);
    } catch (err: any) {
      alert(`Investigation failed: ${err.message}`);
    } finally {
      setActionLoading(false);
    }
  };

  const handleResolveApproval = async (decision: "APPROVE" | "REJECT") => {
    try {
      setActionLoading(true);
      setApprovalError(null);
      const updated = await api.resolveApproval(
        incidentId,
        decision,
        operatorRole,
        "operator-01",
        decision === "REJECT" ? (rejectionReason || "Operator rejected proposal") : undefined
      );
      setIncident(updated);
    } catch (err: any) {
      setApprovalError(err.message || "Failed to resolve approval.");
    } finally {
      setActionLoading(false);
    }
  };

  if (loading && !incident) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] space-y-3 font-mono text-xs text-slate-400">
        <RefreshCw className="w-8 h-8 animate-spin text-accent-blue" />
        <p>Loading incident telemetry and audit history...</p>
      </div>
    );
  }

  if (error || !incident) {
    return (
      <div className="space-y-4">
        <Link href="/incidents" className="text-xs text-accent-blue hover:underline flex items-center gap-1 font-mono">
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Incidents
        </Link>
        <div className="p-6 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-300">
          <h2 className="font-bold text-base">Error Loading Incident</h2>
          <p className="text-xs mt-1">{error || "Incident record not found."}</p>
        </div>
      </div>
    );
  }

  const investigation = incident.investigations?.[0];
  const policyDecision = incident.policy_decisions?.[0];
  const pendingApproval = incident.approval_requests?.find((a) => a.status === "PENDING");
  const telemetry = incident.telemetry_snapshot || {};
  const isStale = (incident.audit_events || []).some(
    (e) => e.event_type === "TELEMETRY_CHECKED" && e.payload?.is_stale
  );

  return (
    <div className="space-y-8">
      {/* Top Breadcrumb & Action Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-surfaceBorder pb-6">
        <div>
          <Link
            href="/incidents"
            className="text-xs text-slate-400 hover:text-white flex items-center gap-1 font-mono mb-2"
          >
            <ArrowLeft className="w-3.5 h-3.5" /> Return to Incidents
          </Link>
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-2xl font-mono font-bold text-white tracking-tight">
              {incident.id}
            </h1>
            <SeverityBadge severity={incident.severity} />
            <StatusBadge status={incident.status} />
            {policyDecision && <PolicyPill outcome={policyDecision.outcome} />}
          </div>
          <p className="text-xs text-slate-400 mt-1 font-mono">
            Site: <span className="text-slate-200">{incident.site_id}</span> • Drone:{" "}
            <span className="text-slate-200">{incident.drone_id}</span> • Event:{" "}
            <span className="text-accent-blue font-bold">{incident.event_type}</span>
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => handleRunInvestigation(false)}
            disabled={actionLoading}
            className="flex items-center text-xs font-mono px-4 py-2 bg-accent-blue hover:bg-sky-400 text-slate-950 font-bold rounded-md transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 mr-2 ${actionLoading ? "animate-spin" : ""}`} />
            Run LangGraph Investigation
          </button>
        </div>
      </div>

      {/* Staleness / Telemetry Alert Banner */}
      {isStale && (
        <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/40 text-amber-300 text-xs flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 flex-shrink-0 text-amber-400 mt-0.5" />
          <div>
            <span className="font-bold uppercase tracking-wider font-mono">Stale Telemetry Detected</span>
            <p className="mt-0.5 text-amber-200/90">
              Telemetry feed age exceeded 60.0s threshold. Autonomous flight commands are blocked; only telemetry refresh requests are permitted.
            </p>
          </div>
        </div>
      )}

      {/* Main Grid: 2-column layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column (2 spans): Investigation Findings & Citations */}
        <div className="lg:col-span-2 space-y-6">
          {/* Investigation Findings Card */}
          <div className="bg-surface border border-surfaceBorder rounded-xl p-5 space-y-5">
            <div className="flex items-center justify-between border-b border-surfaceBorder pb-3">
              <h2 className="text-sm font-bold text-white flex items-center gap-2 font-mono uppercase tracking-wide">
                <Cpu className="w-4 h-4 text-accent-blue" />
                Evidence-Backed Diagnosis
              </h2>
              {investigation && (
                <span className="text-[11px] font-mono text-purple-400 bg-purple-500/10 border border-purple-500/20 px-2 py-0.5 rounded">
                  {investigation.diagnosis_category}
                </span>
              )}
            </div>

            {investigation ? (
              <div className="space-y-4 text-xs">
                <div>
                  <span className="text-slate-400 uppercase font-mono text-[10px] tracking-wider block mb-1">
                    Primary Likely Cause
                  </span>
                  <div className="p-3 bg-background/60 border border-surfaceBorder rounded-lg font-mono text-slate-200 font-semibold text-sm">
                    {investigation.likely_cause}
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {/* Observed Facts */}
                  <div className="p-3 bg-background/40 border border-surfaceBorder rounded-lg space-y-2">
                    <span className="text-emerald-400 font-mono font-bold uppercase text-[10px] tracking-wider flex items-center gap-1.5">
                      <CheckCircle2 className="w-3.5 h-3.5" /> Observed Facts (Direct Data)
                    </span>
                    <ul className="list-disc list-inside space-y-1 text-slate-300">
                      {investigation.observed_facts?.map((fact, i) => (
                        <li key={i} className="leading-relaxed">
                          {fact}
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Hypotheses */}
                  <div className="p-3 bg-background/40 border border-surfaceBorder rounded-lg space-y-2">
                    <span className="text-purple-400 font-mono font-bold uppercase text-[10px] tracking-wider flex items-center gap-1.5">
                      <HelpCircle className="w-3.5 h-3.5" /> Diagnostic Hypotheses
                    </span>
                    <ul className="list-disc list-inside space-y-1 text-slate-300">
                      {investigation.hypotheses?.map((hyp, i) => (
                        <li key={i} className="leading-relaxed">
                          {hyp}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>

                {/* Uncertainty Notes */}
                {investigation.uncertainty_notes && (
                  <div className="p-3 bg-background/40 border border-surfaceBorder rounded-lg space-y-1">
                    <span className="text-amber-400 font-mono font-bold uppercase text-[10px] tracking-wider">
                      Uncertainty & Evidence Limitations
                    </span>
                    <p className="text-slate-300 leading-relaxed font-mono text-[11px]">
                      {investigation.uncertainty_notes}
                    </p>
                  </div>
                )}
              </div>
            ) : (
              <div className="p-6 text-center text-slate-400 font-mono text-xs">
                No investigation record exists yet. Click "Run LangGraph Investigation" above to analyze telemetry and SOPs.
              </div>
            )}
          </div>

          {/* SOP Document Retrieval & Citations Card */}
          <div className="bg-surface border border-surfaceBorder rounded-xl p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-surfaceBorder pb-3">
              <h2 className="text-sm font-bold text-white flex items-center gap-2 font-mono uppercase tracking-wide">
                <BookOpen className="w-4 h-4 text-accent-blue" />
                Retrieved Standard Operating Procedures (ChromaDB)
              </h2>
              <span className="text-[11px] font-mono text-slate-400">
                {investigation?.retrieved_sop_citations?.length ?? 0} CITATIONS
              </span>
            </div>

            {investigation?.retrieved_sop_citations && investigation.retrieved_sop_citations.length > 0 ? (
              <div className="space-y-3">
                {investigation.retrieved_sop_citations.map((c, i) => (
                  <div
                    key={i}
                    className="p-3.5 rounded-lg bg-background/50 border border-surfaceBorder space-y-2 text-xs"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <span className="font-mono font-bold text-accent-blue bg-blue-500/10 px-1.5 py-0.5 rounded text-[11px]">
                          {c.sop_id}
                        </span>
                        <span className="font-semibold text-slate-200">{c.title}</span>
                      </div>
                      <span className="font-mono text-[10px] text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded">
                        Sim: {(c.relevance_score * 100).toFixed(1)}%
                      </span>
                    </div>
                    {c.section && (
                      <span className="text-[10px] font-mono text-slate-400 block">
                        Section: {c.section}
                      </span>
                    )}
                    <p className="text-slate-300 font-serif italic bg-slate-950/60 p-2.5 rounded border border-surfaceBorder/80 text-[11px] leading-relaxed">
                      "{c.excerpt}"
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-6 text-center text-slate-400 font-mono text-xs">
                Zero matching SOP citations retrieved. (Scenario 4: Grounding check prevents hallucinatory guidance).
              </div>
            )}
          </div>

          {/* Chronological Audit Timeline Card */}
          <div className="bg-surface border border-surfaceBorder rounded-xl p-5 space-y-4">
            <h2 className="text-sm font-bold text-white flex items-center gap-2 font-mono uppercase tracking-wide border-b border-surfaceBorder pb-3">
              <Clock className="w-4 h-4 text-accent-blue" />
              Chronological Audit Trail (Append-Only)
            </h2>

            <div className="space-y-3">
              {incident.audit_events?.map((ev, i) => (
                <div
                  key={ev.id || i}
                  className="flex items-start space-x-3 p-3 rounded-lg bg-background/50 border border-surfaceBorder/80 text-xs"
                >
                  <div className="w-2 h-2 rounded-full bg-accent-blue mt-1.5 flex-shrink-0" />
                  <div className="flex-1 space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="font-mono font-bold text-white">{ev.event_type}</span>
                      <span className="text-[10px] font-mono text-slate-500">
                        {new Date(ev.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                    <div className="text-[11px] font-mono text-slate-400">
                      Actor: <span className="text-accent-blue">{ev.actor}</span>
                    </div>
                    <pre className="mt-1 p-2 bg-slate-950/80 rounded border border-surfaceBorder text-[10px] font-mono text-slate-300 overflow-x-auto">
                      {JSON.stringify(ev.payload, null, 2)}
                    </pre>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column (1 span): Safety Gate, Approval Interface, & Telemetry */}
        <div className="space-y-6">
          {/* Deterministic Safety Gate Decision */}
          <div className="bg-surface border border-surfaceBorder rounded-xl p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-surfaceBorder pb-3">
              <h2 className="text-sm font-bold text-white flex items-center gap-2 font-mono uppercase tracking-wide">
                <Shield className="w-4 h-4 text-emerald-400" />
                Safety Policy Gate
              </h2>
              {policyDecision && <PolicyPill outcome={policyDecision.outcome} />}
            </div>

            {policyDecision ? (
              <div className="space-y-3 text-xs">
                <div>
                  <span className="text-slate-400 font-mono text-[10px] uppercase">
                    Proposed Simulated Action
                  </span>
                  <div className="p-2 bg-background/70 border border-surfaceBorder rounded font-mono font-bold text-slate-200 mt-1">
                    {policyDecision.action_type}
                  </div>
                </div>

                <div>
                  <span className="text-slate-400 font-mono text-[10px] uppercase">Policy Reasons</span>
                  <ul className="list-disc list-inside mt-1 space-y-1 text-slate-300 text-[11px]">
                    {policyDecision.reasons?.map((r, i) => (
                      <li key={i}>{r}</li>
                    ))}
                  </ul>
                </div>

                {policyDecision.failed_checks?.length > 0 && (
                  <div className="p-2.5 rounded bg-rose-500/10 border border-rose-500/30 text-rose-300">
                    <span className="font-mono font-bold text-[10px] uppercase block mb-1">
                      Failed Safety Constraints:
                    </span>
                    <ul className="list-disc list-inside text-[11px]">
                      {policyDecision.failed_checks.map((fc, i) => (
                        <li key={i}>{fc}</li>
                      ))}
                    </ul>
                  </div>
                )}

                <div className="border-t border-surfaceBorder pt-2 text-[10px] font-mono text-slate-500">
                  Evaluated Policies: {policyDecision.policy_ids_evaluated?.join(", ")}
                </div>
              </div>
            ) : (
              <div className="p-4 text-center text-slate-500 font-mono text-xs">
                Awaiting investigation run.
              </div>
            )}
          </div>

          {/* Pending Approval Interface (Screen D) */}
          {pendingApproval && (
            <div className="bg-gradient-to-b from-amber-500/10 to-surface border border-amber-500/40 rounded-xl p-5 space-y-4">
              <div className="flex items-center space-x-2 text-amber-400 font-mono text-xs font-bold uppercase tracking-wider">
                <UserCheck className="w-4 h-4 animate-bounce" />
                <span>Human Approval Interface</span>
              </div>

              <div className="text-xs text-slate-300 space-y-2">
                <p>
                  Action <span className="font-mono font-bold text-white">{pendingApproval.action_type}</span> requires human authorization before execution.
                </p>
                <div className="p-2 bg-background/80 rounded border border-surfaceBorder text-[11px] font-mono text-slate-400">
                  Parameters: {JSON.stringify(pendingApproval.action_params)}
                </div>
              </div>

              {approvalError && (
                <div className="p-2.5 bg-rose-500/20 border border-rose-500/40 rounded text-rose-200 text-xs">
                  {approvalError}
                </div>
              )}

              {/* Role Selector for testing demo authorization */}
              <div className="space-y-1.5 text-xs">
                <label className="font-mono text-slate-400 text-[11px]">
                  Authorize As Operator Role:
                </label>
                <select
                  value={operatorRole}
                  onChange={(e) => setOperatorRole(e.target.value)}
                  className="w-full bg-background border border-surfaceBorder rounded px-2.5 py-1.5 text-xs text-white font-mono"
                >
                  <option value="demo_operator">demo_operator (Authorized Operator)</option>
                  <option value="supervisor">supervisor (Flight Supervisor)</option>
                  <option value="viewer">viewer (Unauthorized - Test 403 Rejection)</option>
                </select>
              </div>

              {/* Optional Rejection Reason */}
              <div className="space-y-1.5 text-xs">
                <label className="font-mono text-slate-400 text-[11px]">
                  Rejection Reason (if rejecting):
                </label>
                <input
                  type="text"
                  placeholder="e.g. Weather risk unacceptable"
                  value={rejectionReason}
                  onChange={(e) => setRejectionReason(e.target.value)}
                  className="w-full bg-background border border-surfaceBorder rounded px-2.5 py-1.5 text-xs text-white placeholder-slate-600 font-mono"
                />
              </div>

              {/* Action Buttons */}
              <div className="flex items-center gap-2 pt-2">
                <button
                  onClick={() => handleResolveApproval("APPROVE")}
                  disabled={actionLoading}
                  className="flex-1 py-2 px-3 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-mono font-bold text-xs rounded transition-colors"
                >
                  Approve Action
                </button>
                <button
                  onClick={() => handleResolveApproval("REJECT")}
                  disabled={actionLoading}
                  className="flex-1 py-2 px-3 bg-rose-500/20 hover:bg-rose-500/30 border border-rose-500/40 text-rose-300 font-mono text-xs rounded transition-colors"
                >
                  Reject Action
                </button>
              </div>
            </div>
          )}

          {/* Operational Telemetry Snapshot Card */}
          <div className="bg-surface border border-surfaceBorder rounded-xl p-5 space-y-4">
            <h2 className="text-sm font-bold text-white flex items-center gap-2 font-mono uppercase tracking-wide border-b border-surfaceBorder pb-3">
              <Radio className="w-4 h-4 text-accent-blue" />
              Operational Telemetry Snapshot
            </h2>

            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="p-2.5 bg-background/60 rounded border border-surfaceBorder space-y-0.5">
                <span className="text-[10px] font-mono text-slate-400 block">Battery Level</span>
                <span className={`text-base font-mono font-bold ${(telemetry.battery_pct ?? 100) < 30 ? "text-rose-400" : "text-emerald-400"}`}>
                  {telemetry.battery_pct !== undefined ? `${telemetry.battery_pct}%` : "N/A"}
                </span>
              </div>

              <div className="p-2.5 bg-background/60 rounded border border-surfaceBorder space-y-0.5">
                <span className="text-[10px] font-mono text-slate-400 block">Altitude</span>
                <span className="text-base font-mono font-bold text-slate-200">
                  {telemetry.altitude_m !== undefined ? `${telemetry.altitude_m} m` : "N/A"}
                </span>
              </div>

              <div className="p-2.5 bg-background/60 rounded border border-surfaceBorder space-y-0.5">
                <span className="text-[10px] font-mono text-slate-400 block">Current Speed</span>
                <span className="text-base font-mono font-bold text-slate-200">
                  {telemetry.speed_mps !== undefined ? `${telemetry.speed_mps} m/s` : "N/A"}
                </span>
              </div>

              <div className="p-2.5 bg-background/60 rounded border border-surfaceBorder space-y-0.5">
                <span className="text-[10px] font-mono text-slate-400 block">Heartbeat Link</span>
                <span className={`text-base font-mono font-bold ${telemetry.heartbeat_ok ? "text-emerald-400" : "text-rose-400"}`}>
                  {telemetry.heartbeat_ok ? "ACTIVE" : "DESYNC"}
                </span>
              </div>
            </div>

            <div className="p-2.5 bg-background/60 rounded border border-surfaceBorder text-xs space-y-1">
              <span className="text-[10px] font-mono text-slate-400 block">GPS Position</span>
              <div className="font-mono text-slate-200">
                Lat: {telemetry.gps_lat ?? "N/A"} • Lon: {telemetry.gps_lon ?? "N/A"}
              </div>
              <div className="text-[10px] text-slate-500 font-mono">
                Timestamp: {telemetry.timestamp || "None"}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
