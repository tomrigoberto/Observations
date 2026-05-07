"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";
import { api, type Member } from "@/lib/api";

const TRANSCRIPT_TYPES = [
  "account_transcript",
  "return_transcript",
  "record_of_account",
  "wage_and_income",
  "verification_of_non_filing",
] as const;

const CURRENT_YEAR = new Date().getFullYear();

type Status = "pending" | "uploading" | "uploaded" | "failed";

type Item = {
  id: string;
  file: File;
  memberId: string;
  transcriptType: string;
  taxYear: number;
  status: Status;
  error?: string;
};

function autoDetectType(filename: string): string {
  const lower = filename.toLowerCase();
  if (lower.includes("wage") || /(^|[^a-z])wi([^a-z]|$)/.test(lower) || lower.includes("w&i"))
    return "wage_and_income";
  if (lower.includes("record") && lower.includes("account")) return "record_of_account";
  if (/(^|[^a-z])roa([^a-z]|$)/.test(lower)) return "record_of_account";
  if (lower.includes("non-filing") || lower.includes("nonfiling") || /(^|[^a-z])vnf([^a-z]|$)/.test(lower))
    return "verification_of_non_filing";
  if (lower.includes("return")) return "return_transcript";
  return "account_transcript";
}

function autoDetectYear(filename: string): number {
  const matches = filename.match(/(19|20)\d{2}/g);
  if (!matches) return CURRENT_YEAR - 1;
  for (const m of matches) {
    const y = parseInt(m, 10);
    if (y >= 2000 && y <= CURRENT_YEAR) return y;
  }
  return CURRENT_YEAR - 1;
}

function makeId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

export default function UploadPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [members, setMembers] = useState<Member[]>([]);
  const [items, setItems] = useState<Item[]>([]);
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [skipped, setSkipped] = useState<string[]>([]);

  // Bulk-set helpers
  const [bulkMember, setBulkMember] = useState<string>("");
  const [bulkType, setBulkType] = useState<string>("");
  const [bulkYear, setBulkYear] = useState<string>("");

  useEffect(() => {
    api.listMembers(id).then((ms) => {
      setMembers(ms);
      setBulkMember(ms[0]?.id ?? "");
    });
  }, [id]);

  function addFiles(files: File[]) {
    if (members.length === 0) return;
    const valid: File[] = [];
    const rejected: string[] = [];
    for (const f of files) {
      if (/\.html?$/i.test(f.name)) valid.push(f);
      else rejected.push(f.name);
    }
    if (rejected.length) setSkipped(rejected);
    if (!valid.length) return;

    const defaultMember = members[0]?.id ?? "";
    const newItems: Item[] = valid.map((f) => ({
      id: makeId(),
      file: f,
      memberId: defaultMember,
      transcriptType: autoDetectType(f.name),
      taxYear: autoDetectYear(f.name),
      status: "pending",
    }));
    setItems((prev) => [...prev, ...newItems]);
  }

  function onDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragOver(false);
    addFiles(Array.from(e.dataTransfer.files));
  }

  function onPick(e: React.ChangeEvent<HTMLInputElement>) {
    addFiles(Array.from(e.target.files ?? []));
    e.target.value = "";
  }

  function update(itemId: string, patch: Partial<Item>) {
    setItems((prev) => prev.map((i) => (i.id === itemId ? { ...i, ...patch } : i)));
  }

  function remove(itemId: string) {
    setItems((prev) => prev.filter((i) => i.id !== itemId));
  }

  function applyBulk() {
    setItems((prev) =>
      prev.map((i) => {
        if (i.status === "uploading" || i.status === "uploaded") return i;
        return {
          ...i,
          memberId: bulkMember || i.memberId,
          transcriptType: bulkType || i.transcriptType,
          taxYear: bulkYear ? Number(bulkYear) : i.taxYear,
        };
      }),
    );
  }

  async function uploadAll() {
    setUploading(true);
    const queue = items.filter((i) => i.status === "pending" || i.status === "failed");
    for (const item of queue) {
      update(item.id, { status: "uploading", error: undefined });
      try {
        await api.uploadTranscript(id, {
          member_id: item.memberId || undefined,
          transcript_type: item.transcriptType,
          tax_year: item.taxYear,
          file: item.file,
        });
        update(item.id, { status: "uploaded" });
      } catch (e) {
        update(item.id, { status: "failed", error: String(e) });
      }
    }
    setUploading(false);
  }

  const pendingCount = useMemo(
    () => items.filter((i) => i.status === "pending" || i.status === "failed").length,
    [items],
  );
  const allDone = items.length > 0 && items.every((i) => i.status === "uploaded");

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Upload transcripts</h1>
        <a
          href={`/clients/${id}`}
          className="text-sm text-slate-600 hover:text-slate-900"
        >
          ← Back to client
        </a>
      </div>

      {members.length === 0 && (
        <div className="rounded border bg-amber-50 border-amber-200 text-amber-900 px-3 py-2 text-sm">
          Add at least one household member before uploading transcripts.
        </div>
      )}

      <div
        onDragEnter={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={onDrop}
        onClick={() => fileInputRef.current?.click()}
        role="button"
        tabIndex={0}
        className={`rounded border-2 border-dashed p-8 text-center cursor-pointer transition-colors select-none ${
          dragOver
            ? "border-slate-900 bg-slate-100"
            : "border-slate-300 bg-white hover:bg-slate-50"
        } ${members.length === 0 ? "pointer-events-none opacity-50" : ""}`}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".html,.htm"
          className="hidden"
          onChange={onPick}
        />
        <div className="font-medium">Drag and drop transcript HTML files here</div>
        <div className="text-sm text-slate-500 mt-1">
          or click to choose multiple files. Member, type, and tax year are auto-detected from each filename and editable below.
        </div>
      </div>

      {skipped.length > 0 && (
        <div className="rounded border bg-amber-50 border-amber-200 text-amber-900 px-3 py-2 text-sm flex items-start">
          <div className="flex-1">
            <strong>Skipped {skipped.length} non-HTML file{skipped.length === 1 ? "" : "s"}:</strong>{" "}
            {skipped.join(", ")}
          </div>
          <button
            className="text-amber-900 hover:text-amber-700 ml-2"
            onClick={() => setSkipped([])}
            aria-label="dismiss"
          >
            ×
          </button>
        </div>
      )}

      {items.length > 0 && (
        <div className="rounded border bg-white">
          <div className="px-3 py-2 border-b flex items-center justify-between text-sm">
            <div>
              <span className="font-medium">{items.length}</span>
              <span className="text-slate-500">
                {" "}file{items.length === 1 ? "" : "s"} · {pendingCount} pending
              </span>
            </div>
            <button
              className="text-xs text-slate-600 hover:text-red-700"
              onClick={() => setItems([])}
              disabled={uploading}
            >
              Clear all
            </button>
          </div>

          <div className="px-3 py-2 border-b bg-slate-50 text-xs flex items-center gap-2 flex-wrap">
            <span className="text-slate-600 font-medium">Bulk set (applies to all not-yet-uploaded):</span>
            <select
              className="border rounded px-2 py-1"
              value={bulkMember}
              onChange={(e) => setBulkMember(e.target.value)}
            >
              <option value="">(member unchanged)</option>
              {members.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.display_name}
                </option>
              ))}
            </select>
            <select
              className="border rounded px-2 py-1"
              value={bulkType}
              onChange={(e) => setBulkType(e.target.value)}
            >
              <option value="">(type unchanged)</option>
              {TRANSCRIPT_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
            <input
              className="border rounded px-2 py-1 w-24"
              placeholder="year"
              type="number"
              value={bulkYear}
              onChange={(e) => setBulkYear(e.target.value)}
            />
            <button
              className="rounded border bg-white px-2 py-1 hover:bg-slate-100"
              onClick={applyBulk}
              disabled={uploading || !(bulkMember || bulkType || bulkYear)}
            >
              Apply
            </button>
          </div>

          <table className="w-full text-sm">
            <thead className="text-left text-slate-500 text-xs uppercase">
              <tr>
                <th className="px-3 py-2">File</th>
                <th className="px-3 py-2">Member</th>
                <th className="px-3 py-2">Transcript type</th>
                <th className="px-3 py-2">Tax year</th>
                <th className="px-3 py-2">Status</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {items.map((i) => {
                const locked = i.status === "uploading" || i.status === "uploaded";
                return (
                  <tr key={i.id} className="border-t align-middle">
                    <td className="px-3 py-2 max-w-[220px] truncate" title={i.file.name}>
                      <div className="font-mono text-xs">{i.file.name}</div>
                      <div className="text-[10px] text-slate-400">
                        {(i.file.size / 1024).toFixed(0)} KB
                      </div>
                    </td>
                    <td className="px-3 py-2">
                      <select
                        className="border rounded px-2 py-1 w-full"
                        value={i.memberId}
                        onChange={(e) => update(i.id, { memberId: e.target.value })}
                        disabled={locked}
                      >
                        {members.map((m) => (
                          <option key={m.id} value={m.id}>
                            {m.display_name}
                          </option>
                        ))}
                      </select>
                    </td>
                    <td className="px-3 py-2">
                      <select
                        className="border rounded px-2 py-1 w-full"
                        value={i.transcriptType}
                        onChange={(e) => update(i.id, { transcriptType: e.target.value })}
                        disabled={locked}
                      >
                        {TRANSCRIPT_TYPES.map((t) => (
                          <option key={t} value={t}>
                            {t}
                          </option>
                        ))}
                      </select>
                    </td>
                    <td className="px-3 py-2">
                      <input
                        type="number"
                        className="border rounded px-2 py-1 w-24"
                        value={i.taxYear}
                        onChange={(e) => update(i.id, { taxYear: Number(e.target.value) })}
                        disabled={locked}
                      />
                    </td>
                    <td className="px-3 py-2 text-xs whitespace-nowrap">
                      {i.status === "pending" && <span className="text-slate-500">queued</span>}
                      {i.status === "uploading" && (
                        <span className="text-blue-600">uploading…</span>
                      )}
                      {i.status === "uploaded" && (
                        <span className="text-emerald-700">✓ uploaded</span>
                      )}
                      {i.status === "failed" && (
                        <span className="text-red-700" title={i.error}>
                          ✗ failed
                        </span>
                      )}
                    </td>
                    <td className="px-3 py-2 text-right">
                      {!locked && (
                        <button
                          onClick={() => remove(i.id)}
                          className="text-xs text-slate-500 hover:text-red-700"
                        >
                          remove
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>

          {items.some((i) => i.error) && (
            <div className="border-t p-3 text-xs text-red-700 bg-red-50">
              <div className="font-medium mb-1">Upload errors</div>
              <ul className="list-disc pl-5">
                {items
                  .filter((i) => i.error)
                  .map((i) => (
                    <li key={i.id}>
                      <span className="font-mono">{i.file.name}</span>: {i.error}
                    </li>
                  ))}
              </ul>
            </div>
          )}
        </div>
      )}

      <div className="flex gap-2">
        <button
          onClick={uploadAll}
          disabled={uploading || pendingCount === 0 || members.length === 0}
          className="rounded bg-slate-900 text-white px-4 py-2 disabled:opacity-50"
        >
          {uploading
            ? "Uploading…"
            : `Upload ${pendingCount} file${pendingCount === 1 ? "" : "s"}`}
        </button>
        {allDone && (
          <button
            onClick={() => router.push(`/clients/${id}`)}
            className="rounded border bg-white px-4 py-2 hover:bg-slate-50"
          >
            Done — back to client
          </button>
        )}
      </div>
    </div>
  );
}
