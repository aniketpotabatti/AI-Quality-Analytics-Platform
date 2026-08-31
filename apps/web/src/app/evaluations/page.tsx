"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Sidebar from "@/components/layout/Sidebar";
import {
  getMe,
  listEvaluationRuns,
  type EvaluationRunResponse,
} from "@/lib/api-client";
import { getAccessToken } from "@/lib/api-client";
import Link from "next/link";

const STATUSES = ["all", "pending", "running", "completed", "failed", "cancelled"] as const;

function StatusBadge({ status }: { status: string }) {
  return <span className={`badge badge-${status}`}>{status}</span>;
}

function ProgressBar({ run }: { run: EvaluationRunResponse }) {
  const pct = run.total_cases > 0 ? (run.completed_cases / run.total_cases) * 100 : 0;
  const color = run.status === "completed" ? "var(--green)"
    : run.status === "failed" ? "var(--red)"
    : "var(--brand-500)";
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
      <div className="score-bar" style={{ flex: 1, minWidth: 80 }}>
        <div className="score-bar-fill" style={{ width: `${pct}%`, background: color }} />
      </div>
      <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", minWidth: 32 }}>
        {run.completed_cases}/{run.total_cases}
      </span>
    </div>
  );
}

export default function EvaluationsPage() {
  const router = useRouter();
  const [runs, setRuns] = useState<EvaluationRunResponse[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [wsId, setWsId] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState("all");

  useEffect(() => {
    const token = getAccessToken();
    if (!token) { router.push("/login"); return; }

    (async () => {
      try {
        const me = await getMe();
        const workspaceId = me.workspaces[0]?.workspace_id;
        if (!workspaceId) { setLoading(false); return; }
        setWsId(workspaceId);
      } catch {
        router.push("/login");
      } finally {
        setLoading(false);
      }
    })();
  }, [router]);

  useEffect(() => {
    if (!wsId) return;
    setLoading(true);
    listEvaluationRuns(wsId, {
      status: statusFilter === "all" ? undefined : statusFilter,
      limit: 50,
    }).then(data => {
      setRuns(data.items);
      setTotal(data.pagination.total);
    }).finally(() => setLoading(false));
  }, [wsId, statusFilter]);

  return (
    <div className="app-layout">
      <Sidebar />
      <main className="main-content">
        <div className="page-header">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
            <div>
              <h1 className="gradient-text" style={{ fontSize: "1.75rem", fontWeight: 800, marginBottom: 4 }}>
                Evaluations
              </h1>
              <p style={{ color: "var(--text-muted)", fontSize: "0.9375rem" }}>
                {total} evaluation run{total !== 1 ? "s" : ""}
              </p>
            </div>
            <Link href="/evaluations/new" className="btn btn-primary">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <line x1="12" y1="5" x2="12" y2="19" />
                <line x1="5" y1="12" x2="19" y2="12" />
              </svg>
              New Run
            </Link>
          </div>
        </div>

        <div className="page-content">
          {/* Filter tabs */}
          <div style={{ display: "flex", gap: "0.375rem", marginBottom: "1.5rem", padding: "4px", background: "var(--bg-elevated)", borderRadius: 10, width: "fit-content" }}>
            {STATUSES.map(s => (
              <button
                key={s}
                onClick={() => setStatusFilter(s)}
                style={{
                  padding: "0.375rem 0.875rem",
                  borderRadius: 7,
                  border: "none",
                  background: statusFilter === s ? "var(--bg-overlay)" : "transparent",
                  color: statusFilter === s ? "var(--text-primary)" : "var(--text-muted)",
                  fontSize: "0.8125rem",
                  fontWeight: statusFilter === s ? 600 : 400,
                  cursor: "pointer",
                  transition: "all 0.15s",
                  fontFamily: "inherit",
                  textTransform: "capitalize",
                }}
              >
                {s}
              </button>
            ))}
          </div>

          {loading ? (
            <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
              {[1,2,3,4].map(i => (
                <div key={i} style={{ height: 60, borderRadius: 8 }} className="skeleton" />
              ))}
            </div>
          ) : runs.length === 0 ? (
            <div className="card empty-state">
              <div className="empty-icon">⚡</div>
              <h3 style={{ fontWeight: 600, marginBottom: "0.5rem" }}>No evaluation runs</h3>
              <p style={{ color: "var(--text-muted)", marginBottom: "1.5rem", fontSize: "0.9375rem" }}>
                {statusFilter !== "all" ? `No runs with status "${statusFilter}".` : "Create your first evaluation run."}
              </p>
              <Link href="/evaluations/new" className="btn btn-primary">
                Start New Run
              </Link>
            </div>
          ) : (
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Status</th>
                    <th>Progress</th>
                    <th>Pass Rate</th>
                    <th>Avg Score</th>
                    <th>Started</th>
                    <th>Duration</th>
                  </tr>
                </thead>
                <tbody>
                  {runs.map(run => {
                    const startedAt = run.started_at ? new Date(run.started_at) : null;
                    const completedAt = run.completed_at ? new Date(run.completed_at) : null;
                    const durationMs = startedAt && completedAt ? completedAt.getTime() - startedAt.getTime() : null;
                    const durationStr = durationMs != null
                      ? durationMs < 60000 ? `${Math.round(durationMs / 1000)}s`
                        : `${Math.round(durationMs / 60000)}m`
                      : "—";

                    return (
                      <tr
                        key={run.id}
                        onClick={() => router.push(`/evaluations/${run.id}`)}
                        style={{ cursor: "pointer" }}
                      >
                        <td style={{ color: "var(--text-primary)", fontWeight: 500 }}>
                          {run.name}
                        </td>
                        <td><StatusBadge status={run.status} /></td>
                        <td style={{ minWidth: 160 }}><ProgressBar run={run} /></td>
                        <td>
                          {run.pass_rate != null
                            ? <span style={{ color: run.pass_rate >= 0.7 ? "var(--green)" : run.pass_rate >= 0.4 ? "var(--amber)" : "var(--red)", fontWeight: 600 }}>
                                {Math.round(run.pass_rate * 100)}%
                              </span>
                            : <span style={{ color: "var(--text-muted)" }}>—</span>
                          }
                        </td>
                        <td>
                          {run.average_score != null
                            ? <span style={{ fontWeight: 600, color: "var(--text-primary)" }}>
                                {run.average_score.toFixed(2)}
                              </span>
                            : <span style={{ color: "var(--text-muted)" }}>—</span>
                          }
                        </td>
                        <td style={{ color: "var(--text-muted)", fontSize: "0.8125rem" }}>
                          {startedAt ? startedAt.toLocaleDateString() : new Date(run.created_at).toLocaleDateString()}
                        </td>
                        <td style={{ color: "var(--text-muted)", fontSize: "0.8125rem" }}>
                          {durationStr}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
