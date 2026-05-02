"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, type Client } from "@/lib/api";

export default function ClientsPage() {
  const [clients, setClients] = useState<Client[]>([]);
  const [name, setName] = useState("");
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    try {
      setClients(await api.listClients());
    } catch (e) {
      setError(String(e));
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  async function create(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    setCreating(true);
    try {
      await api.createClient(name.trim());
      setName("");
      await refresh();
    } catch (err) {
      setError(String(err));
    } finally {
      setCreating(false);
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-xl font-semibold">Clients</h1>
      </div>
      <form onSubmit={create} className="flex gap-2 mb-6">
        <input
          className="flex-1 border rounded px-3 py-2"
          placeholder="New client name (e.g., Smith Family)"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <button
          className="rounded bg-slate-900 text-white px-4 py-2 disabled:opacity-50"
          disabled={creating}
        >
          Create empty client
        </button>
      </form>
      {error && <div className="text-sm text-red-700 mb-4">{error}</div>}
      <ul className="divide-y rounded border bg-white">
        {clients.map((c) => (
          <li key={c.id} className="p-3">
            <Link href={`/clients/${c.id}`} className="font-medium hover:underline">
              {c.name}
            </Link>
            <div className="text-xs text-slate-500">{new Date(c.created_at).toLocaleString()}</div>
          </li>
        ))}
        {clients.length === 0 && (
          <li className="p-6 text-sm text-slate-500">No clients yet.</li>
        )}
      </ul>
    </div>
  );
}
