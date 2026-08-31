"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Sidebar from "@/components/layout/Sidebar";
import {
  getMe,
  getDataset,
  listTestCases,
  type DatasetResponse,
  type TestCaseResponse,
} from "@/lib/api-client";
import { getAccessToken } from "@/lib/api-client";
import Link from "next/link";

export default function DatasetDetailPage() {
  const router = useRouter();
  const params = useParams();
  const datasetId = params.datasetId as string;

  const [wsId, setWsId] = useState<string | null>(null);
  const [dataset, setDataset] = useState<DatasetResponse | null>(null);
  const [testCases, setTestCases] = useState<TestCaseResponse[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<TestCaseResponse | null>(null);

  useEffect(() => {
    const token = getAccessToken();
    if (!token) { router.push("/login"); return; }

    (async () => {
      try {
        const me = await getMe();
        const workspaceId = me.workspaces[0]?.workspace_id;
        if (!workspaceId) return;
        setWsId(workspaceId);

        const [ds, tcs] = await Promise.all([
          getDataset(workspaceId, datasetId),
          listTestCases(workspaceId, datasetId),
        ]);
        setDataset(ds);
        setTestCases(tcs.items);
        setTotal(tcs.pagination.total);
      } catch {
        router.push("/datasets");
      } finally {
        setLoading(false);
      }
    })();
  }, [router, datasetId]);

  return (
    <div className="app-layout">
      <Sidebar />
      <main className="main-content">
        <div className="page-header">
          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "0.5rem" }}>
            <Link href="/datasets" style={{ color: "var(--text-muted)", textDecoration: "none", fontSize: "0.875rem" }}>
              ← Datasets
            </Link>
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
            <div>
              <h1 className="gradient-text" style={{ fontSize: "1.75rem", fontWeight: 800, marginBottom: 4 }}>
                {loading ? "Loading…" : dataset?.name}
              </h1>
              <p style={{ color: "var(--text-muted)", fontSize: "0.9375rem" }}>
                {total} test case{total !== 1 ? "s" : ""}
                {dataset?.description && ` · ${dataset.description}`}
              </p>
            </div>
            {wsId && (
              <Link
                href={`/evaluations/new?dataset_id=${datasetId}`}
                className="btn btn-primary"
              >
                ⚡ Run Evaluation
              </Link>
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
          ) : testCases.length === 0 ? (
            <div className="card empty-state">
              <div className="empty-icon">📝</div>
              <h3 style={{ fontWeight: 600, marginBottom: "0.5rem" }}>No test cases yet</h3>
              <p style={{ color: "var(--text-muted)", fontSize: "0.9375rem" }}>
                Use the API to bulk-upload test cases, or add them individually.
              </p>
            </div>
          ) : (
            <div style={{ display: "grid", gridTemplateColumns: selected ? "1fr 380px" : "1fr", gap: "1rem" }}>
              <div className="table-container">
                <table>
                  <thead>
                    <tr>
                      <th>#</th>
                      <th>Prompt</th>
                      <th>Response</th>
                      <th>Context</th>
                      <th>Ground Truth</th>
                    </tr>
                  </thead>
                  <tbody>
                    {testCases.map((tc, idx) => (
                      <tr
                        key={tc.id}
                        onClick={() => setSelected(selected?.id === tc.id ? null : tc)}
                        style={{
                          cursor: "pointer",
                          background: selected?.id === tc.id ? "rgba(99,102,241,0.08)" : undefined,
                        }}
                      >
                        <td style={{ color: "var(--text-muted)", fontSize: "0.8125rem", minWidth: 40 }}>
                          {tc.sort_order + 1}
                        </td>
                        <td style={{ maxWidth: 200, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", color: "var(--text-primary)" }}>
                          {tc.prompt}
                        </td>
                        <td style={{ maxWidth: 200, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                          {tc.response}
                        </td>
                        <td>
                          {tc.context ? (
                            <span style={{ color: "var(--green)", fontSize: "0.75rem" }}>✓</span>
                          ) : (
                            <span style={{ color: "var(--text-muted)", fontSize: "0.75rem" }}>—</span>
                          )}
                        </td>
                        <td>
                          {tc.ground_truth ? (
                            <span style={{ color: "var(--green)", fontSize: "0.75rem" }}>✓</span>
                          ) : (
                            <span style={{ color: "var(--text-muted)", fontSize: "0.75rem" }}>—</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {selected && (
                <div className="card animate-slide-in" style={{ position: "sticky", top: "1rem", maxHeight: "calc(100vh - 6rem)", overflowY: "auto" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "1rem" }}>
                    <h3 style={{ fontWeight: 600, fontSize: "0.9375rem" }}>Test Case Detail</h3>
                    <button onClick={() => setSelected(null)} style={{ background: "none", border: "none", color: "var(--text-muted)", cursor: "pointer", fontSize: "1.125rem" }}>×</button>
                  </div>

                  {[
                    { label: "Prompt", value: selected.prompt },
                    { label: "Response", value: selected.response },
                    { label: "Context", value: selected.context },
                    { label: "Ground Truth", value: selected.ground_truth },
                  ].map(f => f.value && (
                    <div key={f.label} style={{ marginBottom: "1rem" }}>
                      <div className="label">{f.label}</div>
                      <div style={{ background: "var(--bg-elevated)", borderRadius: 8, padding: "0.75rem", fontSize: "0.8125rem", lineHeight: 1.6, whiteSpace: "pre-wrap", color: "var(--text-secondary)" }}>
                        {f.value}
                      </div>
                    </div>
                  ))}

                  {selected.external_id && (
                    <div>
                      <div className="label">External ID</div>
                      <code style={{ fontSize: "0.8125rem", color: "var(--brand-400)" }}>{selected.external_id}</code>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
