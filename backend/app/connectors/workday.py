"""Workday connector (unofficial CXS JSON endpoint used by Workday's own career
sites — there is no public Workday job-board API).

Requires per-company configuration in Company.connector_config:
    {
      "endpoint": "https://{tenant}.{wdN}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs"
    }
The ATS auto-detect endpoint fills this in when it can. Respect each site's
terms of use and robots.txt; keep polling intervals conservative for Workday.
"""
import httpx

from ..normalize import RawJob
from .base import ATSConnector, FetchError

PAGE_SIZE = 20
MAX_PAGES = 10  # cap per poll; adjust per company if needed


class WorkdayConnector(ATSConnector):
    name = "workday"

    async def get_jobs(self, company, client: httpx.AsyncClient) -> list[RawJob]:
        cfg = company.connector_config or {}
        endpoint = cfg.get("endpoint")
        if not endpoint:
            raise FetchError(
                f"Workday connector for '{company.name}' needs connector_config.endpoint "
                "(run POST /api/companies/{id}/detect or set it manually)"
            )
        # endpoint: https://{host}/wday/cxs/{tenant}/{site}/jobs
        # public job URL base: https://{host}/{site}
        host = endpoint.split("/wday/")[0]
        site = endpoint.rsplit("/jobs", 1)[0].rsplit("/", 1)[-1]
        public_base = f"{host}/{site}"
        jobs, offset = [], 0
        for _ in range(MAX_PAGES):
            payload = {"appliedFacets": {}, "limit": PAGE_SIZE, "offset": offset, "searchText": ""}
            data = await self._get_json(client, endpoint, method="POST", json_body=payload)
            postings = data.get("jobPostings", [])
            if not postings:
                break
            for j in postings:
                path = j.get("externalPath", "")
                url = f"{public_base}{path}" if path else ""
                bullet = j.get("bulletFields") or [""]
                jobs.append(RawJob(
                    external_job_id=str(bullet[0] or path),
                    title=j.get("title", ""),
                    location=j.get("locationsText", ""),
                    description="",  # detail fetch is a follow-up call; kept lean in V1
                    source_url=url,
                    apply_url=url,
                    raw={"postedOn": j.get("postedOn", "")},
                ))
            offset += PAGE_SIZE
            if offset >= int(data.get("total", 0)):
                break
        return jobs
