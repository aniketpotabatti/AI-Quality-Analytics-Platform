"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Sidebar from "@/components/layout/Sidebar";
import {
  getMe,
  listApiKeys,
  createApiKey,
  revokeApiKey,
  type ApiKeyResponse,
} from "@/lib/api-client";
import { getAccessToken } from "@/lib/api-client";

export default function SettingsPage() {
  const router = useRouter();
  const [wsId, setWsId] = useState<string | null>(null);
  const [keys, setKeys] = useState<ApiKeyResponse[]>([]);
  const [loading, setLoading] = useState(true);

  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState("");
  const [creating, setCreating] = useState(false);
  const [newKeySecret, setNewKeySecret] = useState<string | null>(null);

  useEffect(() => {
    const token = getAccessToken();
    if (!token) { router.push("/login"); return; }

    (async () => {
      try {
        const me = await getMe();
        const workspaceId = me.workspaces[0]?.workspace_id;
        if (!workspaceId) return;
        setWsId(workspaceId);
        const data = await listApiKeys(workspaceId);
        setKeys(data.items);
      } catch {
        // user might not be admin, handle error silently
      } finally {
        setLoading(false);
      }
    })();
  }, [router]);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!wsId || !newName.trim()) return;
    setCreating(true);
    try {
      const res = await createApiKey(wsId, { name: newName.trim(), expires_at: null });
      setKeys([res, ...keys]);
      setNewKeySecret(res.raw_key);
      setNewName("");
    } catch (err) {
      console.error(err);
    } finally {
      setCreating(false);
    }
  }

  async function handleRevoke(keyId: string) {
    if (!wsId) return;
    if (!confirm("Are you sure you want to revoke this API key?")) return;
    try {
      await revokeApiKey(wsId, keyId);
      setKeys(keys.filter(k => k.id !== keyId));
    } catch (err) {
      console.error(err);
    }
  }

  return (
    <div className="app-layout">
      <Sidebar />
      <main className="main-content">
        <div className="page-header">
          <h1 className="gradient-text" style={{ fontSize: "1.75rem", fontWeight: 800, marginBottom: 4 }}>
            Settings
          </h1>
          <p style={{ color: "var(--text-muted)", fontSize: "0.9375rem" }}>
            Manage your workspace and API keys
          </p>
        </div>

        <div className="page-content" style={{ maxWidth: 800 }}>
          <div className="card" style={{ marginBottom: "2rem" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.5rem" }}>
              <div>
                <h2 style={{ fontWeight: 600, fontSize: "1.125rem", color: "var(--text-primary)" }}>API Keys</h2>
                <p style={{ color: "var(--text-muted)", fontSize: "0.875rem" }}>
                  Keys are used to authenticate API requests from your backend.
                </p>
              </div>
              <button className="btn btn-primary" onClick={() => { setShowCreate(true); setNewKeySecret(null); }}>
                + Create Key
              </button>
            </div>

            {loading ? (
              <div className="skeleton" style={{ height: 100, borderRadius: 8 }} />
            ) : keys.length === 0 ? (
              <div style={{ padding: "2rem", textAlign: "center", background: "var(--bg-elevated)", borderRadius: 8 }}>
                <p style={{ color: "var(--text-muted)", fontSize: "0.875rem" }}>No active API keys found.</p>
              </div>
            ) : (
              <div className="table-container">
                <table>
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Prefix</th>
                      <th>Created</th>
                      <th style={{ textAlign: "right" }}>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {keys.map(k => (
                      <tr key={k.id}>
                        <td style={{ fontWeight: 500, color: "var(--text-primary)" }}>{k.name}</td>
                        <td style={{ fontFamily: "monospace", color: "var(--brand-300)" }}>{k.key_prefix}...</td>
                        <td>{new Date(k.created_at).toLocaleDateString()}</td>
                        <td style={{ textAlign: "right" }}>
                          <button onClick={() => handleRevoke(k.id)} style={{ background: "none", border: "none", color: "var(--red)", cursor: "pointer", fontSize: "0.8125rem", fontWeight: 500 }}>
                            Revoke
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {showCreate && (
            <div
              style={{
                position: "fixed", inset: 0, background: "rgba(0,0,0,0.6)",
                display: "flex", alignItems: "center", justifyContent: "center",
                zIndex: 100, backdropFilter: "blur(4px)",
              }}
            >
              <div className="card animate-slide-in" style={{ width: "100%", maxWidth: 480, padding: "2rem" }}>
                <h2 style={{ fontWeight: 700, fontSize: "1.125rem", marginBottom: "1.5rem" }}>Create API Key</h2>
                
                {newKeySecret ? (
                  <div>
                    <div style={{ padding: "1rem", background: "rgba(16,185,129,0.1)", border: "1px solid rgba(16,185,129,0.2)", borderRadius: 8, marginBottom: "1.5rem" }}>
                      <p style={{ color: "var(--green)", fontSize: "0.875rem", marginBottom: "0.75rem", fontWeight: 500 }}>
                        Key created successfully! Please copy it now. You won't be able to see it again.
                      </p>
                      <code style={{ display: "block", padding: "0.75rem", background: "var(--bg-base)", borderRadius: 4, color: "var(--text-primary)", fontSize: "0.875rem", wordBreak: "break-all" }}>
                        {newKeySecret}
                      </code>
                    </div>
                    <button type="button" className="btn btn-primary" style={{ width: "100%" }} onClick={() => { setShowCreate(false); setNewKeySecret(null); }}>
                      Done
                    </button>
                  </div>
                ) : (
                  <form onSubmit={handleCreate} style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                    <div>
                      <label className="label">Key Name</label>
                      <input
                        className="input"
                        placeholder="e.g. Production Backend"
                        value={newName}
                        onChange={e => setNewName(e.target.value)}
                        required
                        autoFocus
                      />
                    </div>
                    <div style={{ display: "flex", gap: "0.75rem", justifyContent: "flex-end", marginTop: "1rem" }}>
                      <button type="button" className="btn btn-ghost" onClick={() => setShowCreate(false)}>Cancel</button>
                      <button type="submit" className="btn btn-primary" disabled={creating}>
                        {creating ? "Creating…" : "Create Key"}
                      </button>
                    </div>
                  </form>
                )}
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
