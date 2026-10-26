"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  Play,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  RefreshCw,
  ExternalLink,
  Shield,
  HelpCircle,
  ArrowRight,
  Info
} from "lucide-react";
import { api } from "@/lib/api";
import { ScenarioItem, ScenarioRunResult } from "@/lib/types";
import { StatusBadge, PolicyPill } from "@/components/StatusBadge";

export default function ScenariosPage() {
  const [scenarios, setScenarios] = useState<ScenarioItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Results map by scenarioId
  const [runningId, setRunningId] = useState<string | null>(null);
  const [results, setResults] = useState<Record<string, ScenarioRunResult>>({});

  useEffect(() => {
    const loadScenarios = async () => {
      try {
        setLoading(true);
        const data = await api.getScenarios();
        setScenarios(data);
      } catch (err: any) {
        setError(err.message || "Failed to load scenario catalog.");
      } finally {
        setLoading(false);
      }
    };
    loadScenarios();
  }, []);

  const handleRunScenario = async (scenarioId: string) => {
    try {
      setRunningId(scenarioId);
      const res = await api.runScenario(scenarioId);
      setResults((prev) => ({ ...prev, [scenarioId]: res }));
    } catch (err: any) {
      alert(`Scenario run failed: ${err.message}`);
    } finally {
      setRunningId(null);
    }
  };

  const handleRunAll = async () => {
    for (const sc of scenarios) {
      await handleRunScenario(sc.id);
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-surfaceBorder pb-6">
        <div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight flex items-center gap-2.5">
            <Play className="w-6 h-6 text-accent-blue" />
            Deterministic Scenario Replay Suite
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Repeatable automated test scenarios validating deterministic policy gates, RAG grounding, and fault tolerance.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleRunAll}
            disabled={runningId !== null || scenarios.length === 0}
            className="flex items-center text-xs font-mono font-bold px-4 py-2 bg-accent-blue hover:bg-sky-400 text-slate-950 rounded-md transition-colors disabled:opacity-50"
          >
            <Play className="w-3.5 h-3.5 mr-2 fill-current" />
            Run All 9 Scenarios
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs">
          {error}
        </div>
      )}

      {loading ? (
        <div className="p-12 text-center text-slate-400 font-mono text-xs flex flex-col items-center justify-center space-y-2">
          <RefreshCw className="w-6 h-6 animate-spin text-accent-blue" />
          <span>Loading scenario definitions...</span>
        </div>
      ) : (
        <div className="space-y-4">
          {scenarios.map((sc) => {
            const result = results[sc.id];
            const isRunning = runningId === sc.id;

            return (
              <div
                key={sc.id}
                className="bg-surface border border-surfaceBorder rounded-xl p-5 space-y-4 hover:border-slate-700 transition-colors"
              >
                <div className="flex flex-col md:flex-row md:items-start justify-between gap-3">
                  <div className="space-y-1">
                    <div className="flex items-center space-x-2">
                      <span className="font-mono text-xs font-bold text-accent-blue">
                        {sc.id.toUpperCase()}
                      </span>
                      <h2 className="text-sm font-bold text-white">{sc.name}</h2>
                    </div>
                    <p className="text-xs text-slate-400 leading-relaxed max-w-3xl">
                      {sc.description}
                    </p>
                  </div>

                  <div className="flex items-center gap-2 flex-shrink-0">
                    <button
                      onClick={() => handleRunScenario(sc.id)}
                      disabled={isRunning}
                      className="flex items-center text-xs font-mono font-bold px-3 py-1.5 bg-surface hover:bg-surfaceHover border border-surfaceBorder hover:border-accent-blue text-slate-200 rounded transition-colors disabled:opacity-50"
                    >
                      <Play className={`w-3 h-3 mr-1.5 ${isRunning ? "animate-spin" : "fill-current"}`} />
                      {isRunning ? "Executing..." : "Replay"}
                    </button>
                  </div>
                </div>

                {/* Scenario Contract & Expectations */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px] font-mono bg-background/50 p-2.5 rounded-lg border border-surfaceBorder/80">
                  <div>
                    <span className="text-slate-500 block">Drone & Site:</span>
                    <span className="text-slate-300">{sc.drone_id} ({sc.site_id})</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block">Event Type:</span>
                    <span className="text-slate-300">{sc.event_type}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block">Expected Gate:</span>
                    <span className="text-accent-blue font-bold">{sc.expected_policy_decision}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block">Expected Outcome:</span>
                    <span className="text-slate-300 font-bold">{sc.expected_outcome}</span>
                  </div>
                </div>

                {/* Live Execution Outcome Result Card */}
                {result && (
                  <div
                    className={`p-4 rounded-lg border text-xs space-y-3 ${
                      result.matches_expected
                        ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-200"
                        : "bg-rose-500/10 border-rose-500/30 text-rose-200"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2 font-mono font-bold">
                        {result.matches_expected ? (
                          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                        ) : (
                          <XCircle className="w-4 h-4 text-rose-400" />
                        )}
                        <span>
                          {result.matches_expected
                            ? "PASSED: Ground Truth Verified"
                            : "FAILED: Outcome Divergence"}
                        </span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <PolicyPill outcome={result.actual_policy_decision} />
                        <StatusBadge status={result.actual_status} />
                      </div>
                    </div>

                    {result.unauthorized_auth_blocked && (
                      <div className="text-[11px] font-mono text-emerald-300 bg-emerald-950/40 p-2 rounded border border-emerald-500/30">
                        Authorization Check: Operator with 'viewer' role rejected with HTTP 403 Forbidden.
                      </div>
                    )}

                    <div className="flex items-center justify-between pt-1 border-t border-surfaceBorder/60 text-[11px] font-mono">
                      <span className="text-slate-400">
                        Recorded Incident: <span className="text-white font-bold">{result.incident?.id}</span>
                      </span>
                      <Link
                        href={`/incidents/${result.incident?.id}`}
                        className="text-accent-blue hover:underline flex items-center gap-1"
                      >
                        Inspect Audit Details <ArrowRight className="w-3 h-3" />
                      </Link>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
