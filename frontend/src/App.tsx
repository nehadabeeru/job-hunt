import { useCallback, useEffect, useState } from "react";
import { api } from "./api";
import CompaniesPage from "./components/CompaniesPage";
import FilterSidebar from "./components/FilterSidebar";
import GoalBar from "./components/GoalBar";
import JobDetail from "./components/JobDetail";
import JobsTable from "./components/JobsTable";
import SummaryCards from "./components/SummaryCards";
import type { Company, Job, JobFilters, Stats } from "./types";

const emptyFilters: JobFilters = { q: "", location: "", remote: "", source: "", status: "", sort: "newest" };

export default function App() {
  const [tab, setTab] = useState<"dashboard" | "companies">("dashboard");
  const [stats, setStats] = useState<Stats | null>(null);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState<JobFilters>(emptyFilters);
  const [openJob, setOpenJob] = useState<number | null>(null);
  const [error, setError] = useState("");

  const loadStats = useCallback(() => { api.stats().then(setStats).catch((e) => setError(String(e))); }, []);
  const loadCompanies = useCallback(() => { api.companies().then(setCompanies).catch((e) => setError(String(e))); }, []);
  const loadJobs = useCallback(() => {
    api.jobs(filters, page).then((r) => { setJobs(r.items); setTotal(r.total); setError(""); })
      .catch((e) => setError(String(e)));
  }, [filters, page]);

  useEffect(() => { loadStats(); loadCompanies(); }, [loadStats, loadCompanies]);
  useEffect(() => { loadJobs(); }, [loadJobs]);

  // Light auto-refresh + browser-channel alert toasts.
  useEffect(() => {
    if ("Notification" in window && Notification.permission === "default") Notification.requestPermission();
    const t = setInterval(async () => {
      loadJobs(); loadStats();
      try {
        const events = await api.alertEvents();
        for (const ev of events) {
          if ("Notification" in window && Notification.permission === "granted") {
            new Notification(`Job Radar · ${Math.round(ev.score)}% match`, { body: ev.title });
          }
        }
      } catch { /* alerts are best-effort */ }
    }, 30000);
    return () => clearInterval(t);
  }, [loadJobs, loadStats]);

  const patchFilters = (patch: Partial<JobFilters>) => { setPage(1); setFilters((f) => ({ ...f, ...patch })); };
  const setStatus = async (id: number, status: string) => {
    await api.setStatus(id, status).catch((e) => setError(String(e)));
    loadJobs(); loadStats();
  };

  const pages = Math.max(1, Math.ceil(total / 50));

  return (
    <div className="min-h-screen">
      <header className="border-b border-line bg-surface">
        <div className="max-w-350 mx-auto px-6 py-3 flex items-center gap-6">
          <div>
            <h1 className="font-display text-lg font-bold leading-tight flex items-center gap-2">
              <span className="inline-block w-2.5 h-2.5 rounded-full bg-radar pulse-dot text-radar" />
              Job Radar
            </h1>
            <p className="text-xs text-muted">Find the right job before everyone else.</p>
          </div>
          <nav className="flex gap-1 ml-6">
            {(["dashboard", "companies"] as const).map((t) => (
              <button key={t}
                className={`px-3 py-1.5 rounded-md text-sm capitalize cursor-pointer ${tab === t ? "bg-radar-soft text-radar font-medium" : "text-muted hover:text-ink"}`}
                onClick={() => setTab(t)}>
                {t}
              </button>
            ))}
          </nav>
          {error && <span className="text-xs text-hot ml-auto max-w-96 truncate" title={error}>{error}</span>}
        </div>
      </header>

      <main className="max-w-350 mx-auto px-6 py-5 space-y-4">
        {tab === "dashboard" ? (
          <>
            <SummaryCards stats={stats} />
            <GoalBar stats={stats} />
            <div className="flex gap-5 items-start">
              <FilterSidebar filters={filters} onChange={patchFilters} companies={companies} />
              <div className="flex-1 min-w-0 space-y-2">
                <div className="flex items-center justify-between text-xs text-muted">
                  <span><span className="font-mono">{total}</span> jobs · sorted by {filters.sort === "newest" ? "newest detected" : filters.sort}</span>
                  <span className="flex gap-2 items-center">
                    <button className="btn-ghost" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>←</button>
                    <span className="font-mono">{page}/{pages}</span>
                    <button className="btn-ghost" disabled={page >= pages} onClick={() => setPage((p) => p + 1)}>→</button>
                  </span>
                </div>
                <JobsTable jobs={jobs} onOpen={setOpenJob} onStatus={setStatus}
                           sort={filters.sort} onSort={(s) => patchFilters({ sort: s })} />
              </div>
            </div>
          </>
        ) : (
          <CompaniesPage companies={companies} refresh={() => { loadCompanies(); loadStats(); }} />
        )}
      </main>

      {openJob !== null && (
        <JobDetail jobId={openJob} onClose={() => setOpenJob(null)}
                   onStatus={async (id, s) => { await setStatus(id, s); setOpenJob(null); }} />
      )}
    </div>
  );
}
