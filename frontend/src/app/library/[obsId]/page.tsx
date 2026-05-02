"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { api, type LibraryObservationDetail } from "@/lib/api";
import { Badge } from "@/components/Badge";

export default function LibraryDetailPage() {
  const { obsId } = useParams<{ obsId: string }>();
  const [obs, setObs] = useState<LibraryObservationDetail | null>(null);

  useEffect(() => {
    api.getLibraryObservation(obsId).then(setObs);
  }, [obsId]);

  if (!obs) return <div>Loading…</div>;

  return (
    <article className="space-y-4">
      <header>
        <div className="flex items-center gap-2 mb-1">
          <Badge tone={obs.severity as "urgent"}>{obs.severity}</Badge>
          <Badge tone={obs.confidence as "deterministic"}>{obs.confidence}</Badge>
          <span className="text-xs text-slate-500">
            {obs.id} · v{obs.version} · {obs.status}
          </span>
        </div>
        <h1 className="text-xl font-semibold">{obs.title}</h1>
        <div className="text-sm text-slate-600">
          {obs.category} / {obs.subcategory}
        </div>
      </header>

      <section>
        <h2 className="font-medium">Statement</h2>
        <p className="whitespace-pre-line text-sm bg-white border rounded p-3">{obs.statement}</p>
      </section>

      <section>
        <h2 className="font-medium">Logic (plain English)</h2>
        <pre className="whitespace-pre-wrap text-xs bg-white border rounded p-3">
          {obs.plain_english_logic}
        </pre>
      </section>

      <section>
        <h2 className="font-medium">Required inputs</h2>
        <ul className="text-sm bg-white border rounded p-3 list-disc pl-5">
          {(obs.required_inputs.transcript_types ?? []).map((t) => (
            <li key={t}>{t}</li>
          ))}
          {obs.required_inputs.min_tax_years ? (
            <li>Minimum tax years: {obs.required_inputs.min_tax_years}</li>
          ) : null}
          {(obs.required_inputs.facts ?? []).map((f) => (
            <li key={f}>fact: {f}</li>
          ))}
        </ul>
      </section>

      <section>
        <h2 className="font-medium">Discussion points</h2>
        <ul className="text-sm bg-white border rounded p-3 list-disc pl-5">
          {obs.discussion_points.map((dp, i) => (
            <li key={i}>{dp}</li>
          ))}
        </ul>
      </section>

      <section>
        <h2 className="font-medium">Sources</h2>
        <ul className="text-xs bg-white border rounded p-3 list-disc pl-5">
          {obs.sources.map((s, i) => (
            <li key={i}>
              {s.description} — {s.transcript_type} · {s.field_path}
            </li>
          ))}
        </ul>
      </section>

      {obs.caveats && (
        <section>
          <h2 className="font-medium">Caveats</h2>
          <p className="text-xs text-amber-800 bg-amber-50 border border-amber-200 rounded p-3">
            {obs.caveats}
          </p>
        </section>
      )}

      <section>
        <h2 className="font-medium">Disclaimers</h2>
        <p className="text-xs">{obs.disclaimers.join(", ")}</p>
      </section>

      <section>
        <h2 className="font-medium">Test cases</h2>
        <ul className="text-xs bg-white border rounded p-3 list-disc pl-5">
          {obs.test_cases.map((tc, i) => (
            <li key={i}>
              {tc.name} — expected_fires: {String(tc.expected_fires)}
            </li>
          ))}
        </ul>
      </section>
    </article>
  );
}
