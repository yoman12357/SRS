export type Json =
  | string
  | number
  | boolean
  | null
  | Json[]
  | { [key: string]: Json };
export interface Question {
  id: string;
  question: string;
  why_needed: string;
  critical: boolean;
}
export interface Analysis {
  title: string;
  domain: string;
  summary: string;
  supported: boolean;
  questions: Question[];
  unresolved_decisions: string[];
  stakeholders?: string[];
  assessments?: {
    evidence_id: string;
    kind: string;
    sections: string[];
    explanation: string;
  }[];
}
export interface Project {
  id: string;
  name: string;
  description: string;
  analysis: Analysis | null;
  answers: { question_id: string; text: string; skipped: boolean }[];
}
export interface Summary {
  id: string;
  name: string;
  description: string;
  updated_at: string;
}
export interface Run {
  id: string;
  input_hash?: string;
  kind: string;
  status: string;
  error: string | null;
  created_at?: string;
  updated_at?: string;
  events: {
    agent: string;
    state: string;
    elapsed_seconds?: number;
    at?: string;
    reused?: boolean;
    budget_seconds?: number;
    retrieval_warning?: string | null;
  }[];
  checkpoints: Record<string, Json>;
}
export interface VersionSummary {
  id: string;
  sequence: number;
  content_hash: string;
  created_at: string;
}
export interface Version extends VersionSummary {
  content: Record<string, Json>;
  presentation?: SRSPresentation;
  quality: {
    status: string;
    checks_passed: number;
    checks_total: number;
    findings: {
      code: string;
      severity: string;
      section: string;
      item_id: string;
      message: string;
    }[];
    traceability: Json[];
  };
}
export interface Review {
  id: string;
  reviewer: string;
  decision: string;
  comment: string;
  content_hash: string;
  created_at: string;
}
export interface ReportRequirement {
  id: string;
  statement: string;
  priority: string;
  basis: string;
  sources: { chunk_id: string; quote: string }[];
  evidence_ids: string[];
  test_ids: string[];
}
export interface ReportSection {
  number: string;
  title: string;
  paragraphs: string[];
  bullets: string[];
  tables: { columns: string[]; rows: string[][] }[];
  requirements: ReportRequirement[];
}
export interface SRSPresentation {
  profile: string;
  title: string;
  sections: ReportSection[];
}
export interface Reference {
  id: string;
  name: string;
  sha256: string;
}

export const sections = [
  "introduction",
  "functional",
  "nonfunctional",
  "security",
  "data",
  "network",
  "compliance",
  "architecture",
  "threats",
  "risks",
  "scenarios",
  "verification",
  "glossary",
  "sdlc",
] as const;
const labels: Record<string, string> = {
  compliance: "Compliance & policy matrix",
  nonfunctional: "Non-functional requirements",
  functional: "Functional requirements",
  security: "Security, privacy & compliance",
  network: "Network & interfaces",
  data: "Data requirements",
  scenarios: "Stories & use cases",
  verification: "Verification & acceptance",
  sdlc: "SDLC & delivery workflow",
  evidence_ids: "Original evidence",
  sources: "Source citations",
  provenance: "AI drafting record",
  requested_model: "Requested model",
  actual_models_used: "Models that authored this draft",
  section_models: "Section authors",
  verification_pairs: "V-Model development and verification pairing",
  test_plan_deliverable: "Test plan created in the development phase",
  basis: "Requirement basis",
  then: "Expected outcome",
  when: "Action",
  given: "Preconditions",
  id: "Identifier",
  source_document_id: "Source document",
  sha256: "Source fingerprint",
  relevance_score: "Retrieval relevance",
};
export function label(key: string): string {
  return (
    labels[key] ??
    key.replaceAll("_", " ").replace(/^./, (c) => c.toUpperCase())
  );
}
export function isActive(run: Run | null): boolean {
  return !!run && ["queued", "running"].includes(run.status);
}
export function approved(reviews: Review[], version: Version | null): boolean {
  return (
    !!version &&
    version.quality.status !== "invalid" &&
    reviews.at(-1)?.decision === "approve" &&
    reviews.at(-1)?.content_hash === version.content_hash
  );
}

export async function request<T>(
  path: string,
  method = "GET",
  data?: unknown,
): Promise<T> {
  const response = await fetch(`/api/v1${path}`, {
    method,
    headers:
      data instanceof FormData ? {} : { "Content-Type": "application/json" },
    body:
      data === undefined
        ? undefined
        : data instanceof FormData
          ? data
          : JSON.stringify(data),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => null);
    const detail = error?.detail;
    throw new Error(
      typeof detail?.message === "string"
        ? detail.message
        : `Request failed (${response.status}). Check your input and retry.`,
    );
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}
