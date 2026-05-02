"use client";

import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { api, type AnalysisRun, type ObservationResult } from "@/lib/api";
import { ObservationCard } from "@/components/ObservationCard";
import { Badge } from "@/components/Badge";

const SEVERITY_ORDER = ["urgent", "risk", "opportunity", "informational"];

export default function RunPage() {
  const { id, runId } = useParams<{ id: string; runId: string }>();
  const [run, setRun] = useState<AnalysisRun | null>(null);
  const [results, setResults] = useState<ObservationResult[]>([]);
  const [filter, setFilter] = useState<{ severity?: string; category?: string }>({});

  async function refresh() {
    const [r, rs] = await Promise.all([
      api.getRun(id, runId),
      api.listResults(id, runId),
    ]);
    setRun(r);
    setResults(rs);
  }

  useEffect(() => {
    refresh();
  }, [id, runId]);

  const filtered = useMemo(() => {
    return results.filter((r) => {
      if (filter.severity && r.severity !== filter.severity) return false;
      if (filter.category && r.category !== filter.category) return false;
      return true;
    });
  }, [results, filter]);

  const grouped = useMemo(() => {
    const m = new Map<string, ObservationResult[]>();
    for (const sev of SEVERITY_ORDER) m.set(sev, []);
    for (const r of filtered) {
      const list = m.get(r.severity) ?? [];
      list.push(r);
      m.set(r.severity, list);
    }
    return m;
  }, [filtered]);

  async function pin(resultId: string) {
    await api.pinResult(id, runId, resultId);
    refresh();
  }

  if (!run) return <div>Loading…</div>;

  const categories = Array.from(new Set(results.map((r) => r.category)));
  const pinnedCount = results.filter((r) => r.pinned_to_summary).length;

  return (
    <div className="space-y-4">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold">Analysis run</h1>
          <div className="text-sm text-slate-600">
            {run.coverage?.label} · rule pack {run.rule_pack_version} · {results.length} observations
            {pinnedCount > 0 && <> · {pinnedCount} pinned to summary</>}
          </div>
        </div>
        <div className="flex gap-2 text-sm">
          <a
            href={api.pdfUrl(id, runId, "summary")}
            target="_blank"
            rel="noreferrer"
            className="rounded border bg-white px-3 py-2 hover:bg-slate-50"
          >
            Exec summary PDF
          </a>
          <a
            href={api.pdfUrl(id, runId, "detail")}
            target="_blank"
            rel="noreferrer"
            className="rounded border bg-white px-3 py-2 hover:bg-slate-50"
          >
            Detailed report PDF
          </a>
        </div>
      </div>

      <div className="flex gap-2 text-sm">
        <select
          className="border rounded px-2 py-1"
          value={filter.severity ?? ""}
          onChange={(e) =>
            setFilter({ ...filter, severity: e.target.value || undefined })
          }
        >
          <option value="">All severities</option>
          {SEVERITY_ORDER.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
        <select
          className="border rounded px-2 py-1"
          value={filter.category ?? ""}
          onChange={(e) =>
            setFilter({ ...filter, category: e.target.value || undefined })
          }
        >
          <option value="">All categories</option>
          {categories.map((c) => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
      </div>

      {SEVERITY_ORDER.map((sev) => {
        const list = grouped.get(sev) ?? [];
        if (list.length === 0) return null;
        return (
          <section key={sev}>
            <div className="flex items-center gap-2 mb-2">
              <Badge tone={sev as "urgent"}>{sev}</Badge>
              <span className="text-sm text-slate-500">{list.length}</span>
            </div>
            {list.map((o) => (
              <ObservationCard key={o.id} obs={o} onPin={pin} />
            ))}
          </section>
        );
      })}

      {filtered.length === 0 && (
        <div className="text-sm text-slate-500">No observations matched.</div>
      )}
    </div>
  );
}
