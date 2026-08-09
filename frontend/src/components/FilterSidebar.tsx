import type { Company, JobFilters } from "../types";

interface Props {
  filters: JobFilters;
  onChange: (f: Partial<JobFilters>) => void;
  companies: Company[];
}

const quick: { label: string; patch: Partial<JobFilters> }[] = [
  { label: "🔥 Posted <1h", patch: { freshness_hours: 1 } },
  { label: "Today", patch: { freshness_hours: 24 } },
  { label: "90%+ matches", patch: { min_score: 90 } },
  { label: "80%+ matches", patch: { min_score: 80 } },
  { label: "Remote", patch: { remote: "remote" } },
  { label: "Not applied", patch: { status: "not_applied" } },
];

export default function FilterSidebar({ filters, onChange, companies }: Props) {
  const label = "text-[11px] uppercase tracking-wide text-muted font-medium mb-1 block";
  const field = "w-full bg-surface border border-line rounded-md px-2 py-1.5 text-sm";
  return (
    <aside className="w-56 shrink-0 space-y-4">
      <div className="flex flex-wrap gap-1.5">
        {quick.map((q) => (
          <button key={q.label} className="btn-ghost" onClick={() => onChange(q.patch)}>{q.label}</button>
        ))}
        <button
          className="btn-ghost text-muted"
          onClick={() => onChange({ q: "", company_id: undefined, min_score: undefined, freshness_hours: undefined, location: "", remote: "", experience_max: undefined, salary_min: undefined, source: "", status: "" })}
        >
          Clear all
        </button>
      </div>
      <div>
        <label className={label}>Keyword</label>
        <input className={field} placeholder="python, platform…" value={filters.q}
               onChange={(e) => onChange({ q: e.target.value })} />
      </div>
      <div>
        <label className={label}>Company</label>
        <select className={field} value={filters.company_id ?? ""}
                onChange={(e) => onChange({ company_id: e.target.value ? Number(e.target.value) : undefined })}>
          <option value="">All companies</option>
          {companies.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
      </div>
      <div>
        <label className={label}>Min match score</label>
        <input type="range" min={0} max={100} step={5} className="w-full accent-(--color-radar)"
               value={filters.min_score ?? 0} onChange={(e) => onChange({ min_score: Number(e.target.value) || undefined })} />
        <div className="font-mono text-xs text-muted">{filters.min_score ?? 0}%+</div>
      </div>
      <div>
        <label className={label}>Freshness</label>
        <select className={field} value={filters.freshness_hours ?? ""}
                onChange={(e) => onChange({ freshness_hours: e.target.value ? Number(e.target.value) : undefined })}>
          <option value="">Any age</option>
          <option value="1">Last hour</option>
          <option value="6">Last 6 hours</option>
          <option value="24">Last 24 hours</option>
          <option value="168">Last week</option>
        </select>
      </div>
      <div>
        <label className={label}>Location contains</label>
        <input className={field} placeholder="e.g. NC, Seattle, Remote" value={filters.location}
               onChange={(e) => onChange({ location: e.target.value })} />
      </div>
      <div>
        <label className={label}>Work mode</label>
        <select className={field} value={filters.remote} onChange={(e) => onChange({ remote: e.target.value })}>
          <option value="">Any</option>
          <option value="remote">Remote</option>
          <option value="hybrid">Hybrid</option>
          <option value="onsite">On-site</option>
        </select>
      </div>
      <div>
        <label className={label}>Max years required</label>
        <input type="number" className={field} min={0} max={15} placeholder="e.g. 6"
               value={filters.experience_max ?? ""}
               onChange={(e) => onChange({ experience_max: e.target.value ? Number(e.target.value) : undefined })} />
      </div>
      <div>
        <label className={label}>Min salary (max of range)</label>
        <input type="number" className={field} step={10000} placeholder="e.g. 150000"
               value={filters.salary_min ?? ""}
               onChange={(e) => onChange({ salary_min: e.target.value ? Number(e.target.value) : undefined })} />
      </div>
      <div>
        <label className={label}>ATS source</label>
        <select className={field} value={filters.source} onChange={(e) => onChange({ source: e.target.value })}>
          <option value="">Any source</option>
          <option value="greenhouse">Greenhouse</option>
          <option value="lever">Lever</option>
          <option value="ashby">Ashby</option>
          <option value="workday">Workday</option>
        </select>
      </div>
      <div>
        <label className={label}>Status</label>
        <select className={field} value={filters.status} onChange={(e) => onChange({ status: e.target.value })}>
          <option value="">Any status</option>
          <option value="not_applied">Not applied</option>
          {["New", "Saved", "Applied", "Interview", "Rejected", "Skip"].map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>
    </aside>
  );
}
