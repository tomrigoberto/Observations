"use client";

import { Badge } from "./Badge";
import type { ObservationResult } from "@/lib/api";

export function ObservationCard({
  obs,
  onPin,
}: {
  obs: ObservationResult;
  onPin?: (id: string) => void;
}) {
  const sev = obs.severity as "urgent" | "risk" | "opportunity" | "informational";
  const conf = obs.confidence as "deterministic" | "inferential" | "speculative";
  return (
    <div className="rounded border bg-white p-4 mb-3 shadow-sm">
      <div className="flex items-center gap-2 mb-2">
        <Badge tone={sev}>{obs.severity}</Badge>
        <Badge tone={conf}>{obs.confidence}</Badge>
        <span className="text-xs text-slate-500">
          {obs.observation_id} · v{obs.observation_version}
        </span>
        {onPin && obs.confidence !== "speculative" && (
          <button
            className="ml-auto text-xs text-slate-600 hover:text-slate-900"
            onClick={() => onPin(obs.id)}
          >
            {obs.pinned_to_summary ? "Unpin from summary" : "Pin to summary"}
          </button>
        )}
      </div>
      <h3 className="font-semibold">{obs.title}</h3>
      <p className="my-2">{obs.statement_rendered}</p>

      {obs.discussion_points.length > 0 && (
        <details className="mb-2">
          <summary className="cursor-pointer text-sm text-slate-700">
            Discussion points ({obs.discussion_points.length})
          </summary>
          <ul className="list-disc pl-5 mt-1 text-sm">
            {obs.discussion_points.map((dp, i) => (
              <li key={i}>{dp}</li>
            ))}
          </ul>
        </details>
      )}

      {obs.sources_rendered.length > 0 && (
        <details className="mb-2">
          <summary className="cursor-pointer text-sm text-slate-700">
            Sources ({obs.sources_rendered.length})
          </summary>
          <ul className="text-xs text-slate-600 list-disc pl-5 mt-1">
            {obs.sources_rendered.map((s, i) => (
              <li key={i}>
                {s.description} — {s.transcript_type} · {s.field_path} · tax year {s.tax_year}
              </li>
            ))}
          </ul>
        </details>
      )}

      {obs.caveats && (
        <div className="text-xs text-amber-800 bg-amber-50 border border-amber-200 rounded p-2 mb-2">
          <strong>Caveats:</strong> {obs.caveats}
        </div>
      )}

      {obs.disclaimers.length > 0 && (
        <div className="text-[11px] text-slate-500">
          Disclaimers: {obs.disclaimers.join(", ")}
        </div>
      )}
    </div>
  );
}
