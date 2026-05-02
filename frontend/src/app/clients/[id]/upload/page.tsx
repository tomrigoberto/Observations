"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api, type Member } from "@/lib/api";

export default function UploadPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [members, setMembers] = useState<Member[]>([]);
  const [memberId, setMemberId] = useState<string>("");
  const [transcriptType, setTranscriptType] = useState("account_transcript");
  const [taxYear, setTaxYear] = useState<number>(new Date().getFullYear() - 1);
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.listMembers(id).then((ms) => {
      setMembers(ms);
      setMemberId(ms[0]?.id ?? "");
    });
  }, [id]);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      await api.uploadTranscript(id, {
        member_id: memberId || undefined,
        transcript_type: transcriptType,
        tax_year: taxYear,
        file,
      });
      router.push(`/clients/${id}`);
    } catch (err) {
      setError(String(err));
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="max-w-lg">
      <h1 className="text-xl font-semibold mb-4">Upload transcript</h1>
      <form onSubmit={submit} className="space-y-3">
        <label className="block text-sm">
          Member
          <select
            className="w-full border rounded px-2 py-1 mt-1"
            value={memberId}
            onChange={(e) => setMemberId(e.target.value)}
          >
            {members.map((m) => (
              <option key={m.id} value={m.id}>
                {m.display_name} ({m.role})
              </option>
            ))}
          </select>
        </label>
        <label className="block text-sm">
          Transcript type
          <select
            className="w-full border rounded px-2 py-1 mt-1"
            value={transcriptType}
            onChange={(e) => setTranscriptType(e.target.value)}
          >
            <option value="account_transcript">account_transcript</option>
            <option value="return_transcript">return_transcript</option>
            <option value="record_of_account">record_of_account</option>
            <option value="wage_and_income">wage_and_income</option>
            <option value="verification_of_non_filing">verification_of_non_filing</option>
          </select>
        </label>
        <label className="block text-sm">
          Tax year
          <input
            type="number"
            className="w-full border rounded px-2 py-1 mt-1"
            value={taxYear}
            onChange={(e) => setTaxYear(Number(e.target.value))}
          />
        </label>
        <label className="block text-sm">
          HTML file
          <input
            type="file"
            accept=".html,.htm"
            className="w-full mt-1"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          />
        </label>
        {error && <div className="text-sm text-red-700">{error}</div>}
        <button
          className="rounded bg-slate-900 text-white px-4 py-2 disabled:opacity-50"
          disabled={uploading || !file || !memberId}
        >
          Upload
        </button>
      </form>
    </div>
  );
}
