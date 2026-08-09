"""Ashby public posting API (official, no auth):
https://developers.ashbyhq.com/reference/jobpostingapi
GET https://api.ashbyhq.com/posting-api/job-board/{board_name}?includeCompensation=true
"""
from datetime import datetime

import httpx

from ..normalize import RawJob
from .base import ATSConnector


class AshbyConnector(ATSConnector):
    name = "ashby"

    async def get_jobs(self, company, client: httpx.AsyncClient) -> list[RawJob]:
        token = company.ats_identifier
        url = f"https://api.ashbyhq.com/posting-api/job-board/{token}?includeCompensation=true"
        data = await self._get_json(client, url)
        jobs = []
        for j in data.get("jobs", []):
            created = None
            if j.get("publishedAt"):
                try:
                    created = datetime.fromisoformat(str(j["publishedAt"]).replace("Z", "+00:00"))
                except ValueError:
                    pass
            comp = ""
            comp_obj = j.get("compensation") or {}
            if comp_obj.get("compensationTierSummary"):
                comp = str(comp_obj["compensationTierSummary"])
            jobs.append(RawJob(
                external_job_id=str(j.get("id", "")),
                title=j.get("title", ""),
                location=j.get("location", ""),
                description=j.get("descriptionPlain") or j.get("descriptionHtml") or "",
                employment_type=j.get("employmentType", ""),
                source_url=j.get("jobUrl", ""),
                apply_url=j.get("applyUrl") or j.get("jobUrl", ""),
                source_created_at=created,
                salary_raw=comp,
                remote_hint="remote" if j.get("isRemote") else "",
                raw={"id": j.get("id")},
            ))
        return jobs
