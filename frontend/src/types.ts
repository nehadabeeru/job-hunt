export interface Job {
  id: number;
  company_id: number;
  company_name: string;
  title: string;
  location: string;
  remote_status: string;
  employment_type: string;
  experience_raw: string;
  experience_min_years: number | null;
  salary_min: number | null;
  salary_max: number | null;
  salary_raw: string;
  technologies: string[];
  ats_provider: string;
  source_url: string;
  apply_url: string;
  first_seen_at: string;
  is_active: boolean;
  is_demo: boolean;
  match_score: number;
  status: string;
}

export interface JobDetail extends Job {
  description: string;
  requirements: string;
  preferred_qualifications: string;
  match_explanation: {
    matching_skills: string[];
    missing_skills: string[];
    experience: { required_raw: string; required_years: number | null; note: string };
    title: { boost_hits: string[]; block_hits: string[] };
    semantic_note: string;
    components: Record<string, number>;
  };
}

export interface Company {
  id: number;
  name: string;
  careers_url: string;
  ats_type: string;
  ats_identifier: string;
  enabled: boolean;
  poll_interval_seconds: number;
  last_checked_at: string | null;
  last_status: string;
  job_count: number;
}

export interface Stats {
  companies_monitored: number;
  new_jobs_today: number;
  strong_matches_today: number;
  applications_today: number;
  applications_week: number;
  applications_month: number;
  daily_goal: number;
  streak_days: number;
  funnel: { applications: number; recruiter_screens: number; interviews: number; offers: number };
}

export interface JobFilters {
  q: string;
  company_id?: number;
  min_score?: number;
  freshness_hours?: number;
  location: string;
  remote: string;
  experience_max?: number;
  salary_min?: number;
  source: string;
  status: string;
  sort: string;
}
