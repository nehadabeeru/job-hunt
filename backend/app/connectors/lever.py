"""Lever Postings API (official, public, no auth):
https://github.com/lever/postings-api
GET https://api.lever.co/v0/postings/{site}?mode=json
"""
from datetime import datetime, timezone

import httpx

from ..normalize import RawJob
from .base import ATSConnector


class LeverConnector(ATSConnector):
    name = "lever"

    async def get_jobs(self, company, client: httpx.AsyncClient) -> list[RawJob]:
        token = company.ats_identifier
        url = f"https://api.lever.co/v0/postings/{token}?mode=json"
        data = await self._get_json(client, url)
        jobs = []
        for j in data if isinstance(data, list) else []:
            cats = j.get("categories") or {}
            created = None
            if j.get("createdAt"):
                created = datetime.fromtimestamp(j["createdAt"] / 1000, tz=timezone.utc)
            desc = (j.get("descriptionPlain") or j.get("description") or "")
            for lst in j.get("lists") or []:
                desc += "\n" + str(lst.get("text", "")) + "\n" + str(lst.get("content", ""))
            jobs.append(RawJob(
                external_job_id=str(j.get("id", "")),
                title=j.get("text", ""),
                location=cats.get("location", "") or "",
                description=desc,
                employment_type=cats.get("commitment", "") or "",
                source_url=j.get("hostedUrl", ""),
                apply_url=j.get("applyUrl") or j.get("hostedUrl", ""),
                source_created_at=created,
                remote_hint=str(j.get("workplaceType", "")),
                raw={"id": j.get("id")},
            ))
        return jobs
