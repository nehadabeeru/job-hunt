from datetime import datetime, timezone

from sqlalchemy import (JSON, Boolean, DateTime, Float, ForeignKey, Index,
                        Integer, String, Text)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    """Single-user in V1; the table exists so multi-user is a migration, not a rewrite."""
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, default="me@local")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class UserPreference(Base):
    __tablename__ = "user_preferences"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    # Skills, target titles, downrank patterns, score weights, experience range,
    # resume text — one JSON document, editable from the API.
    data: Mapped[dict] = mapped_column(JSON, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class Company(Base):
    __tablename__ = "companies"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    careers_url: Mapped[str] = mapped_column(String(1024), default="")
    ats_type: Mapped[str] = mapped_column(String(50), default="unknown")  # greenhouse|lever|ashby|workday|other|unknown
    ats_identifier: Mapped[str] = mapped_column(String(255), default="")  # board token / tenant id
    # Workday needs an explicit CXS endpoint (tenant+site); stored here when detected/configured.
    connector_config: Mapped[dict] = mapped_column(JSON, default=dict)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    poll_interval_seconds: Mapped[int] = mapped_column(Integer, default=180)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_status: Mapped[str] = mapped_column(String(255), default="never checked")
    consecutive_failures: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    jobs = relationship("Job", back_populates="company")


class Job(Base):
    __tablename__ = "jobs"
    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True)
    external_job_id: Mapped[str] = mapped_column(String(255), default="", index=True)
    fingerprint: Mapped[str] = mapped_column(String(64), index=True)  # fallback dedupe key

    title: Mapped[str] = mapped_column(String(512))
    location: Mapped[str] = mapped_column(String(512), default="")
    remote_status: Mapped[str] = mapped_column(String(32), default="unknown")  # remote|hybrid|onsite|unknown
    employment_type: Mapped[str] = mapped_column(String(64), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    requirements: Mapped[str] = mapped_column(Text, default="")
    preferred_qualifications: Mapped[str] = mapped_column(Text, default="")
    experience_raw: Mapped[str] = mapped_column(String(255), default="")
    experience_min_years: Mapped[float | None] = mapped_column(Float, nullable=True)
    salary_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    salary_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    salary_raw: Mapped[str] = mapped_column(String(255), default="")
    technologies: Mapped[list] = mapped_column(JSON, default=list)
    ats_provider: Mapped[str] = mapped_column(String(50), default="")
    source_url: Mapped[str] = mapped_column(String(1024), default="")
    apply_url: Mapped[str] = mapped_column(String(1024), default="")
    source_created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)  # False once it disappears from the board
    # True only for rows inserted by seed_demo.py — never for fetched jobs.
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)

    match_score: Mapped[float] = mapped_column(Float, default=0, index=True)
    match_explanation: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(20), default="New", index=True)  # New|Saved|Applied|Interview|Rejected|Skip

    company = relationship("Company", back_populates="jobs")

    __table_args__ = (
        Index("ix_jobs_company_external", "company_id", "external_job_id"),
        Index("ix_jobs_seen_score", "first_seen_at", "match_score"),
    )


class JobSource(Base):
    """Where a job was observed (a job can surface via several channels later)."""
    __tablename__ = "job_sources"
    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), index=True)
    provider: Mapped[str] = mapped_column(String(50))
    url: Mapped[str] = mapped_column(String(1024), default="")
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class JobSnapshot(Base):
    """Raw payload snapshots — kept when meaningful fields change, for diffing/debugging."""
    __tablename__ = "job_snapshots"
    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), index=True)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    content_hash: Mapped[str] = mapped_column(String(64), default="")
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Application(Base):
    __tablename__ = "applications"
    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), index=True)
    applied_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    stage: Mapped[str] = mapped_column(String(32), default="applied")  # applied|recruiter_screen|interview|offer|rejected
    notes: Mapped[str] = mapped_column(Text, default="")


class Alert(Base):
    __tablename__ = "alerts"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    min_score: Mapped[float] = mapped_column(Float, default=85)
    max_age_minutes: Mapped[int] = mapped_column(Integer, default=15)
    channels: Mapped[list] = mapped_column(JSON, default=lambda: ["browser"])  # browser|email (telegram/discord/slack/sms later)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class AlertEvent(Base):
    """One row per (alert, job) — this is what prevents duplicate notifications."""
    __tablename__ = "alert_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    alert_id: Mapped[int] = mapped_column(ForeignKey("alerts.id"), index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), index=True)
    fired_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    delivered: Mapped[bool] = mapped_column(Boolean, default=False)
    seen: Mapped[bool] = mapped_column(Boolean, default=False)

    __table_args__ = (Index("ix_alert_events_unique", "alert_id", "job_id", unique=True),)
