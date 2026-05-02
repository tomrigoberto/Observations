"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api, type AnalysisRun, type Client, type Member, type Transcript } from "@/lib/api";

export default function ClientDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const id = params.id;

  const [client, setClient] = useState<Client | null>(null);
  const [members, setMembers] = useState<Member[]>([]);
  const [coverage, setCoverage] = useState<Awaited<ReturnType<typeof api.coverage>> | null>(null);
  const [runs, setRuns] = useState<AnalysisRun[]>([]);
  const [running, setRunning] = useState(false);
  const [memberDraft, setMemberDraft] = useState({ display_name: "", role: "primary_taxpayer", birth_year: "" });

  async function refresh() {
    const [c, m, cov, r] = await Promise.all([
      api.getClient(id),
      api.listMembers(id),
      api.coverage(id),
      api.listRuns(id),
    ]);
    setClient(c);
    setMembers(m);
    setCoverage(cov);
    setRuns(r);
  }

  useEffect(() => {
    refresh();
  }, [id]);

  async function addMember(e: React.FormEvent) {
    e.preventDefault();
    await api.addMember(id, {
      role: memberDraft.role,
      display_name: memberDraft.display_name,
      birth_year: memberDraft.birth_year ? Number(memberDraft.birth_year) : null,
    });
    setMemberDraft({ display_name: "", role: "primary_taxpayer", birth_year: "" });
    refresh();
  }

  async function runAnalysis() {
    setRunning(true);
    try {
      const run = await api.triggerAnalysis(id);
      router.push(`/clients/${id}/runs/${run.id}`);
    } finally {
      setRunning(false);
    }
  }

  if (!client) return <div>Loading…</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">{client.name}</h1>
        <div className="flex gap-2">
          <Link
            href={`/clients/${id}/upload`}
            className="rounded border px-3 py-2 text-sm bg-white"
          >
            Upload transcript
          </Link>
          <button
            className="rounded bg-slate-900 text-white px-3 py-2 text-sm disabled:opacity-50"
            disabled={running || members.length === 0}
            onClick={runAnalysis}
          >
            Run analysis
          </button>
        </div>
      </div>

      <section>
        <h2 className="font-medium mb-2">Household members</h2>
        <ul className="rounded border bg-white divide-y">
          {members.map((m) => (
            <li key={m.id} className="p-3 text-sm">
              <strong>{m.display_name}</strong>{" "}
              <span className="text-slate-500">({m.role}{m.birth_year ? `, b. ${m.birth_year}` : ""})</span>
            </li>
          ))}
          {members.length === 0 && (
            <li className="p-3 text-sm text-slate-500">No members. Add at least one before running analysis.</li>
          )}
        </ul>
        <form onSubmit={addMember} className="flex gap-2 mt-2 text-sm">
          <input
            className="flex-1 border rounded px-2 py-1"
            placeholder="Display name"
            value={memberDraft.display_name}
            onChange={(e) => setMemberDraft({ ...memberDraft, display_name: e.target.value })}
            required
          />
          <select
            className="border rounded px-2 py-1"
            value={memberDraft.role}
            onChange={(e) => setMemberDraft({ ...memberDraft, role: e.target.value })}
          >
            <option value="primary_taxpayer">primary_taxpayer</option>
            <option value="spouse">spouse</option>
            <option value="dependent">dependent</option>
          </select>
          <input
            className="w-24 border rounded px-2 py-1"
            placeholder="birth year"
            value={memberDraft.birth_year}
            onChange={(e) => setMemberDraft({ ...memberDraft, birth_year: e.target.value })}
          />
          <button className="rounded bg-slate-900 text-white px-3 py-1">Add</button>
        </form>
      </section>

      <section>
        <h2 className="font-medium mb-2">Input transparency</h2>
        <div className="rounded border bg-white p-3 text-sm">
          <div className="text-slate-700 mb-2">{coverage?.coverage_label}</div>
          {coverage && coverage.tax_years.length > 0 ? (
            <table className="w-full text-xs">
              <thead>
                <tr className="text-left text-slate-500">
                  <th className="py-1">Owner</th>
                  {coverage.tax_years.map((y) => (
                    <th key={y} className="py-1">{y}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {Object.entries(coverage.matrix).map(([owner, byYear]) => (
                  <tr key={owner} className="border-t">
                    <td className="py-1 font-mono text-[10px]">{owner.slice(0, 8)}…</td>
                    {coverage.tax_years.map((y) => (
                      <td key={y} className="py-1">
                        {byYear[y]
                          ? Object.keys(byYear[y])
                              .map((tt) => `${tt[0]}✓`)
                              .join(" ")
                          : "—"}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="text-slate-500">No transcripts uploaded yet.</div>
          )}
        </div>
      </section>

      <section>
        <h2 className="font-medium mb-2">Analysis runs</h2>
        <ul className="rounded border bg-white divide-y">
          {runs.map((r) => (
            <li key={r.id} className="p-3 text-sm flex items-center justify-between">
              <div>
                <Link href={`/clients/${id}/runs/${r.id}`} className="font-medium hover:underline">
                  Run {r.id.slice(0, 8)}…
                </Link>
                <div className="text-xs text-slate-500">
                  {new Date(r.started_at).toLocaleString()} · {r.coverage?.label}
                </div>
              </div>
              <span className="text-xs text-slate-600">rule pack {r.rule_pack_version}</span>
            </li>
          ))}
          {runs.length === 0 && (
            <li className="p-3 text-sm text-slate-500">No runs yet. Add members, upload transcripts, then run analysis.</li>
          )}
        </ul>
      </section>
    </div>
  );
}
