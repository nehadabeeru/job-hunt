import csv
import io

import httpx
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..ats_detect import detect
from ..db import get_db
from ..ingest import poll_company
from ..models import Company, Job
from ..schemas import CompanyIn, CompanyOut

router = APIRouter(prefix="/api/companies", tags=["companies"])


def _with_counts(db: Session, companies: list[Company]) -> list[dict]:
    counts = dict(db.execute(select(Job.company_id, func.count()).where(Job.is_active == True).group_by(Job.company_id)).all())
    out = []
    for c in companies:
        d = CompanyOut.model_validate(c).model_dump()
        d["job_count"] = counts.get(c.id, 0)
        out.append(d)
    return out


@router.get("")
def list_companies(db: Session = Depends(get_db)):
    companies = db.execute(select(Company).order_by(Company.name)).scalars().all()
    return _with_counts(db, companies)


@router.post("", status_code=201)
async def create_company(body: CompanyIn, db: Session = Depends(get_db)):
    company = Company(**body.model_dump())
    if company.ats_type == "unknown" and company.careers_url:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            ats, ident, cfg = await detect(company.careers_url, client)
        company.ats_type, company.ats_identifier = ats, ident
        company.connector_config = cfg
    db.add(company)
    db.commit()
    return _with_counts(db, [company])[0]


@router.patch("/{company_id}")
def update_company(company_id: int, body: CompanyIn, db: Session = Depends(get_db)):
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(404, "company not found")
    for k, v in body.model_dump().items():
        setattr(company, k, v)
    db.commit()
    return _with_counts(db, [company])[0]


@router.delete("/{company_id}")
def delete_company(company_id: int, db: Session = Depends(get_db)):
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(404, "company not found")
    company.enabled = False  # soft-disable; jobs/applications history stays intact
    db.commit()
    return {"ok": True, "disabled": True}


@router.post("/{company_id}/detect")
async def detect_company(company_id: int, db: Session = Depends(get_db)):
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(404, "company not found")
    async with httpx.AsyncClient(follow_redirects=True) as client:
        ats, ident, cfg = await detect(company.careers_url, client)
    if ats != "unknown":
        company.ats_type, company.ats_identifier = ats, ident
        if cfg:
            company.connector_config = cfg
        db.commit()
    return {"ats_type": ats, "ats_identifier": ident, "connector_config": cfg}


@router.post("/{company_id}/poll")
async def poll_now(company_id: int, db: Session = Depends(get_db)):
    """Manually poll one company right now (also useful for verifying a new token)."""
    headers = {"User-Agent": "JobRadar/1.0 (personal job-search dashboard)"}
    async with httpx.AsyncClient(headers=headers, follow_redirects=True) as client:
        return await poll_company(company_id, client, db)


@router.post("/import-csv")
async def import_csv(file: UploadFile, db: Session = Depends(get_db)):
    """CSV columns: name, careers_url[, ats_type, ats_identifier]. Hundreds of rows OK."""
    content = (await file.read()).decode("utf-8", errors="replace")
    reader = csv.DictReader(io.StringIO(content))
    added, skipped = 0, 0
    for row in reader:
        name = (row.get("name") or "").strip()
        if not name:
            continue
        exists = db.execute(select(Company).where(func.lower(Company.name) == name.lower())).scalar_one_or_none()
        if exists:
            skipped += 1
            continue
        ats = (row.get("ats_type") or "unknown").strip().lower()
        ident = (row.get("ats_identifier") or "").strip()
        url = (row.get("careers_url") or "").strip()
        if ats == "unknown" and url:
            from ..ats_detect import detect_from_url
            ats, ident = detect_from_url(url)
        db.add(Company(name=name, careers_url=url, ats_type=ats or "unknown", ats_identifier=ident))
        added += 1
    db.commit()
    return {"added": added, "skipped_existing": skipped}
