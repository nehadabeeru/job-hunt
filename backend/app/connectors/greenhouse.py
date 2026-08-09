"""Greenhouse Job Board API (official, public, no auth):
https://developers.greenhouse.io/job-board.html
GET https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true
"""
from datetime import datetime

import httpx

from ..normalize import RawJob
from .base import ATSConnector


class GreenhouseConnector(ATSConnector):
    name = "greenhouse"

    async def get_jobs(self, company, client: httpx.AsyncClient) -> list[RawJob]:
        token = company.ats_identifier
        url = f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true"
        data = await self._get_json(client, url)
        jobs = []
        for j in data.get("jobs", []):
            created = None
            for key in ("first_published", "updated_at"):
                if j.get(key):
                    try:
                        created = datetime.fromisoformat(str(j[key]).replace("Z", "+00:00"))
                        break
                    except ValueError:
                        pass
            meta_pay = ""
            for f in j.get("metadata") or []:
                if f and "salary" in str(f.get("name", "")).lower() and f.get("value"):
                    meta_pay = str(f["value"])
            jobs.append(RawJob(
                external_job_id=str(j.get("id", "")),
                title=j.get("title", ""),
                location=(j.get("location") or {}).get("name", ""),
                description=j.get("content", ""),
                source_url=j.get("absolute_url", ""),
                apply_url=j.get("absolute_url", ""),
                source_created_at=created,
                salary_raw=meta_pay,
                raw={"id": j.get("id"), "updated_at": j.get("updated_at")},
            ))
        return jobs
