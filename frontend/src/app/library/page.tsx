"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, type LibraryObservationSummary } from "@/lib/api";
import { Badge } from "@/components/Badge";

export default function LibraryPage() {
  const [items, setItems] = useState<LibraryObservationSummary[]>([]);
  const [info, setInfo] = useState<Awaited<ReturnType<typeof api.ruleP>> | null>(null);
  const [filter, setFilter] = useState<{ category?: string; severity?: string; q?: string }>({});

  async function refresh() {
    setItems(await api.listLibrary(filter));
  }
  useEffect(() => {
    refresh();
  }, [filter.category, filter.severity, filter.q]);
  useEffect(() => {
    api.ruleP().then(setInfo);
  }, []);

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-xl font-semibold">Observation library</h1>
        {info && (
          <div className="text-xs text-slate-500">
            {info.observation_count} observations · {info.pattern_count} patterns · rule pack {info.version}
          </div>
        )}
      </div>
      <div className="flex gap-2 mb-4 text-sm">
        <input
          className="flex-1 border rounded px-2 py-1"
          placeholder="Search by ID or title"
          value={filter.q ?? ""}
          onChange={(e) => setFilter({ ...filter, q: e.target.value || undefined })}
        />
        <select
          className="border rounded px-2 py-1"
          value={filter.category ?? ""}
          onChange={(e) => setFilter({ ...filter, category: e.target.value || undefined })}
        >
          <option value="">All categories</option>
          <option value="life_events">life_events</option>
          <option value="tax">tax</option>
          <option value="financial">financial</option>
          <option value="estate">estate</option>
        </select>
        <select
          className="border rounded px-2 py-1"
          value={filter.severity ?? ""}
          onChange={(e) => setFilter({ ...filter, severity: e.target.value || undefined })}
        >
          <option value="">All severities</option>
          <option value="urgent">urgent</option>
          <option value="risk">risk</option>
          <option value="opportunity">opportunity</option>
          <option value="informational">informational</option>
        </select>
      </div>
      <ul className="divide-y rounded border bg-white">
        {items.map((o) => (
          <li key={o.id} className="p-3 text-sm">
            <div className="flex items-center gap-2">
              <Badge tone={o.severity as "urgent"}>{o.severity}</Badge>
              <Badge tone={o.confidence as "deterministic"}>{o.confidence}</Badge>
              <Link href={`/library/${o.id}`} className="font-medium hover:underline">
                {o.title}
              </Link>
              <span className="ml-auto text-xs text-slate-500">
                {o.id} · {o.category}/{o.subcategory} · v{o.version}
              </span>
            </div>
          </li>
        ))}
        {items.length === 0 && (
          <li className="p-6 text-sm text-slate-500">No observations match your filters.</li>
        )}
      </ul>
    </div>
  );
}
