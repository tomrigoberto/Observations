type Tone = "urgent" | "risk" | "opportunity" | "informational" | "deterministic" | "inferential" | "speculative" | "neutral";

const CLS: Record<Tone, string> = {
  urgent: "bg-red-100 text-red-800 border-red-200",
  risk: "bg-amber-100 text-amber-800 border-amber-200",
  opportunity: "bg-emerald-100 text-emerald-800 border-emerald-200",
  informational: "bg-slate-100 text-slate-800 border-slate-200",
  deterministic: "bg-blue-100 text-blue-800 border-blue-200",
  inferential: "bg-indigo-100 text-indigo-800 border-indigo-200",
  speculative: "bg-purple-100 text-purple-800 border-purple-200",
  neutral: "bg-slate-100 text-slate-800 border-slate-200",
};

export function Badge({ tone = "neutral", children }: { tone?: Tone; children: React.ReactNode }) {
  return (
    <span className={`inline-block text-[11px] uppercase tracking-wide rounded border px-1.5 py-0.5 ${CLS[tone]}`}>
      {children}
    </span>
  );
}
