"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Sidebar from "@/components/layout/Sidebar";
import {
  getMe,
  listWorkspaces,
  getWorkspaceSummary,
  listEvaluationRuns,
  type MeResponse,
  type WorkspaceSummaryResponse,
  type EvaluationRunResponse,
} from "@/lib/api-client";
import { getAccessToken } from "@/lib/api-client";
import Link from "next/link";

function StatusBadge({ status }: { status: string }) {
  return <span className={`badge badge-${status}`}>{status}</span>;
}

function ScoreCircle({ score }: { score: number | null | undefined }) {
  if (score == null) return <span style={{ color: "var(--text-muted)" }}>—</span>;
  const pct = Math.round(score * 100);
  const color = pct >= 70 ? "var(--green)" : pct >= 40 ? "var(--amber)" : "var(--red)";
  return (
    <span style={{ color, fontWeight: 600, fontSize: "0.9375rem" }}>{pct}%</span>
  );
}

export default function DashboardPage() {
  const router = useRouter();
  const [me, setMe] = useState<MeResponse | null>(null);
  const [summary, setSummary] = useState<WorkspaceSummaryResponse | null>(null);
  const [recentRuns, setRecentRuns] = useState<EvaluationRunResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [wsId, setWsId] = useState<string | null>(null);

  useEffect(() => {
    const token = getAccessToken();
    if (!token) { router.push("/login"); return; }

    (async () => {
      try {
        const meData = await getMe();
        setMe(meData);
        const workspaceId = meData.workspaces[0]?.workspace_id;
        if (!workspaceId) { setLoading(false); return; }
        setWsId(workspaceId);

        const [sum, runs] = await Promise.all([
          getWorkspaceSummary(workspaceId),
          listEvaluationRuns(workspaceId, { limit: 5 }),
        ]);
        setSummary(sum);
        setRecentRuns(runs.items);
      } catch {
        router.push("/login");
      } finally {
        setLoading(false);
      }
    })();
  }, [router]);

  if (loading) {
    return (
      <div className="app-layout">
        <Sidebar />
        <main className="main-content" style={{ display: "flex", alignItems: "center", justifyContent: "center" }}>
          <div style={{ textAlign: "center" }}>
            <div className="animate-spin" style={{ width: 40, height: 40, border: "3px solid var(--border)", borderTopColor: "var(--brand-500)", borderRadius: "50%", margin: "0 auto 1rem" }} />
            <p style={{ color: "var(--text-muted)" }}>Loading your workspace…</p>
          </div>
        </main>
      </div>
    );
  }

  const stats = [
    {
      label: "Datasets",
      value: summary?.dataset_count ?? 0,
      icon: "🗄️",
      link: `/datasets`,
    },
    {
      label: "Test Cases",
      value: summary?.test_case_count ?? 0,
      icon: "📝",
      link: null,
    },
    {
      label: "Evaluation Runs",
      value: summary?.evaluation_run_count ?? 0,
      icon: "⚡",
      link: `/evaluations`,
    },
    {
      label: "Completed Runs",
      value: summary?.completed_run_count ?? 0,
      icon: "✅",
      link: null,
    },
  ];

  return (
    <div className="app-layout">
      <Sidebar />
      <main className="main-content">
        {/* Header */}
        <div className="page-header">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
            <div>
              <h1 className="gradient-text" style={{ fontSize: "1.75rem", fontWeight: 800, marginBottom: 4 }}>
                Dashboard
              </h1>
              <p style={{ color: "var(--text-muted)", fontSize: "0.9375rem" }}>
                Welcome back, {me?.user.full_name || me?.user.email} · {me?.workspaces[0]?.workspace_name}
              </p>
            </div>
            <Link href="/evaluations/new" className="btn btn-primary">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <line x1="12" y1="5" x2="12" y2="19" />
                <line x1="5" y1="12" x2="19" y2="12" />
              </svg>
              New Evaluation
            </Link>
          </div>
        </div>

        <div className="page-content">
          {/* Stats Grid */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "1rem", marginBottom: "2rem" }}>
            {stats.map((stat) => (
              <div key={stat.label} className="stat-card">
                <div style={{ fontSize: "1.75rem", marginBottom: "0.75rem" }}>{stat.icon}</div>
                <div style={{ fontSize: "2rem", fontWeight: 700, color: "var(--text-primary)", lineHeight: 1 }}>
                  {stat.value.toLocaleString()}
                </div>
                <div style={{ fontSize: "0.875rem", color: "var(--text-muted)", marginTop: "0.25rem" }}>
                  {stat.label}
                </div>
              </div>
            ))}
          </div>

          {/* Recent Runs */}
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
              <h2 style={{ fontWeight: 600, fontSize: "1.0625rem", color: "var(--text-primary)" }}>
                Recent Evaluation Runs
              </h2>
              <Link href="/evaluations" style={{ color: "var(--brand-400)", fontSize: "0.875rem", textDecoration: "none" }}>
                View all →
              </Link>
            </div>

            {recentRuns.length === 0 ? (
              <div className="card empty-state">
                <div className="empty-icon">⚡</div>
                <h3 style={{ fontWeight: 600, marginBottom: "0.5rem" }}>No evaluations yet</h3>
                <p style={{ color: "var(--text-muted)", marginBottom: "1.5rem", fontSize: "0.9375rem" }}>
                  Create a dataset, add test cases, then run your first evaluation.
                </p>
                <Link href="/evaluations/new" className="btn btn-primary">
                  Start Evaluating
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
                      <th>Score</th>
                      <th>Created</th>
                    </tr>
                  </thead>
                  <tbody>
                    {recentRuns.map((run) => {
                      const progress = run.total_cases > 0
                        ? Math.round((run.completed_cases / run.total_cases) * 100)
                        : 0;
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
                          <td style={{ minWidth: 140 }}>
                            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                              <div className="score-bar" style={{ flex: 1 }}>
                                <div
                                  className="score-bar-fill"
                                  style={{
                                    width: `${progress}%`,
                                    background: run.status === "completed" ? "var(--green)"
                                      : run.status === "failed" ? "var(--red)"
                                      : "var(--brand-500)",
                                  }}
                                />
                              </div>
                              <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", minWidth: 32 }}>
                                {progress}%
                              </span>
                            </div>
                          </td>
                          <td>
                            <ScoreCircle score={run.average_score} />
                          </td>
                          <td style={{ color: "var(--text-muted)", fontSize: "0.8125rem" }}>
                            {new Date(run.created_at).toLocaleDateString()}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
