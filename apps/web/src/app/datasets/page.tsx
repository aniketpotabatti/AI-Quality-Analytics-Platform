"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Sidebar from "@/components/layout/Sidebar";
import {
  getMe,
  listDatasets,
  createDataset,
  type DatasetResponse,
} from "@/lib/api-client";
import { getAccessToken } from "@/lib/api-client";
import Link from "next/link";

export default function DatasetsPage() {
  const router = useRouter();
  const [datasets, setDatasets] = useState<DatasetResponse[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [wsId, setWsId] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const token = getAccessToken();
    if (!token) { router.push("/login"); return; }

    (async () => {
      try {
        const me = await getMe();
        const workspaceId = me.workspaces[0]?.workspace_id;
        if (!workspaceId) { setLoading(false); return; }
        setWsId(workspaceId);
        const data = await listDatasets(workspaceId);
        setDatasets(data.items);
        setTotal(data.pagination.total);
      } catch {
        router.push("/login");
      } finally {
        setLoading(false);
      }
    })();
  }, [router]);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!wsId || !newName.trim()) return;
    setCreating(true);
    setError("");
    try {
      const ds = await createDataset(wsId, { name: newName.trim(), description: newDesc || undefined });
      setDatasets([ds, ...datasets]);
      setTotal(total + 1);
      setShowCreate(false);
      setNewName("");
      setNewDesc("");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to create dataset");
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="app-layout">
      <Sidebar />
      <main className="main-content">
        <div className="page-header">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
            <div>
              <h1 className="gradient-text" style={{ fontSize: "1.75rem", fontWeight: 800, marginBottom: 4 }}>
                Datasets
              </h1>
              <p style={{ color: "var(--text-muted)", fontSize: "0.9375rem" }}>
                {total} dataset{total !== 1 ? "s" : ""} in your workspace
              </p>
            </div>
            <button onClick={() => setShowCreate(true)} className="btn btn-primary">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <line x1="12" y1="5" x2="12" y2="19" />
                <line x1="5" y1="12" x2="19" y2="12" />
              </svg>
              New Dataset
            </button>
          </div>
        </div>

        <div className="page-content">
          {/* Create modal */}
          {showCreate && (
            <div
              style={{
                position: "fixed", inset: 0, background: "rgba(0,0,0,0.6)",
                display: "flex", alignItems: "center", justifyContent: "center",
                zIndex: 100, backdropFilter: "blur(4px)",
              }}
            >
              <div className="card animate-slide-in" style={{ width: "100%", maxWidth: 480, padding: "2rem" }}>
                <h2 style={{ fontWeight: 700, fontSize: "1.125rem", marginBottom: "1.5rem" }}>Create Dataset</h2>
                <form onSubmit={handleCreate} style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                  <div>
                    <label className="label">Dataset Name *</label>
                    <input
                      className="input"
                      placeholder="e.g. RAG QA Test Suite"
                      value={newName}
                      onChange={e => setNewName(e.target.value)}
                      required
                      autoFocus
                    />
                  </div>
                  <div>
                    <label className="label">Description</label>
                    <input
                      className="input"
                      placeholder="Optional description…"
                      value={newDesc}
                      onChange={e => setNewDesc(e.target.value)}
                    />
                  </div>
                  {error && (
                    <div style={{ padding: "0.75rem", borderRadius: 8, background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.2)", color: "#f87171", fontSize: "0.875rem" }}>
                      {error}
                    </div>
                  )}
                  <div style={{ display: "flex", gap: "0.75rem", justifyContent: "flex-end", marginTop: "0.5rem" }}>
                    <button type="button" className="btn btn-ghost" onClick={() => setShowCreate(false)}>Cancel</button>
                    <button type="submit" className="btn btn-primary" disabled={creating}>
                      {creating ? "Creating…" : "Create Dataset"}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}

          {loading ? (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "1rem" }}>
              {[1,2,3].map(i => (
                <div key={i} className="card">
                  <div className="skeleton" style={{ height: 20, marginBottom: 8, borderRadius: 8 }} />
                  <div className="skeleton" style={{ height: 14, width: "60%", borderRadius: 8 }} />
                </div>
              ))}
            </div>
          ) : datasets.length === 0 ? (
            <div className="card empty-state">
              <div className="empty-icon">🗄️</div>
              <h3 style={{ fontWeight: 600, marginBottom: "0.5rem" }}>No datasets yet</h3>
              <p style={{ color: "var(--text-muted)", marginBottom: "1.5rem", fontSize: "0.9375rem" }}>
                Create your first dataset to start adding test cases.
              </p>
              <button className="btn btn-primary" onClick={() => setShowCreate(true)}>
                Create Dataset
              </button>
            </div>
          ) : (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: "1rem" }}>
              {datasets.map(ds => (
                <Link
                  key={ds.id}
                  href={`/datasets/${ds.id}`}
                  style={{ textDecoration: "none" }}
                >
                  <div className="card" style={{ height: "100%", cursor: "pointer" }}>
                    <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: "0.75rem" }}>
                      <div
                        style={{
                          width: 40, height: 40, borderRadius: 10,
                          background: "linear-gradient(135deg, rgba(99,102,241,0.2), rgba(129,140,248,0.15))",
                          border: "1px solid rgba(99,102,241,0.2)",
                          display: "flex", alignItems: "center", justifyContent: "center",
                          fontSize: "1.125rem",
                        }}
                      >
                        🗄️
                      </div>
                      {ds.test_case_count != null && (
                        <span className="badge badge-pending">
                          {ds.test_case_count} cases
                        </span>
                      )}
                    </div>
                    <h3 style={{ fontWeight: 600, color: "var(--text-primary)", marginBottom: 4, fontSize: "1rem" }}>
                      {ds.name}
                    </h3>
                    {ds.description && (
                      <p style={{ fontSize: "0.8125rem", color: "var(--text-muted)", lineHeight: 1.5, marginBottom: "0.75rem" }}>
                        {ds.description}
                      </p>
                    )}
                    <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "auto" }}>
                      Created {new Date(ds.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
