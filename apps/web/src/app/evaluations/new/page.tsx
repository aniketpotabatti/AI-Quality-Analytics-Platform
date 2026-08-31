"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Sidebar from "@/components/layout/Sidebar";
import {
  getMe,
  listDatasets,
  createEvaluationRun,
  type DatasetResponse,
} from "@/lib/api-client";
import { getAccessToken } from "@/lib/api-client";

const AVAILABLE_METRICS = [
  { id: "faithfulness", label: "Faithfulness", desc: "Response grounded in context?" },
  { id: "answer_relevance", label: "Answer Relevance", desc: "Response relevant to prompt?" },
  { id: "groundedness", label: "Groundedness", desc: "Matches ground truth?" },
  { id: "llm_as_judge", label: "LLM as Judge", desc: "Gemini 1.5 Flash quality score" },
];

export default function NewEvaluationPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const preselectedDatasetId = searchParams.get("dataset_id") ?? "";

  const [wsId, setWsId] = useState<string | null>(null);
  const [datasets, setDatasets] = useState<DatasetResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const [name, setName] = useState("");
  const [datasetId, setDatasetId] = useState(preselectedDatasetId);
  const [metrics, setMetrics] = useState<string[]>(["faithfulness", "answer_relevance", "groundedness"]);

  useEffect(() => {
    const token = getAccessToken();
    if (!token) { router.push("/login"); return; }

    (async () => {
      try {
        const me = await getMe();
        const workspaceId = me.workspaces[0]?.workspace_id;
        if (!workspaceId) return;
        setWsId(workspaceId);
        const data = await listDatasets(workspaceId);
        setDatasets(data.items);
        if (!datasetId && data.items[0]) {
          setDatasetId(data.items[0].id);
        }
      } catch {
        router.push("/login");
      } finally {
        setLoading(false);
      }
    })();
  }, [router]);

  function toggleMetric(id: string) {
    setMetrics(prev =>
      prev.includes(id) ? prev.filter(m => m !== id) : [...prev, id]
    );
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!wsId || !datasetId || metrics.length === 0) return;
    setSubmitting(true);
    setError("");

    const runName = name.trim() || `Evaluation ${new Date().toLocaleString()}`;

    try {
      const run = await createEvaluationRun(wsId, {
        name: runName,
        dataset_id: datasetId,
        metrics_config: { metrics },
      });
      router.push(`/evaluations/${run.id}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to create evaluation");
      setSubmitting(false);
    }
  }

  return (
    <div className="app-layout">
      <Sidebar />
      <main className="main-content">
        <div className="page-header">
          <div style={{ marginBottom: "0.5rem" }}>
            <button onClick={() => router.back()} style={{ background: "none", border: "none", color: "var(--text-muted)", cursor: "pointer", fontSize: "0.875rem", fontFamily: "inherit" }}>
              ← Back
            </button>
          </div>
          <h1 className="gradient-text" style={{ fontSize: "1.75rem", fontWeight: 800, marginBottom: 4 }}>
            New Evaluation Run
          </h1>
          <p style={{ color: "var(--text-muted)", fontSize: "0.9375rem" }}>
            Configure and start a hallucination evaluation
          </p>
        </div>

        <div className="page-content" style={{ maxWidth: 680 }}>
          {loading ? (
            <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
              {[1,2,3].map(i => (
                <div key={i} style={{ height: 80, borderRadius: 12 }} className="skeleton" />
              ))}
            </div>
          ) : (
            <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
              {/* Run Name */}
              <div className="card">
                <h2 style={{ fontWeight: 600, fontSize: "1rem", marginBottom: "1rem" }}>Run Details</h2>
                <div>
                  <label className="label">Run Name</label>
                  <input
                    className="input"
                    placeholder="e.g. Production QA — July 2025"
                    value={name}
                    onChange={e => setName(e.target.value)}
                  />
                  <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: 4 }}>
                    Leave blank for auto-generated name
                  </p>
                </div>
              </div>

              {/* Dataset */}
              <div className="card">
                <h2 style={{ fontWeight: 600, fontSize: "1rem", marginBottom: "1rem" }}>Dataset</h2>
                {datasets.length === 0 ? (
                  <p style={{ color: "var(--text-muted)", fontSize: "0.875rem" }}>
                    No datasets found. <a href="/datasets" style={{ color: "var(--brand-400)" }}>Create one first</a>.
                  </p>
                ) : (
                  <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                    {datasets.map(ds => (
                      <label
                        key={ds.id}
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: "0.75rem",
                          padding: "0.875rem",
                          borderRadius: 8,
                          border: `1px solid ${datasetId === ds.id ? "rgba(99,102,241,0.4)" : "var(--border)"}`,
                          background: datasetId === ds.id ? "rgba(99,102,241,0.06)" : "var(--bg-elevated)",
                          cursor: "pointer",
                          transition: "all 0.15s",
                        }}
                      >
                        <input
                          type="radio"
                          name="dataset"
                          value={ds.id}
                          checked={datasetId === ds.id}
                          onChange={() => setDatasetId(ds.id)}
                          style={{ accentColor: "var(--brand-500)" }}
                        />
                        <div>
                          <div style={{ fontWeight: 500, color: "var(--text-primary)", fontSize: "0.9375rem" }}>
                            {ds.name}
                          </div>
                          {ds.description && (
                            <div style={{ fontSize: "0.8125rem", color: "var(--text-muted)" }}>
                              {ds.description}
                            </div>
                          )}
                        </div>
                      </label>
                    ))}
                  </div>
                )}
              </div>

              {/* Metrics */}
              <div className="card">
                <h2 style={{ fontWeight: 600, fontSize: "1rem", marginBottom: "0.375rem" }}>Evaluation Metrics</h2>
                <p style={{ fontSize: "0.8125rem", color: "var(--text-muted)", marginBottom: "1rem" }}>
                  Select one or more metrics to evaluate your responses
                </p>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem" }}>
                  {AVAILABLE_METRICS.map(m => {
                    const active = metrics.includes(m.id);
                    return (
                      <button
                        key={m.id}
                        type="button"
                        onClick={() => toggleMetric(m.id)}
                        style={{
                          padding: "1rem",
                          borderRadius: 10,
                          border: `1px solid ${active ? "rgba(99,102,241,0.4)" : "var(--border)"}`,
                          background: active ? "rgba(99,102,241,0.08)" : "var(--bg-elevated)",
                          cursor: "pointer",
                          textAlign: "left",
                          transition: "all 0.15s",
                          fontFamily: "inherit",
                        }}
                      >
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                          <div style={{ fontWeight: 500, color: active ? "var(--brand-300)" : "var(--text-primary)", fontSize: "0.9375rem", marginBottom: 4 }}>
                            {m.label}
                          </div>
                          {active && (
                            <div style={{ width: 18, height: 18, borderRadius: "50%", background: "var(--brand-500)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
                              <svg width="10" height="10" viewBox="0 0 12 12" fill="none">
                                <path d="M2 6l3 3 5-5" stroke="white" strokeWidth="2" strokeLinecap="round" />
                              </svg>
                            </div>
                          )}
                        </div>
                        <div style={{ fontSize: "0.8125rem", color: "var(--text-muted)" }}>{m.desc}</div>
                      </button>
                    );
                  })}
                </div>
                {metrics.length === 0 && (
                  <p style={{ marginTop: "0.75rem", fontSize: "0.8125rem", color: "var(--red)" }}>
                    Select at least one metric
                  </p>
                )}
              </div>

              {error && (
                <div style={{ padding: "0.875rem 1rem", borderRadius: 8, background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.2)", color: "#f87171", fontSize: "0.875rem" }}>
                  {error}
                </div>
              )}

              <div style={{ display: "flex", gap: "0.75rem" }}>
                <button type="button" className="btn btn-ghost" onClick={() => router.back()}>
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={submitting || metrics.length === 0 || !datasetId}
                  style={{ flex: 1 }}
                >
                  {submitting ? "Starting evaluation…" : "⚡ Start Evaluation"}
                </button>
              </div>
            </form>
          )}
        </div>
      </main>
    </div>
  );
}
