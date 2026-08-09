import { useEffect, useState } from "react";
import { api, fmtSalary, timeAgo } from "../api";
import type { JobDetail as JD } from "../types";

interface Props {
  jobId: number;
  onClose: () => void;
  onStatus: (id: number, status: string) => void;
}

export default function JobDetail({ jobId, onClose, onStatus }: Props) {
  const [job, setJob] = useState<JD | null>(null);
  useEffect(() => {
    api.job(jobId).then(setJob).catch(() => setJob(null));
  }, [jobId]);
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  if (!job) return null;
  const ex = job.match_explanation;
  return (
    <div className="fixed inset-0 z-40" role="dialog" aria-modal="true">
      <div className="absolute inset-0 bg-ink/30" onClick={onClose} />
      <div className="absolute right-0 top-0 h-full w-[560px] max-w-full bg-surface border-l border-line overflow-y-auto p-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="text-xs text-muted">{job.company_name}{job.is_demo && <span className="ml-2 font-mono bg-warm/15 text-warm rounded px-1">DEMO DATA</span>}</div>
            <h2 className="font-display text-xl font-medium mt-0.5">{job.title}</h2>
            <div className="text-sm text-muted mt-1">
              {job.location || "Location unlisted"} · {fmtSalary(job.salary_min, job.salary_max, job.salary_raw)} ·
              first detected <span className="font-mono">{timeAgo(job.first_seen_at)}</span> ago
            </div>
            {job.source_url && <a className="text-xs text-radar underline" href={job.source_url} target="_blank" rel="noreferrer">View original posting</a>}
          </div>
          <div className="text-right shrink-0">
            <div className="font-mono text-3xl font-medium text-radar">{Math.round(job.match_score)}%</div>
            <div className="text-[11px] text-muted uppercase tracking-wide">match</div>
          </div>
        </div>

        <div className="flex gap-2 my-4">
          <a className="btn-primary !px-4 !py-2 !text-sm" href={job.apply_url} target="_blank" rel="noreferrer">Apply now</a>
          <button className="btn-ghost !px-4 !py-2 !text-sm" onClick={() => onStatus(job.id, "Applied")}>Mark applied</button>
          <button className="btn-ghost !px-4 !py-2 !text-sm" onClick={() => onStatus(job.id, "Saved")}>Save</button>
          <button className="btn-ghost !px-4 !py-2 !text-sm" onClick={() => onStatus(job.id, "Skip")}>Skip</button>
          <button className="btn-ghost !px-4 !py-2 !text-sm ml-auto" onClick={onClose}>Close</button>
        </div>

        <section className="mb-4">
          <h3 className="text-[11px] uppercase tracking-wide text-muted font-medium mb-1.5">Why this matches</h3>
          <div className="flex flex-wrap gap-1">
            {ex.matching_skills.map((s) => (
              <span key={s} className="text-xs bg-radar-soft text-radar rounded px-1.5 py-0.5">{s} ✓</span>
            ))}
            {ex.matching_skills.length === 0 && <span className="text-xs text-muted">No profile skills detected in this posting.</span>}
          </div>
        </section>

        <section className="mb-4">
          <h3 className="text-[11px] uppercase tracking-wide text-muted font-medium mb-1.5">Missing from your profile match</h3>
          <div className="flex flex-wrap gap-1">
            {ex.missing_skills.map((s) => (
              <span key={s} className="text-xs bg-paper border border-line text-muted rounded px-1.5 py-0.5">{s}</span>
            ))}
            {ex.missing_skills.length === 0 && <span className="text-xs text-muted">Nothing significant.</span>}
          </div>
        </section>

        <section className="mb-4">
          <h3 className="text-[11px] uppercase tracking-wide text-muted font-medium mb-1.5">Experience fit</h3>
          <p className="text-sm">{ex.experience.note}{ex.experience.required_raw ? ` (posting says "${ex.experience.required_raw}")` : ""}</p>
          {ex.title.block_hits.length > 0 && (
            <p className="text-xs text-hot mt-1">Down-ranked: title contains {ex.title.block_hits.join(", ")}</p>
          )}
        </section>

        <section className="mb-4">
          <h3 className="text-[11px] uppercase tracking-wide text-muted font-medium mb-1.5">Score breakdown</h3>
          <div className="space-y-1">
            {Object.entries(ex.components).map(([k, v]) => (
              <div key={k} className="flex items-center gap-2 text-xs">
                <span className="w-36 text-muted">{k.replace(/_/g, " ")}</span>
                <div className="flex-1 h-1.5 bg-paper border border-line rounded-full overflow-hidden">
                  <div className="h-full bg-radar" style={{ width: `${v * 100}%` }} />
                </div>
                <span className="font-mono w-8 text-right">{Math.round(v * 100)}</span>
              </div>
            ))}
          </div>
          <p className="text-[11px] text-muted mt-1">{ex.semantic_note}</p>
        </section>

        <section>
          <h3 className="text-[11px] uppercase tracking-wide text-muted font-medium mb-1.5">Job description</h3>
          <div className="text-sm whitespace-pre-wrap leading-relaxed text-ink/90">
            {job.description || "Description not captured for this source yet (Workday detail fetch lands in Phase 2)."}
          </div>
        </section>
      </div>
    </div>
  );
}
