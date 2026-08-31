"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Sidebar from "@/components/layout/Sidebar";
import {
  getMe,
  getEvaluationRun,
  listEvaluationResults,
  type EvaluationRunResponse,
  type EvaluationResultResponse,
} from "@/lib/api-client";
import { getAccessToken } from "@/lib/api-client";
import Link from "next/link";

function StatusBadge({ status }: { status: string }) {
  return <span className={`badge badge-${status}`}>{status}</span>;
}

export default function EvaluationDetailPage() {
  const router = useRouter();
  const params = useParams();
  const runId = params.runId as string;

  const [wsId, setWsId] = useState<string | null>(null);
  const [run, setRun] = useState<EvaluationRunResponse | null>(null);
  const [results, setResults] = useState<EvaluationResultResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedResult, setSelectedResult] = useState<EvaluationResultResponse | null>(null);

  async function loadData(workspaceId: string) {
    try {
      const [r, res] = await Promise.all([
        getEvaluationRun(workspaceId, runId),
        listEvaluationResults(workspaceId, runId, 100),
      ]);
      setRun(r);
      setResults(res.items);
    } catch {
      router.push("/evaluations");
    }
  }

  useEffect(() => {
    const token = getAccessToken();
    if (!token) { router.push("/login"); return; }

    (async () => {
      try {
        const me = await getMe();
        const workspaceId = me.workspaces[0]?.workspace_id;
        if (!workspaceId) return;
        setWsId(workspaceId);
        await loadData(workspaceId);
      } finally {
        setLoading(false);
      }
    })();
  }, [router, runId]);

  // Poll if still running
  useEffect(() => {
    if (!wsId || !run || (run.status !== "running" && run.status !== "pending")) return;
    const interval = setInterval(() => {
      loadData(wsId);
    }, 3000);
    return () => clearInterval(interval);
  }, [wsId, run]);

  const pct = run && run.total_cases > 0 ? (run.completed_cases / run.total_cases) * 100 : 0;
  
  return (
    <div className="app-layout">
      <Sidebar />
      <main className="main-content">
        <div className="page-header">
          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "0.5rem" }}>
            <Link href="/evaluations" style={{ color: "var(--text-muted)", textDecoration: "none", fontSize: "0.875rem" }}>
              ← Evaluations
            </Link>
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
            <div>
              <h1 className="gradient-text" style={{ fontSize: "1.75rem", fontWeight: 800, marginBottom: 4 }}>
                {loading ? "Loading…" : run?.name}
              </h1>
              <p style={{ color: "var(--text-muted)", fontSize: "0.9375rem", display: "flex", alignItems: "center", gap: 12 }}>
                {run && <StatusBadge status={run.status} />}
                <span>
                  {run?.completed_cases} of {run?.total_cases} completed
                </span>
                {run?.average_score != null && (
                  <span>· Avg Score: {run.average_score.toFixed(2)}</span>
                )}
                {run?.pass_rate != null && (
                  <span>· Pass Rate: {Math.round(run.pass_rate * 100)}%</span>
                )}
              </p>
            </div>
            {run?.status === "running" && (
              <button className="btn btn-danger" disabled>
                Stop Run
              </button>
            )}
          </div>
        </div>

        <div className="page-content">
          {loading ? (
            <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
              {[1,2,3,4].map(i => (
                <div key={i} style={{ height: 56, borderRadius: 8 }} className="skeleton" />
              ))}
            </div>
          ) : (
            <>
              {run && (run.status === "pending" || run.status === "running") && (
                <div className="card" style={{ marginBottom: "1.5rem" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.5rem", fontSize: "0.875rem" }}>
                    <span style={{ fontWeight: 500, color: "var(--brand-400)" }}>Evaluation in progress…</span>
                    <span style={{ color: "var(--text-muted)" }}>{Math.round(pct)}%</span>
                  </div>
                  <div className="score-bar">
                    <div className="score-bar-fill" style={{ width: `${pct}%`, background: "var(--brand-500)" }} />
                  </div>
                </div>
              )}

              {results.length === 0 ? (
                <div className="card empty-state">
                  <div className="empty-icon">⏳</div>
                  <h3 style={{ fontWeight: 600, marginBottom: "0.5rem" }}>No results yet</h3>
                  <p style={{ color: "var(--text-muted)", fontSize: "0.9375rem" }}>
                    Waiting for the evaluation pipeline to process test cases.
                  </p>
                </div>
              ) : (
                <div style={{ display: "grid", gridTemplateColumns: selectedResult ? "1fr 400px" : "1fr", gap: "1rem" }}>
                  <div className="table-container">
                    <table>
                      <thead>
                        <tr>
                          <th>Status</th>
                          <th>Test Case ID</th>
                          <th>Overall Score</th>
                          <th>Metrics</th>
                        </tr>
                      </thead>
                      <tbody>
                        {results.map(res => (
                          <tr
                            key={res.id}
                            onClick={() => setSelectedResult(selectedResult?.id === res.id ? null : res)}
                            style={{
                              cursor: "pointer",
                              background: selectedResult?.id === res.id ? "rgba(99,102,241,0.08)" : undefined,
                            }}
                          >
                            <td><StatusBadge status={res.status} /></td>
                            <td style={{ color: "var(--text-muted)", fontSize: "0.8125rem", fontFamily: "monospace" }}>
                              {res.test_case_id.split("-")[0]}
                            </td>
                            <td>
                              {res.overall_score != null ? (
                                <span style={{ fontWeight: 600, color: "var(--text-primary)" }}>{res.overall_score.toFixed(2)}</span>
                              ) : "—"}
                            </td>
                            <td>
                              <div style={{ display: "flex", gap: "4px" }}>
                                {res.metric_scores.map(ms => (
                                  <div
                                    key={ms.id}
                                    title={`${ms.metric_type}: ${ms.score}`}
                                    style={{
                                      width: 8, height: 16, borderRadius: 2,
                                      background: ms.passed ? "var(--green)" : "var(--red)",
                                      opacity: ms.score > 0 ? 0.8 + (ms.score * 0.2) : 0.5
                                    }}
                                  />
                                ))}
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  {selectedResult && (
                    <div className="card animate-slide-in" style={{ position: "sticky", top: "1rem", maxHeight: "calc(100vh - 6rem)", overflowY: "auto" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "1rem" }}>
                        <h3 style={{ fontWeight: 600, fontSize: "0.9375rem" }}>Evaluation Details</h3>
                        <button onClick={() => setSelectedResult(null)} style={{ background: "none", border: "none", color: "var(--text-muted)", cursor: "pointer", fontSize: "1.125rem" }}>×</button>
                      </div>

                      {selectedResult.error_message && (
                        <div style={{ padding: "0.75rem", borderRadius: 8, background: "rgba(239,68,68,0.1)", color: "#f87171", fontSize: "0.875rem", marginBottom: "1rem" }}>
                          <strong>Error:</strong> {selectedResult.error_message}
                        </div>
                      )}

                      <h4 style={{ fontSize: "0.8125rem", textTransform: "uppercase", letterSpacing: "0.05em", color: "var(--text-muted)", marginBottom: "0.5rem" }}>
                        Metric Scores
                      </h4>

                      <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                        {selectedResult.metric_scores.map(ms => (
                          <div key={ms.id} style={{ background: "var(--bg-elevated)", border: "1px solid var(--border)", borderRadius: 8, padding: "0.875rem" }}>
                            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.5rem" }}>
                              <span style={{ fontWeight: 600, color: "var(--text-primary)", fontSize: "0.875rem" }}>
                                {ms.metric_type}
                              </span>
                              <span className={`badge ${ms.passed ? "badge-completed" : "badge-failed"}`}>
                                {ms.score.toFixed(2)}
                              </span>
                            </div>
                            {ms.rationale && (
                              <div style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", lineHeight: 1.5 }}>
                                {ms.rationale}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </div>
      </main>
    </div>
  );
}
