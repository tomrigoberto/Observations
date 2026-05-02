const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${text}`);
  }
  return res.json();
}

export type Client = {
  id: string;
  name: string;
  created_at: string;
};

export type Member = {
  id: string;
  role: string;
  display_name: string;
  birth_year: number | null;
};

export type Entity = {
  id: string;
  entity_type: string;
  name: string;
};

export type Transcript = {
  id: string;
  member_id: string | null;
  entity_id: string | null;
  transcript_type: string;
  tax_year: number;
  source_filename: string;
  parse_status: string;
  parse_error: string | null;
  uploaded_at: string;
};

export type AnalysisRun = {
  id: string;
  rule_pack_version: string;
  status: string;
  started_at: string;
  completed_at: string | null;
  coverage: { tax_years?: number[]; label?: string } | null;
};

export type ObservationResult = {
  id: string;
  observation_id: string;
  observation_version: string;
  title: string;
  category: string;
  subcategory: string;
  severity: string;
  confidence: string;
  fired: boolean;
  captured_vars: Record<string, unknown>;
  statement_rendered: string;
  discussion_points: string[];
  sources_rendered: { description: string; transcript_type: string; field_path: string; tax_year: string }[];
  caveats: string | null;
  disclaimers: string[];
  pinned_to_summary: boolean;
  dismissed: boolean;
  suppressed: boolean;
};

export type LibraryObservationSummary = {
  id: string;
  title: string;
  category: string;
  subcategory: string;
  severity: string;
  confidence: string;
  status: string;
  version: string;
  audience_tags: string[];
};

export type LibraryObservationDetail = LibraryObservationSummary & {
  statement: string;
  discussion_points: string[];
  plain_english_logic: string;
  required_inputs: { transcript_types?: string[]; min_tax_years?: number; facts?: string[] };
  sources: { description: string; transcript_type: string; field_path: string; tax_year?: string | number }[];
  caveats: string | null;
  disclaimers: string[];
  test_cases: { name: string; fixture: string; expected_fires: boolean; expected_capture?: Record<string, unknown> }[];
  metadata: Record<string, unknown>;
};

export const api = {
  listClients: () => request<Client[]>("/clients"),
  createClient: (name: string) =>
    request<Client>("/clients", { method: "POST", body: JSON.stringify({ name }) }),
  getClient: (id: string) => request<Client>(`/clients/${id}`),
  listMembers: (id: string) => request<Member[]>(`/clients/${id}/members`),
  addMember: (id: string, body: { role: string; display_name: string; birth_year?: number | null }) =>
    request<Member>(`/clients/${id}/members`, { method: "POST", body: JSON.stringify(body) }),
  listEntities: (id: string) => request<Entity[]>(`/clients/${id}/entities`),
  addEntity: (id: string, body: { entity_type: string; name: string }) =>
    request<Entity>(`/clients/${id}/entities`, { method: "POST", body: JSON.stringify(body) }),
  coverage: (id: string) =>
    request<{ matrix: Record<string, Record<string, Record<string, { id: string; parse_status: string }>>>; tax_years: number[]; coverage_label: string }>(`/clients/${id}/coverage`),
  uploadTranscript: async (
    clientId: string,
    body: { member_id?: string; entity_id?: string; transcript_type: string; tax_year: number; file: File },
  ): Promise<Transcript> => {
    const fd = new FormData();
    fd.append("client_id", clientId);
    if (body.member_id) fd.append("member_id", body.member_id);
    if (body.entity_id) fd.append("entity_id", body.entity_id);
    fd.append("transcript_type", body.transcript_type);
    fd.append("tax_year", String(body.tax_year));
    fd.append("file", body.file);
    const res = await fetch(`${API_BASE}/transcripts`, { method: "POST", body: fd });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },
  listRuns: (clientId: string) =>
    request<AnalysisRun[]>(`/clients/${clientId}/analysis`),
  triggerAnalysis: (clientId: string) =>
    request<AnalysisRun>(`/clients/${clientId}/analysis`, { method: "POST" }),
  getRun: (clientId: string, runId: string) =>
    request<AnalysisRun>(`/clients/${clientId}/analysis/${runId}`),
  listResults: (clientId: string, runId: string) =>
    request<ObservationResult[]>(`/clients/${clientId}/analysis/${runId}/results`),
  pinResult: (clientId: string, runId: string, resultId: string) =>
    request<{ pinned: boolean }>(
      `/clients/${clientId}/analysis/${runId}/results/${resultId}/pin`,
      { method: "POST" },
    ),
  listLibrary: (params?: { category?: string; severity?: string; q?: string }) => {
    const q = new URLSearchParams();
    if (params?.category) q.set("category", params.category);
    if (params?.severity) q.set("severity", params.severity);
    if (params?.q) q.set("q", params.q);
    const qs = q.toString();
    return request<LibraryObservationSummary[]>(`/library${qs ? `?${qs}` : ""}`);
  },
  getLibraryObservation: (id: string) =>
    request<LibraryObservationDetail>(`/library/${id}`),
  ruleP: () => request<{ version: string; observation_count: number; pattern_count: number; by_category: Record<string, number>; library_path: string }>("/library/_meta/info"),
};
