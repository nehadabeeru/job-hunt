import { fmtSalary, freshTier, timeAgo } from "../api";
import type { Job } from "../types";

interface Props {
  jobs: Job[];
  onOpen: (id: number) => void;
  onStatus: (id: number, status: string) => void;
  sort: string;
  onSort: (s: string) => void;
}

const tierStyle: Record<string, { dot: string; text: string; icon: string }> = {
  hot: { dot: "bg-hot text-hot", text: "text-hot", icon: "🔥" },
  fresh: { dot: "bg-fresh text-fresh", text: "text-fresh", icon: "🟢" },
  warm: { dot: "bg-warm text-warm", text: "text-warm", icon: "🟡" },
  stale: { dot: "bg-muted text-muted", text: "text-muted", icon: "⚪" },
};

function ScorePill({ score }: { score: number }) {
  const cls = score >= 90 ? "bg-radar text-white" : score >= 80 ? "bg-radar-soft text-radar" : score >= 60 ? "bg-paper text-ink border border-line" : "bg-paper text-muted border border-line";
  return <span className={`font-mono text-xs font-medium rounded px-1.5 py-0.5 ${cls}`}>{Math.round(score)}%</span>;
}

const statusCls: Record<string, string> = {
  New: "text-radar", Saved: "text-warm", Applied: "text-fresh",
  Interview: "text-fresh", Rejected: "text-muted line-through", Skip: "text-muted",
};

export default function JobsTable({ jobs, onOpen, onStatus, sort, onSort }: Props) {
  const th = "text-left text-[11px] uppercase tracking-wide text-muted font-medium px-2 py-2 select-none";
  const sortable = (key: string, label: string) => (
    <button className={`${sort === key ? "text-ink" : ""} hover:text-ink cursor-pointer uppercase tracking-wide`} onClick={() => onSort(key)}>
      {label}{sort === key ? " ↓" : ""}
    </button>
  );
  return (
    <table className="w-full bg-surface border border-line rounded-lg text-sm border-separate border-spacing-0 overflow-hidden">
      <thead className="bg-paper">
        <tr>
          <th className={th}>{sortable("newest", "Fresh")}</th>
          <th className={th}>{sortable("score", "Match")}</th>
          <th className={th}>{sortable("company", "Company")}</th>
          <th className={th}>Role</th>
          <th className={th}>Location</th>
          <th className={th}>{sortable("experience", "Exp")}</th>
          <th className={th}>{sortable("salary", "Salary")}</th>
          <th className={th}>Source</th>
          <th className={th}>Status</th>
          <th className={th}>Actions</th>
        </tr>
      </thead>
      <tbody>
        {jobs.map((j) => {
          const tier = freshTier(j.first_seen_at);
          const t = tierStyle[tier];
          return (
            <tr key={j.id} className="border-t border-line hover:bg-paper/60 cursor-pointer" onClick={() => onOpen(j.id)}>
              <td className="px-2 py-1.5 whitespace-nowrap border-t border-line">
                <span className={`inline-block w-2 h-2 rounded-full mr-1.5 align-middle ${t.dot} ${tier === "hot" ? "pulse-dot" : ""}`} />
                <span className={`font-mono text-xs ${t.text}`} title={`First detected ${timeAgo(j.first_seen_at)} ago`}>
                  {timeAgo(j.first_seen_at)}
                </span>
              </td>
              <td className="px-2 py-1.5 border-t border-line"><ScorePill score={j.match_score} /></td>
              <td className="px-2 py-1.5 font-medium whitespace-nowrap border-t border-line">{j.company_name}</td>
              <td className="px-2 py-1.5 border-t border-line">
                <span className="line-clamp-1">{j.title}</span>
                {j.is_demo && <span className="ml-1 text-[10px] font-mono bg-warm/15 text-warm rounded px-1 align-middle">DEMO</span>}
              </td>
              <td className="px-2 py-1.5 text-muted whitespace-nowrap max-w-40 truncate border-t border-line">
                {j.location || "—"}{j.remote_status === "remote" && <span className="ml-1 text-radar text-xs">R</span>}
              </td>
              <td className="px-2 py-1.5 font-mono text-xs text-muted whitespace-nowrap border-t border-line">
                {j.experience_min_years != null ? `${j.experience_min_years}+ yrs` : "—"}
              </td>
              <td className="px-2 py-1.5 font-mono text-xs whitespace-nowrap border-t border-line">{fmtSalary(j.salary_min, j.salary_max, j.salary_raw)}</td>
              <td className="px-2 py-1.5 text-xs text-muted capitalize border-t border-line">{j.ats_provider}</td>
              <td className={`px-2 py-1.5 text-xs font-medium border-t border-line ${statusCls[j.status] ?? ""}`}>{j.status}</td>
              <td className="px-2 py-1.5 whitespace-nowrap border-t border-line" onClick={(e) => e.stopPropagation()}>
                <a className="btn-primary mr-1" href={j.apply_url} target="_blank" rel="noreferrer"
                   onClick={() => setTimeout(() => onStatus(j.id, j.status), 0)}>Apply</a>
                <button className="btn-ghost mr-1" onClick={() => onStatus(j.id, "Applied")}>Applied</button>
                <button className="btn-ghost mr-1" onClick={() => onStatus(j.id, "Saved")}>Save</button>
                <button className="btn-ghost" onClick={() => onStatus(j.id, "Skip")}>Skip</button>
              </td>
            </tr>
          );
        })}
        {jobs.length === 0 && (
          <tr><td colSpan={10} className="px-4 py-10 text-center text-muted text-sm">
            No jobs match these filters yet. Add companies on the Companies page, then enable polling or press "Poll now".
          </td></tr>
        )}
      </tbody>
    </table>
  );
}
