"""Given a careers URL, figure out which ATS backs it and extract the board token."""
import re

import httpx

PATTERNS = [
    ("greenhouse", re.compile(r"boards(?:-api)?\.greenhouse\.io/(?:v1/boards/)?(?:embed/job_board\?for=)?([a-z0-9_-]+)", re.I)),
    ("greenhouse", re.compile(r"job-boards\.greenhouse\.io/([a-z0-9_-]+)", re.I)),
    ("greenhouse", re.compile(r"greenhouse\.io/embed/job_board\?for=([a-z0-9_-]+)", re.I)),
    ("lever", re.compile(r"jobs\.lever\.co/([a-z0-9_-]+)", re.I)),
    ("ashby", re.compile(r"jobs\.ashbyhq\.com/([a-z0-9_.-]+)", re.I)),
    ("workday", re.compile(r"([a-z0-9-]+)\.wd\d+\.myworkdayjobs\.com", re.I)),
]


def detect_from_url(url: str) -> tuple[str, str]:
    for ats, pat in PATTERNS:
        m = pat.search(url or "")
        if m:
            return ats, m.group(1)
    return "unknown", ""


async def detect(careers_url: str, client: httpx.AsyncClient) -> tuple[str, str, dict]:
    """Returns (ats_type, ats_identifier, connector_config)."""
    ats, ident = detect_from_url(careers_url)
    if ats != "unknown":
        return ats, ident, _workday_config(careers_url) if ats == "workday" else {}
    try:
        resp = await client.get(careers_url, follow_redirects=True, timeout=15)
        body = resp.text[:400_000]
        final = str(resp.url)
        ats, ident = detect_from_url(final)
        if ats == "unknown":
            for pat_ats, pat in PATTERNS:
                m = pat.search(body)
                if m:
                    ats, ident = pat_ats, m.group(1)
                    break
        cfg = _workday_config(final if "myworkdayjobs" in final else body) if ats == "workday" else {}
        return ats, ident, cfg
    except Exception:
        return "unknown", "", {}


def _workday_config(text: str) -> dict:
    m = re.search(r"https://([a-z0-9-]+)\.(wd\d+)\.myworkdayjobs\.com/(?:[a-z-]+/)?([A-Za-z0-9_-]+)", text or "")
    if not m:
        return {}
    tenant, wd, site = m.group(1), m.group(2), m.group(3)
    return {
        "tenant": tenant,
        "endpoint": f"https://{tenant}.{wd}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs",
        "site": site,
    }
