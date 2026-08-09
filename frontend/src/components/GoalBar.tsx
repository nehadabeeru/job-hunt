import type { Stats } from "../types";

export default function GoalBar({ stats }: { stats: Stats | null }) {
  if (!stats) return null;
  const pct = Math.min(100, Math.round((stats.applications_today / stats.daily_goal) * 100));
  const f = stats.funnel;
  return (
    <div className="bg-surface border border-line rounded-lg px-4 py-3 flex items-center gap-6">
      <div className="flex-1">
        <div className="flex items-baseline justify-between mb-1.5">
          <span className="text-sm font-medium">
            Today's goal: <span className="font-mono">{stats.applications_today} / {stats.daily_goal}</span> applications
          </span>
          {stats.streak_days > 0 && (
            <span className="text-xs text-radar font-medium">{stats.streak_days}-day {stats.daily_goal}+ streak</span>
          )}
        </div>
        <div className="h-2 rounded-full bg-paper border border-line overflow-hidden">
          <div className="h-full bg-radar transition-all" style={{ width: `${pct}%` }} />
        </div>
      </div>
      <div className="text-xs text-muted font-mono whitespace-nowrap" title="Applications → Screens → Interviews → Offers">
        {f.applications} → {f.recruiter_screens} → {f.interviews} → {f.offers}
      </div>
    </div>
  );
}
