from datetime import datetime

from pydantic import BaseModel, ConfigDict

STATUSES = ["New", "Saved", "Applied", "Interview", "Rejected", "Skip"]


class CompanyIn(BaseModel):
    name: str
    careers_url: str = ""
    ats_type: str = "unknown"
    ats_identifier: str = ""
    connector_config: dict = {}
    enabled: bool = True
    poll_interval_seconds: int = 180


class CompanyOut(CompanyIn):
    model_config = ConfigDict(from_attributes=True)
    id: int
    last_checked_at: datetime | None = None
    last_status: str = ""
    consecutive_failures: int = 0
    job_count: int = 0


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    company_id: int
    company_name: str = ""
    external_job_id: str
    title: str
    location: str
    remote_status: str
    employment_type: str
    experience_raw: str
    experience_min_years: float | None
    salary_min: float | None
    salary_max: float | None
    salary_raw: str
    technologies: list
    ats_provider: str
    source_url: str
    apply_url: str
    source_created_at: datetime | None
    first_seen_at: datetime
    last_seen_at: datetime
    is_active: bool
    is_demo: bool
    match_score: float
    status: str


class JobDetailOut(JobOut):
    description: str
    requirements: str
    preferred_qualifications: str
    match_explanation: dict


class StatusUpdate(BaseModel):
    status: str


class AlertIn(BaseModel):
    name: str
    min_score: float = 85
    max_age_minutes: int = 15
    channels: list[str] = ["browser"]
    enabled: bool = True


class ApplicationStageUpdate(BaseModel):
    stage: str
    notes: str = ""
