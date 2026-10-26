"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  AlertTriangle,
  Search,
  Filter,
  RefreshCw,
  ExternalLink,
  PlusCircle,
  Clock
} from "lucide-react";
import { api } from "@/lib/api";
import { Incident } from "@/lib/types";
import { StatusBadge, SeverityBadge, PolicyPill } from "@/components/StatusBadge";

export default function IncidentsListPage() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [severityFilter, setSeverityFilter] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");

  const loadIncidents = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.listIncidents(statusFilter, severityFilter);
      setIncidents(data);
    } catch (err: any) {
      setError(err.message || "Failed to load incidents.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadIncidents();
  }, [statusFilter, severityFilter]);

  const filtered = incidents.filter((inc) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      inc.id.toLowerCase().includes(q) ||
      inc.drone_id.toLowerCase().includes(q) ||
      inc.site_id.toLowerCase().includes(q) ||
      inc.event_type.toLowerCase().includes(q)
    );
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-surfaceBorder pb-6">
        <div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight flex items-center gap-2.5">
            <AlertTriangle className="w-6 h-6 text-amber-400" />
            Drone Incident Records
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Complete operational audit trail of alarms, investigation diagnoses, and safety decisions.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={loadIncidents}
            disabled={loading}
            className="flex items-center text-xs font-mono px-3 py-2 bg-surface hover:bg-surfaceHover border border-surfaceBorder rounded-md text-slate-300 transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 mr-2 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
          <Link
            href="/scenarios"
            className="flex items-center text-xs font-mono px-3 py-2 bg-blue-500/10 hover:bg-blue-500/20 text-accent-blue border border-blue-500/30 rounded-md transition-colors font-bold"
          >
            Run Seeded Scenarios
          </Link>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 bg-surface border border-surfaceBorder rounded-xl p-4">
        {/* Search */}
        <div className="relative">
          <Search className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
          <input
            type="text"
            placeholder="Search Drone, Site, or ID..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-background border border-surfaceBorder rounded-lg pl-9 pr-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-accent-blue"
          />
        </div>

        {/* Status Filter */}
        <div className="flex items-center space-x-2">
          <span className="text-xs font-mono text-slate-400">Status:</span>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="flex-1 bg-background border border-surfaceBorder rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-accent-blue font-mono"
          >
            <option value="ALL">All Statuses</option>
            <option value="OPEN">OPEN</option>
            <option value="AWAITING_APPROVAL">AWAITING APPROVAL</option>
            <option value="RESOLVED">RESOLVED</option>
            <option value="BLOCKED">BLOCKED</option>
            <option value="ERROR">ERROR</option>
          </select>
        </div>

        {/* Severity Filter */}
        <div className="flex items-center space-x-2">
          <span className="text-xs font-mono text-slate-400">Severity:</span>
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="flex-1 bg-background border border-surfaceBorder rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-accent-blue font-mono"
          >
            <option value="ALL">All Severities</option>
            <option value="LOW">LOW</option>
            <option value="MEDIUM">MEDIUM</option>
            <option value="HIGH">HIGH</option>
            <option value="CRITICAL">CRITICAL</option>
          </select>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs">
          {error}
        </div>
      )}

      {/* Incidents Table / List */}
      {loading ? (
        <div className="p-12 text-center text-slate-400 font-mono text-xs flex flex-col items-center justify-center space-y-2">
          <RefreshCw className="w-6 h-6 animate-spin text-accent-blue" />
          <span>Loading incidents from PostgreSQL database...</span>
        </div>
      ) : filtered.length === 0 ? (
        <div className="p-12 text-center bg-surface border border-surfaceBorder rounded-xl">
          <p className="text-sm font-semibold text-slate-300">No matching incidents found</p>
          <p className="text-xs text-slate-500 mt-1">
            Try adjusting your search criteria or trigger a scenario to inject an incident.
          </p>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-surfaceBorder bg-surface">
          <table className="min-w-full divide-y divide-surfaceBorder text-left text-xs">
            <thead className="bg-background/80 font-mono text-slate-400">
              <tr>
                <th className="px-4 py-3 font-semibold">INCIDENT ID</th>
                <th className="px-4 py-3 font-semibold">DRONE & SITE</th>
                <th className="px-4 py-3 font-semibold">EVENT TYPE</th>
                <th className="px-4 py-3 font-semibold">SEVERITY</th>
                <th className="px-4 py-3 font-semibold">STATUS</th>
                <th className="px-4 py-3 font-semibold">POLICY GATE</th>
                <th className="px-4 py-3 font-semibold">RECORDED</th>
                <th className="px-4 py-3 font-semibold text-right">ACTION</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-surfaceBorder/60 text-slate-300">
              {filtered.map((inc) => {
                const latestDecision = inc.policy_decisions?.[0]?.outcome;
                const formattedDate = new Date(inc.created_at).toLocaleString();

                return (
                  <tr
                    key={inc.id}
                    className="hover:bg-surfaceHover/80 transition-colors group"
                  >
                    <td className="px-4 py-3.5 font-mono font-bold text-accent-blue">
                      {inc.id}
                    </td>
                    <td className="px-4 py-3.5">
                      <div className="font-semibold text-white">{inc.drone_id}</div>
                      <div className="text-[11px] font-mono text-slate-400">{inc.site_id}</div>
                    </td>
                    <td className="px-4 py-3.5 font-mono text-slate-200">
                      {inc.event_type}
                    </td>
                    <td className="px-4 py-3.5">
                      <SeverityBadge severity={inc.severity} />
                    </td>
                    <td className="px-4 py-3.5">
                      <StatusBadge status={inc.status} />
                    </td>
                    <td className="px-4 py-3.5">
                      {latestDecision ? (
                        <PolicyPill outcome={latestDecision} />
                      ) : (
                        <span className="text-[11px] font-mono text-slate-500">PENDING RUN</span>
                      )}
                    </td>
                    <td className="px-4 py-3.5 text-slate-400 font-mono text-[11px]">
                      {formattedDate}
                    </td>
                    <td className="px-4 py-3.5 text-right">
                      <Link
                        href={`/incidents/${inc.id}`}
                        className="inline-flex items-center px-2.5 py-1 rounded bg-surface hover:bg-slate-700 border border-surfaceBorder text-slate-200 text-xs font-mono font-semibold transition-colors"
                      >
                        Inspect <ExternalLink className="w-3 h-3 ml-1" />
                      </Link>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
