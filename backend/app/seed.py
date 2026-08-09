"""Seed the company watchlist from data/companies_seed.csv.

NOTE ON TOKENS: the seeded ats_identifier values are best-effort, well-known
board tokens. Companies change ATS vendors; a wrong token shows up as a 404 in
the company's last_status on first poll — fix it there or hit /detect.
Run:  python -m app.seed
"""
import csv
import pathlib

from sqlalchemy import func, select

from .db import Base, SessionLocal, engine
from .models import Company

CSV_PATH = pathlib.Path(__file__).resolve().parent.parent / "data" / "companies_seed.csv"


def run():
    Base.metadata.create_all(engine)
    with SessionLocal() as db, open(CSV_PATH) as f:
        added = 0
        for row in csv.DictReader(f):
            name = row["name"].strip()
            if not name or row["ats_type"] == "disabled_example":
                continue
            exists = db.execute(select(Company).where(func.lower(Company.name) == name.lower())).scalar_one_or_none()
            if exists:
                continue
            db.add(Company(
                name=name, careers_url=row["careers_url"].strip(),
                ats_type=row["ats_type"].strip(), ats_identifier=row["ats_identifier"].strip(),
            ))
            added += 1
        db.commit()
        print(f"seeded {added} companies")


if __name__ == "__main__":
    run()
