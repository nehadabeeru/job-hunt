import type { Company, Job, JobDetail, JobFilters, Stats } from "./types";

const BASE = "";

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(BASE + path, init);
  if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
  return res.json();
}

export const api = {
  stats: () => req<Stats>("/api/stats/summary"),
  jobs: (f: Partial<JobFilters>, page = 1) => {
    const p = new URLSearchParams();
    Object.entries(f).forEach(([k, v]) => {
      if (v !== undefined && v !== "" && v !== null) p.set(k, String(v));
    });
    p.set("page", String(page));
    return req<{ items: Job[]; total: number; page: number; page_size: number }>(`/api/jobs?${p}`);
  },
  job: (id: number) => req<JobDetail>(`/api/jobs/${id}`),
  setStatus: (id: number, status: string) =>
    req(`/api/jobs/${id}/status`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ status }) }),
  companies: () => req<Company[]>("/api/companies"),
  addCompany: (name: string, careers_url: string) =>
    req<Company>("/api/companies", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ name, careers_url }) }),
  pollCompany: (id: number) => req(`/api/companies/${id}/poll`, { method: "POST" }),
  detectCompany: (id: number) => req(`/api/companies/${id}/detect`, { method: "POST" }),
  importCsv: (file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return req<{ added: number; skipped_existing: number }>("/api/companies/import-csv", { method: "POST", body: fd });
  },
  alertEvents: () => req<{ id: number; job_id: number; title: string; score: number }[]>("/api/alerts/events"),
};

export function timeAgo(iso: string): string {
  const mins = Math.max(0, Math.round((Date.now() - new Date(iso).getTime()) / 60000));
  if (mins < 60) return `${mins}m`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h`;
  return `${Math.floor(hrs / 24)}d`;
}

export type FreshTier = "hot" | "fresh" | "warm" | "stale";
export function freshTier(iso: string): FreshTier {
  const hrs = (Date.now() - new Date(iso).getTime()) / 3600000;
  if (hrs < 1) return "hot";
  if (hrs < 6) return "fresh";
  if (hrs < 24) return "warm";
  return "stale";
}

export function fmtSalary(min: number | null, max: number | null, raw: string): string {
  const k = (n: number) => `$${Math.round(n / 1000)}K`;
  if (min && max) return `${k(min)}–${k(max)}`;
  if (raw) return raw.length > 18 ? raw.slice(0, 18) + "…" : raw;
  return "—";
}
