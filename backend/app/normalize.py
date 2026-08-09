"""Turn a raw connector payload into normalized Job fields."""
import re
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class RawJob:
    external_job_id: str
    title: str
    location: str = ""
    description: str = ""          # plain text or HTML (stripped below)
    employment_type: str = ""
    source_url: str = ""
    apply_url: str = ""
    source_created_at: datetime | None = None
    salary_raw: str = ""
    remote_hint: str = ""          # connector-provided hint, e.g. "remote"
    raw: dict = field(default_factory=dict)


TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"[ \t]+")

EXPERIENCE_RE = re.compile(
    r"(\d{1,2})\s*(?:\+|\-\s*\d{1,2})?\s*(?:or more\s+)?years?", re.IGNORECASE
)
SALARY_RE = re.compile(
    r"\$\s?(\d{2,3})(?:,(\d{3}))?(?:\.\d+)?\s*[kK]?\s*(?:-|–|to)\s*\$?\s?(\d{2,3})(?:,(\d{3}))?(?:\.\d+)?\s*[kK]?"
)

TECH_TERMS = [
    "python", "java", "go", "golang", "rust", "c++", "typescript", "javascript", "scala",
    "kotlin", "ruby", "aws", "gcp", "azure", "lambda", "appsync", "fastapi", "django",
    "flask", "spring", "graphql", "rest", "grpc", "postgresql", "postgres", "mysql",
    "dynamodb", "mongodb", "redis", "opensearch", "elasticsearch", "kafka", "sqs", "sns",
    "rabbitmq", "docker", "kubernetes", "terraform", "microservices", "spark", "airflow",
    "snowflake", "databricks", "dbt", "ci/cd", "genai", "llm", "rag", "embeddings",
    "pytorch", "tensorflow", "react", "node",
]


def strip_html(text: str) -> str:
    text = re.sub(r"<(br|/p|/li|/div|/h[1-6])\s*/?>", "\n", text or "", flags=re.IGNORECASE)
    text = TAG_RE.sub(" ", text)
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&nbsp;", " ").replace("&#39;", "'").replace("&quot;", '"')
    lines = [WS_RE.sub(" ", ln).strip() for ln in text.splitlines()]
    return "\n".join(ln for ln in lines if ln)


def parse_experience(text: str) -> tuple[str, float | None]:
    m = EXPERIENCE_RE.search(text or "")
    if not m:
        return "", None
    return m.group(0), float(m.group(1))


def parse_salary(text: str) -> tuple[str, float | None, float | None]:
    m = SALARY_RE.search(text or "")
    if not m:
        return "", None, None
    def to_num(whole, thousands):
        v = float(whole + (thousands or ""))
        return v * 1000 if v < 1000 else v
    lo = to_num(m.group(1), m.group(2))
    hi = to_num(m.group(3), m.group(4))
    return m.group(0), lo, hi


def detect_remote(location: str, hint: str, description: str) -> str:
    blob = f"{location} {hint}".lower()
    if "remote" in blob:
        return "hybrid" if "hybrid" in blob else "remote"
    if "hybrid" in blob:
        return "hybrid"
    head = (description or "")[:600].lower()
    if "fully remote" in head or "remote-first" in head:
        return "remote"
    if location:
        return "onsite"
    return "unknown"


def extract_technologies(text: str) -> list[str]:
    low = (text or "").lower()
    found = []
    for term in TECH_TERMS:
        pattern = r"(?<![a-z0-9+])" + re.escape(term) + r"(?![a-z0-9+])"
        if re.search(pattern, low):
            found.append("postgresql" if term == "postgres" else ("go" if term == "golang" else term))
    return sorted(set(found))


def split_sections(description: str) -> tuple[str, str]:
    """Best-effort extraction of requirements / preferred sections from plain text."""
    req, pref = "", ""
    lines = (description or "").splitlines()
    bucket = None
    req_lines, pref_lines = [], []
    for ln in lines:
        low = ln.lower().strip()
        if any(h in low for h in ("requirement", "qualifications", "what you'll need", "what you need", "must have")) and len(low) < 80:
            bucket = "pref" if "preferred" in low or "nice" in low else "req"
            continue
        if any(h in low for h in ("preferred", "nice to have", "bonus points")) and len(low) < 80:
            bucket = "pref"
            continue
        if low.endswith(":") and len(low) < 60 and bucket:
            bucket = None
        if bucket == "req":
            req_lines.append(ln)
        elif bucket == "pref":
            pref_lines.append(ln)
    req = "\n".join(req_lines[:60]).strip()
    pref = "\n".join(pref_lines[:40]).strip()
    return req, pref


def normalize(raw: RawJob) -> dict:
    description = strip_html(raw.description)
    exp_raw, exp_years = parse_experience(description)
    sal_raw, sal_min, sal_max = parse_salary(raw.salary_raw or description)
    requirements, preferred = split_sections(description)
    return {
        "external_job_id": str(raw.external_job_id or ""),
        "title": (raw.title or "").strip(),
        "location": (raw.location or "").strip(),
        "remote_status": detect_remote(raw.location, raw.remote_hint, description),
        "employment_type": raw.employment_type or "",
        "description": description,
        "requirements": requirements,
        "preferred_qualifications": preferred,
        "experience_raw": exp_raw,
        "experience_min_years": exp_years,
        "salary_raw": raw.salary_raw or sal_raw,
        "salary_min": sal_min,
        "salary_max": sal_max,
        "technologies": extract_technologies(description + " " + raw.title),
        "source_url": raw.source_url,
        "apply_url": raw.apply_url or raw.source_url,
        "source_created_at": raw.source_created_at,
    }
