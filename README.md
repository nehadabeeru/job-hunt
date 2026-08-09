# Job Radar

Near-real-time software engineering job discovery from company ATS systems
(Greenhouse, Lever, Ashby, Workday) — before postings go stale on LinkedIn.
Built for a 30-applications-per-day workflow.

## Quick start (Docker — recommended)

```bash
docker compose up --build
# seed the ~45-company starter watchlist:
docker compose exec api python -m app.seed
```

Open http://localhost:5173. The poller is on (`ENABLE_POLLING=true` in
docker-compose.yml); within a minute or two jobs stream in from seeded
Greenhouse/Lever/Ashby boards. Use **Companies → Poll now** to fetch one
company immediately.

## Quick start (no Docker)

```bash
cd backend
pip install -r requirements.txt
python -m app.seed                      # seed companies (SQLite by default)
ENABLE_POLLING=true uvicorn app.main:app --reload   # http://localhost:8000

cd ../frontend
npm install && npm run dev              # http://localhost:5173 (proxies /api)
```

## Real data vs demo data

The app never invents job data. Everything in the table comes from live ATS
fetches, except rows inserted by the optional demo script, which are flagged
`is_demo=true` and rendered with a **DEMO** badge:

```bash
python -m app.seed_demo          # insert 5 clearly-labeled demo rows
python -m app.seed_demo --clear  # remove them
```

The seeded board tokens in `backend/data/companies_seed.csv` are best-effort
well-known tokens. Companies switch ATS vendors; a wrong token surfaces as
`error: 404` in that company's Status column — fix the token or press
**Detect** (which reads the careers URL and re-identifies the ATS).

## How it works

- **Connectors** (`backend/app/connectors/`) implement one interface
  (`ATSConnector.get_jobs`). Greenhouse, Lever, and Ashby use their official
  public job-board APIs — no HTML scraping. Workday uses the CXS JSON endpoint
  that powers Workday's own career sites and needs a per-company endpoint
  (auto-filled by Detect when possible); keep its polling conservative and
  respect site terms. Adding a new ATS = one new file + one registry entry.
- **Scheduler** (`app/scheduler.py`): APScheduler tick finds due companies,
  fetches them concurrently (bounded semaphore), with retries, exponential
  backoff, per-company failure isolation, and failure-based interval backoff.
- **Ingestion** (`app/ingest.py`): normalize → dedupe (ATS job ID, fallback
  fingerprint of company+title+location+URL) → upsert. Reappearing jobs keep
  their identity unless meaningful fields changed (content hash + snapshots).
  Jobs that vanish from a board are marked inactive, not deleted.
- **Scoring** (`app/scoring.py`): hybrid 0–100 with configurable weights
  (skill overlap 35 / similarity 25 / title 15 / experience 10 / freshness 10 /
  location 5), priority-skill boosting, blocked-title hard down-rank, and a
  full per-job explanation. V1 similarity is lexical vs `resume_text` in
  preferences; Phase 3 swaps in embeddings behind the same interface.
  After editing preferences: `POST /api/jobs/rescore`.
- **Alerts**: rules like *score ≥ 85 AND first seen < 15 min*. The unique
  (alert, job) constraint guarantees no duplicate notifications. Browser
  channel = frontend polls `/api/alerts/events` and raises Notifications;
  email sends if SMTP is configured. New channels plug into `app/notify.py`.

## API surface

`/api/jobs` (filters: q, company_id, min_score, freshness_hours, location,
remote, experience_max, salary_min, source, status, sort, paging) ·
`/api/jobs/{id}` · `PATCH /api/jobs/{id}/status` · `POST /api/jobs/rescore` ·
`/api/companies` (+ `/detect`, `/poll`, `/import-csv`) · `/api/stats/summary` ·
`/api/alerts` (+ `/events`) · `/api/preferences` · `/api/applications`.
Interactive docs at http://localhost:8000/docs.

## Roadmap hooks already in place

- **Phase 2** — Ashby + Workday connectors: implemented. Scoring: implemented.
  Notifications: implemented (browser/email).
- **Phase 3** — Notion sync: config keys exist (`NOTION_TOKEN`,
  `NOTION_DATABASE_ID`); the sync job reads Saved/Applied jobs and writes to a
  Notion DB (the app stays the source of truth). Resume embeddings: replace
  the `semantic_similarity` component in `scoring.py`. Analytics: `applications`
  table already tracks stages for the conversion funnel.

## Notes on responsible polling

Default interval is 180s per company with backoff on failures and 429
handling. Greenhouse/Lever/Ashby endpoints are public APIs intended for job
boards; still, keep concurrency modest. For Workday and any scraped source,
check the site's terms and robots.txt, and prefer longer intervals.
