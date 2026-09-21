"use client";

import { useState, type FormEvent } from "react";
import { useAuth } from "../../lib/auth-context";

export default function LoginPage() {
  const { login } = useAuth();
  const [username, setUsername] = useState(""); const [password, setPassword] = useState("");
  const [error, setError] = useState(""); const [busy, setBusy] = useState(false);
  async function submit(event: FormEvent) {
    event.preventDefault(); setError(""); setBusy(true);
    try { await login(username, password); } catch (reason) { setError(reason instanceof Error ? reason.message : "Unable to sign in."); } finally { setBusy(false); }
  }
  return <main className="flex min-h-[calc(100vh-76px)] items-center justify-center bg-canvas px-6 py-12">
    <form onSubmit={submit} className="w-full max-w-md rounded-2xl bg-white p-8 shadow-soft">
      <p className="eyebrow">Welcome back</p><h1 className="mb-2 font-display text-4xl font-bold text-ink">Sign in</h1>
      <p className="mb-8 text-sm text-slate-500">Pick up where your team left off.</p>
      {error && <p className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-700" role="alert">{error}</p>}
      <label className="mb-4 block text-sm font-semibold text-ink">Username<input required value={username} onChange={e => setUsername(e.target.value)} className="mt-2 w-full rounded-lg border border-slate-200 px-3 py-3 outline-none focus:border-coral focus:ring-2 focus:ring-coral/20" /></label>
      <label className="mb-6 block text-sm font-semibold text-ink">Password<input required type="password" value={password} onChange={e => setPassword(e.target.value)} className="mt-2 w-full rounded-lg border border-slate-200 px-3 py-3 outline-none focus:border-coral focus:ring-2 focus:ring-coral/20" /></label>
      <button disabled={busy} className="w-full rounded-lg bg-ink px-4 py-3 font-bold text-white disabled:opacity-50">{busy ? "Signing in..." : "Sign in"}</button>
    </form>
  </main>;
}
