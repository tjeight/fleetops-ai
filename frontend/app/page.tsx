"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  AlertTriangle,
  ShieldCheck,
  Clock,
  CheckCircle2,
  XCircle,
  Play,
  ArrowRight,
  BatteryCharging,
  Cpu,
  RefreshCw,
  ExternalLink
} from "lucide-react";
import { api } from "@/lib/api";
import { DashboardStats, Incident } from "@/lib/types";
import { StatusBadge, SeverityBadge, PolicyPill } from "@/components/StatusBadge";

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recentIncidents, setRecentIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [runningScenario, setRunningScenario] = useState<string | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [statsData, incidentsData] = await Promise.all([
        api.getDashboardStats(),
        api.listIncidents(undefined, undefined),
      ]);
      setStats(statsData);
      setRecentIncidents(incidentsData.slice(0, 6));
    } catch (err: any) {
      setError(err.message || "Failed to connect to FleetOps API server.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleQuickRun = async (scenarioId: string) => {
    try {
      setRunningScenario(scenarioId);
      await api.runScenario(scenarioId);
      await loadData();
    } catch (err: any) {
      alert(`Error running scenario: ${err.message}`);
    } finally {
      setRunningScenario(null);
    }
  };

  if (loading && !stats) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <RefreshCw className="w-8 h-8 text-accent-blue animate-spin" />
        <p className="text-slate-400 font-mono text-sm">Telemetry & Incident stream loading...</p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Top Banner / Headline */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-surfaceBorder pb-6">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight flex items-center gap-3">
            Operations Center
            <span className="text-xs font-mono font-normal bg-blue-500/10 text-accent-blue border border-blue-500/20 px-2.5 py-1 rounded">
              SITE ALPHA-01
            </span>
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Real-time incident triage, evidence correlation, and deterministic flight safety policy gating.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={loadData}
            disabled={loading}
            className="flex items-center text-xs font-mono px-3 py-2 bg-surface hover:bg-surfaceHover border border-surfaceBorder rounded-md text-slate-300 transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 mr-2 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
          <Link
            href="/scenarios"
            className="flex items-center text-xs font-mono px-4 py-2 bg-accent-blue hover:bg-sky-400 text-slate-950 font-bold rounded-md transition-colors"
          >
            <Play className="w-3.5 h-3.5 mr-2 fill-current" />
            Scenario Replay
          </Link>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 text-sm flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 flex-shrink-0 text-rose-400 mt-0.5" />
          <div className="flex-1">
            <p className="font-semibold">Backend Connection Alert</p>
            <p className="text-xs text-rose-200/80 mt-1">{error}</p>
            <p className="text-xs text-slate-400 mt-2">
              Ensure FastAPI backend is running on <code className="bg-slate-950 px-1 py-0.5 rounded">http://localhost:8000</code>.
            </p>
          </div>
          <button
            onClick={loadData}
            className="px-2.5 py-1 bg-rose-500/20 hover:bg-rose-500/30 rounded text-xs font-mono text-rose-200"
          >
            Retry
          </button>
        </div>
      )}

      {/* KPI Stats Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
        <div className="bg-surface border border-surfaceBorder rounded-xl p-4 flex flex-col justify-between">
          <span className="text-xs font-mono text-slate-400">TOTAL INCIDENTS</span>
          <span className="text-2xl font-bold font-mono text-white mt-2">
            {stats?.total_incidents ?? 0}
          </span>
          <span className="text-[11px] text-slate-500 mt-1 font-mono">Logged to audit</span>
        </div>

        <div className="bg-surface border border-surfaceBorder rounded-xl p-4 flex flex-col justify-between">
          <span className="text-xs font-mono text-blue-400">OPEN / TRIAGE</span>
          <span className="text-2xl font-bold font-mono text-blue-400 mt-2">
            {stats?.open_incidents ?? 0}
          </span>
          <span className="text-[11px] text-slate-500 mt-1 font-mono">Pending agent run</span>
        </div>

        <div className="bg-surface border border-surfaceBorder rounded-xl p-4 flex flex-col justify-between">
          <span className="text-xs font-mono text-amber-400">AWAITING APPROVAL</span>
          <span className="text-2xl font-bold font-mono text-amber-400 mt-2">
            {stats?.awaiting_approval_incidents ?? 0}
          </span>
          <span className="text-[11px] text-slate-500 mt-1 font-mono">Operator action required</span>
        </div>

        <div className="bg-surface border border-surfaceBorder rounded-xl p-4 flex flex-col justify-between">
          <span className="text-xs font-mono text-purple-400">INVESTIGATING</span>
          <span className="text-2xl font-bold font-mono text-purple-400 mt-2">
            {stats?.investigating_incidents ?? 0}
          </span>
          <span className="text-[11px] text-slate-500 mt-1 font-mono">LangGraph processing</span>
        </div>

        <div className="bg-surface border border-surfaceBorder rounded-xl p-4 flex flex-col justify-between">
          <span className="text-xs font-mono text-emerald-400">RESOLVED</span>
          <span className="text-2xl font-bold font-mono text-emerald-400 mt-2">
            {stats?.resolved_incidents ?? 0}
          </span>
          <span className="text-[11px] text-slate-500 mt-1 font-mono">Executed safely</span>
        </div>

        <div className="bg-surface border border-surfaceBorder rounded-xl p-4 flex flex-col justify-between">
          <span className="text-xs font-mono text-rose-400">SAFETY BLOCKED</span>
          <span className="text-2xl font-bold font-mono text-rose-400 mt-2">
            {stats?.blocked_incidents ?? 0}
          </span>
          <span className="text-[11px] text-slate-500 mt-1 font-mono">Policy enforced</span>
        </div>
      </div>

      {/* Quick Scenario Run Bar */}
      <div className="bg-gradient-to-r from-surface to-surface/40 border border-surfaceBorder rounded-xl p-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
          <div>
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <Play className="w-4 h-4 text-accent-blue" />
              Quick Scenario Injection
            </h2>
            <p className="text-xs text-slate-400">
              One-click simulate incidents to test deterministic safety policies and RAG retrieval.
            </p>
          </div>
          <Link
            href="/scenarios"
            className="text-xs text-accent-blue hover:underline flex items-center gap-1"
          >
            View all 9 scenarios <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          <button
            onClick={() => handleQuickRun("low_battery")}
            disabled={runningScenario !== null}
            className="flex flex-col text-left p-3 rounded-lg bg-surface/80 hover:bg-surfaceHover border border-surfaceBorder hover:border-rose-500/40 transition-all text-xs"
          >
            <div className="flex items-center justify-between font-mono font-semibold text-rose-400">
              <span>Low Battery (18%)</span>
              <span className="text-[10px] bg-rose-500/20 px-1.5 py-0.5 rounded">BLOCK</span>
            </div>
            <p className="text-slate-400 text-[11px] mt-1.5 line-clamp-2">
              Proposes dispatch; safety policy gate strictly blocks reserve violation.
            </p>
          </button>

          <button
            onClick={() => handleQuickRun("conflicting_sops")}
            disabled={runningScenario !== null}
            className="flex flex-col text-left p-3 rounded-lg bg-surface/80 hover:bg-surfaceHover border border-surfaceBorder hover:border-amber-500/40 transition-all text-xs"
          >
            <div className="flex items-center justify-between font-mono font-semibold text-amber-400">
              <span>Conflicting SOP-005</span>
              <span className="text-[10px] bg-amber-500/20 px-1.5 py-0.5 rounded">APPROVAL</span>
            </div>
            <p className="text-slate-400 text-[11px] mt-1.5 line-clamp-2">
              High-wind perimeter alarm retrieves contradictory guidance; pauses for operator.
            </p>
          </button>

          <button
            onClick={() => handleQuickRun("geofence_violation")}
            disabled={runningScenario !== null}
            className="flex flex-col text-left p-3 rounded-lg bg-surface/80 hover:bg-surfaceHover border border-surfaceBorder hover:border-rose-500/40 transition-all text-xs"
          >
            <div className="flex items-center justify-between font-mono font-semibold text-rose-400">
              <span>Geofence Breach</span>
              <span className="text-[10px] bg-rose-500/20 px-1.5 py-0.5 rounded">BLOCK</span>
            </div>
            <p className="text-slate-400 text-[11px] mt-1.5 line-clamp-2">
              Waypoints outside operational bounding box are unconditionally blocked.
            </p>
          </button>

          <button
            onClick={() => handleQuickRun("normal_patrol_failure")}
            disabled={runningScenario !== null}
            className="flex flex-col text-left p-3 rounded-lg bg-surface/80 hover:bg-surfaceHover border border-surfaceBorder hover:border-emerald-500/40 transition-all text-xs"
          >
            <div className="flex items-center justify-between font-mono font-semibold text-emerald-400">
              <span>Normal Patrol Fault</span>
              <span className="text-[10px] bg-emerald-500/20 px-1.5 py-0.5 rounded">EXECUTE</span>
            </div>
            <p className="text-slate-400 text-[11px] mt-1.5 line-clamp-2">
              Optical payload glitch; SOP-004 cited, safe diagnostic hover allowed.
            </p>
          </button>
        </div>
      </div>

      {/* Main Two-Column Layout: Simulated Fleet Health & Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column (2 spans): Recent Incidents */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-amber-400" />
              Active & Recent Incidents
            </h2>
            <Link
              href="/incidents"
              className="text-xs text-accent-blue hover:underline flex items-center gap-1 font-mono"
            >
              All Incidents ({stats?.total_incidents ?? 0}) <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          {recentIncidents.length === 0 ? (
            <div className="p-8 text-center bg-surface border border-surfaceBorder rounded-xl">
              <ShieldCheck className="w-10 h-10 text-emerald-400 mx-auto mb-2 opacity-80" />
              <p className="text-sm text-slate-300 font-semibold">Zero active incidents</p>
              <p className="text-xs text-slate-500 mt-1">
                Inject a sample scenario above to observe LangGraph investigation.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {recentIncidents.map((incident) => {
                const latestDecision = incident.policy_decisions?.[0]?.outcome;
                const hasPendingApproval = incident.approval_requests?.some(a => a.status === "PENDING");
                
                return (
                  <Link
                    key={incident.id}
                    href={`/incidents/${incident.id}`}
                    className="block p-4 rounded-xl bg-surface border border-surfaceBorder hover:border-accent-blue/50 hover:bg-surfaceHover transition-all group"
                  >
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                      <div className="flex items-center space-x-3">
                        <span className="font-mono text-xs font-bold text-slate-400 group-hover:text-accent-blue transition-colors">
                          {incident.id}
                        </span>
                        <SeverityBadge severity={incident.severity} />
                        <span className="font-semibold text-sm text-white">
                          {incident.drone_id}
                        </span>
                        <span className="text-xs text-slate-400 font-mono">
                          {incident.site_id}
                        </span>
                      </div>
                      <div className="flex items-center space-x-2">
                        {latestDecision && <PolicyPill outcome={latestDecision} />}
                        <StatusBadge status={incident.status} />
                      </div>
                    </div>

                    <div className="mt-2.5 flex flex-col sm:flex-row sm:items-center justify-between text-xs text-slate-400 gap-1 border-t border-surfaceBorder/60 pt-2.5">
                      <span className="font-mono text-slate-300">
                        Event: <span className="text-accent-blue">{incident.event_type}</span>
                      </span>
                      {hasPendingApproval && (
                        <span className="text-amber-400 font-mono font-bold animate-pulse">
                          ACTION AWAITING OPERATOR APPROVAL
                        </span>
                      )}
                      <span className="text-[11px] text-slate-500">
                        {new Date(incident.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                      </span>
                    </div>
                  </Link>
                );
              })}
            </div>
          )}
        </div>

        {/* Right Column: Simulated Fleet Health */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Cpu className="w-5 h-5 text-accent-blue" />
              Simulated Fleet Roster
            </h2>
            <span className="text-[10px] font-mono text-slate-500">4 UNITS ACTIVE</span>
          </div>

          <div className="bg-surface border border-surfaceBorder rounded-xl p-4 space-y-3">
            {stats?.fleet_health?.map((drone) => (
              <div
                key={drone.drone_id}
                className="p-3 rounded-lg bg-background/50 border border-surfaceBorder/80 flex items-center justify-between text-xs"
              >
                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <span className="font-mono font-bold text-white">{drone.drone_id}</span>
                    <span className="text-[10px] font-mono text-slate-400">{drone.site_id}</span>
                  </div>
                  <div className="text-[11px] text-slate-400 font-mono">
                    Status: <span className="text-slate-300">{drone.status}</span>
                  </div>
                </div>

                <div className="text-right space-y-1">
                  <div className="flex items-center space-x-1.5 font-mono">
                    <BatteryCharging className="w-3.5 h-3.5 text-accent-emerald" />
                    <span className={`font-bold ${drone.battery_pct < 30 ? "text-rose-400" : "text-emerald-400"}`}>
                      {drone.battery_pct}%
                    </span>
                  </div>
                  <span className="text-[10px] text-slate-500 font-mono">TELEMETRY OK</span>
                </div>
              </div>
            ))}

            <div className="border-t border-surfaceBorder/80 pt-3 text-[11px] text-slate-400 font-mono flex items-center justify-between">
              <span>Geofence Status:</span>
              <span className="text-emerald-400 font-bold">CONTAINED</span>
            </div>
            <div className="text-[11px] text-slate-400 font-mono flex items-center justify-between">
              <span>Policy Enforcement:</span>
              <span className="text-accent-blue font-bold">DETERMINISTIC GATE</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
