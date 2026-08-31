"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { login, register, setTokens } from "@/lib/api-client";

type Mode = "login" | "register";

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<Mode>("login");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const [form, setForm] = useState({
    email: "",
    password: "",
    full_name: "",
    workspace_name: "",
  });

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    setForm({ ...form, [e.target.name]: e.target.value });
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      let tokens;
      if (mode === "login") {
        tokens = await login({ email: form.email, password: form.password });
      } else {
        tokens = await register({
          email: form.email,
          password: form.password,
          full_name: form.full_name,
          workspace_name: form.workspace_name || "My Workspace",
        });
      }
      setTokens(tokens.access_token, tokens.refresh_token);
      router.push("/dashboard");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Authentication failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "var(--bg-base)",
        padding: "2rem",
        position: "relative",
        overflow: "hidden",
      }}
    >
      {/* Background decoration */}
      <div
        style={{
          position: "absolute",
          top: "20%",
          left: "50%",
          transform: "translateX(-50%)",
          width: 600,
          height: 600,
          borderRadius: "50%",
          background: "radial-gradient(circle, rgba(99,102,241,0.08) 0%, transparent 70%)",
          pointerEvents: "none",
        }}
      />

      <div className="animate-slide-in" style={{ width: "100%", maxWidth: 440, position: "relative" }}>
        {/* Logo */}
        <div style={{ textAlign: "center", marginBottom: "2.5rem" }}>
          <div
            style={{
              width: 56,
              height: 56,
              borderRadius: 16,
              background: "linear-gradient(135deg, #4f46e5, #818cf8)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              margin: "0 auto 1rem",
              boxShadow: "0 8px 24px rgba(99,102,241,0.4)",
            }}
          >
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" stroke="white" strokeWidth="2" />
            </svg>
          </div>
          <h1 style={{ fontSize: "1.5rem", fontWeight: 700, color: "var(--text-primary)", margin: 0 }}>
            Hallucination Analytics
          </h1>
          <p style={{ color: "var(--text-muted)", fontSize: "0.875rem", marginTop: 4 }}>
            {mode === "login" ? "Sign in to your workspace" : "Create your account"}
          </p>
        </div>

        {/* Card */}
        <div className="card" style={{ padding: "2rem" }}>
          {/* Mode toggle */}
          <div
            style={{
              display: "flex",
              background: "var(--bg-elevated)",
              borderRadius: 8,
              padding: 3,
              marginBottom: "1.5rem",
            }}
          >
            {(["login", "register"] as Mode[]).map((m) => (
              <button
                key={m}
                onClick={() => { setMode(m); setError(""); }}
                style={{
                  flex: 1,
                  padding: "0.4375rem",
                  borderRadius: 6,
                  border: "none",
                  background: mode === m ? "var(--bg-overlay)" : "transparent",
                  color: mode === m ? "var(--text-primary)" : "var(--text-muted)",
                  fontWeight: 500,
                  fontSize: "0.875rem",
                  cursor: "pointer",
                  transition: "all 0.15s",
                  fontFamily: "inherit",
                }}
              >
                {m === "login" ? "Sign In" : "Register"}
              </button>
            ))}
          </div>

          <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
            {mode === "register" && (
              <div>
                <label className="label">Full Name</label>
                <input
                  className="input"
                  type="text"
                  name="full_name"
                  placeholder="Ada Lovelace"
                  value={form.full_name}
                  onChange={handleChange}
                  required
                />
              </div>
            )}

            <div>
              <label className="label">Email</label>
              <input
                className="input"
                type="email"
                name="email"
                placeholder="you@company.com"
                value={form.email}
                onChange={handleChange}
                required
              />
            </div>

            <div>
              <label className="label">Password</label>
              <input
                className="input"
                type="password"
                name="password"
                placeholder="••••••••"
                value={form.password}
                onChange={handleChange}
                required
                minLength={8}
              />
            </div>

            {mode === "register" && (
              <div>
                <label className="label">Workspace Name</label>
                <input
                  className="input"
                  type="text"
                  name="workspace_name"
                  placeholder="Acme AI"
                  value={form.workspace_name}
                  onChange={handleChange}
                />
              </div>
            )}

            {error && (
              <div
                style={{
                  padding: "0.75rem 1rem",
                  borderRadius: 8,
                  background: "rgba(239,68,68,0.1)",
                  border: "1px solid rgba(239,68,68,0.2)",
                  color: "#f87171",
                  fontSize: "0.875rem",
                }}
              >
                {error}
              </div>
            )}

            <button
              type="submit"
              className="btn btn-primary"
              style={{ width: "100%", marginTop: "0.5rem", padding: "0.75rem" }}
              disabled={loading}
            >
              {loading ? (
                <>
                  <span className="animate-spin" style={{ display: "inline-block", width: 14, height: 14, border: "2px solid rgba(255,255,255,0.3)", borderTopColor: "white", borderRadius: "50%" }} />
                  {mode === "login" ? "Signing in…" : "Creating account…"}
                </>
              ) : (
                mode === "login" ? "Sign In" : "Create Account"
              )}
            </button>
          </form>
        </div>

        <p style={{ textAlign: "center", marginTop: "1.5rem", fontSize: "0.8125rem", color: "var(--text-muted)" }}>
          Hallucination Analytics Studio — Evaluate what your AI gets wrong
        </p>
      </div>
    </div>
  );
}
