"""OPTIONAL: insert clearly-labeled DEMO jobs so the UI is reviewable before
polling is enabled. Every row is created with is_demo=True and the UI shows a
DEMO badge on them. Live-fetched jobs never get this flag.
Run:    python -m app.seed_demo
Clear:  python -m app.seed_demo --clear
"""
import sys
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select

from .db import Base, SessionLocal, engine
from .dedupe import fingerprint
from .models import Company, Job
from .preferences import get_preferences
from .scoring import score_job

DEMO = [
    ("Stripe", "Backend Software Engineer, Payments Platform", "Seattle, WA", 8, 3,
     "$180,000 - $220,000", "We build distributed systems in Python and Java on AWS. You will design REST and GraphQL APIs, work with PostgreSQL, DynamoDB and Redis, ship microservices with Docker and Terraform, and operate event-driven pipelines on Kafka. Requirements: 3+ years of backend experience."),
    ("Databricks", "Software Engineer II - Data Platform", "Remote - US", 45, 4,
     "$160,000 - $200,000", "Python, distributed systems, AWS, Postgres, async processing, CI/CD. Requirements: 4+ years building data platforms. Preferred: GenAI, RAG, embeddings, OpenSearch."),
    ("Notion", "AI Platform Engineer", "San Francisco, CA", 130, 3,
     "$170,000 - $210,000", "Build GenAI features: LLM pipelines, RAG, embeddings, vector search with OpenSearch. Python, FastAPI, AWS Lambda, event-driven architecture. Requirements: 3+ years."),
    ("Plaid", "Staff Software Engineer, Infrastructure", "New York, NY", 300, 8,
     "$240,000 - $290,000", "Lead infrastructure strategy. Kubernetes, Go, gRPC. Requirements: 8+ years."),
    ("Cloudflare", "Distributed Systems Engineer", "Austin, TX", 60 * 26, 5,
     "$165,000 - $205,000", "Rust and Python services at global scale, distributed systems, Kafka-style messaging, Docker, Terraform. Requirements: 5+ years."),
]


def run():
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        if "--clear" in sys.argv:
            db.execute(delete(Job).where(Job.is_demo == True))
            db.commit()
            print("demo jobs cleared")
            return
        prefs = get_preferences(db)
        now = datetime.now(timezone.utc)
        added = 0
        for company_name, title, location, minutes_ago, years, salary, desc in DEMO:
            company = db.execute(select(Company).where(Company.name == company_name)).scalar_one_or_none()
            if not company:
                company = Company(name=company_name, ats_type="greenhouse", ats_identifier=company_name.lower())
                db.add(company)
                db.flush()
            first_seen = now - timedelta(minutes=minutes_ago)
            fields = {
                "title": title, "location": location, "description": desc, "requirements": "",
                "preferred_qualifications": "", "remote_status": "remote" if "remote" in location.lower() else "onsite",
                "experience_raw": f"{years}+ years", "experience_min_years": float(years),
                "first_seen_at": first_seen,
            }
            score, explanation = score_job(fields, prefs, now)
            fp = fingerprint(company.id, title, location, "")
            if db.execute(select(Job).where(Job.fingerprint == fp)).scalar_one_or_none():
                continue
            lo, hi = [float(s.replace("$", "").replace(",", "")) for s in salary.replace(" ", "").split("-")]
            db.add(Job(
                company_id=company.id, external_job_id=f"demo-{added}", fingerprint=fp,
                title=title, location=location, description=desc,
                remote_status=fields["remote_status"], experience_raw=fields["experience_raw"],
                experience_min_years=float(years), salary_raw=salary, salary_min=lo, salary_max=hi,
                technologies=[], ats_provider=company.ats_type,
                source_url="", apply_url="https://example.com/DEMO-not-a-real-posting",
                first_seen_at=first_seen, last_seen_at=now, is_active=True, is_demo=True,
                match_score=score, match_explanation=explanation, status="New",
            ))
            added += 1
        db.commit()
        print(f"inserted {added} DEMO jobs (is_demo=True — shown with a DEMO badge)")


if __name__ == "__main__":
    run()
