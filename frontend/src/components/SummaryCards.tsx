import type { Stats } from "../types";

export default function SummaryCards({ stats }: { stats: Stats | null }) {
  const cards = [
    { label: "Companies monitored", value: stats?.companies_monitored },
    { label: "New jobs today", value: stats?.new_jobs_today },
    { label: "Strong matches today", value: stats?.strong_matches_today, accent: true },
    { label: "Applications today", value: stats?.applications_today },
    { label: "Applications this week", value: stats?.applications_week },
  ];
  return (
    <div className="grid grid-cols-5 gap-3">
      {cards.map((c) => (
        <div key={c.label} className="bg-surface border border-line rounded-lg px-4 py-3">
          <div className={`font-mono text-2xl font-medium ${c.accent ? "text-radar" : ""}`}>{c.value ?? "–"}</div>
          <div className="text-xs text-muted mt-0.5">{c.label}</div>
        </div>
      ))}
    </div>
  );
}
