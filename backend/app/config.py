"""Central configuration. Every value can be overridden with environment variables."""
import os


class Settings:
    # sqlite by default so the app runs with zero setup; point at Postgres in prod:
    #   DATABASE_URL=postgresql+psycopg2://jobradar:jobradar@db:5432/jobradar
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./jobradar.db")

    # Master switch for the background poller. Off by default so imports/tests
    # and first-run exploration never hit external ATS APIs unintentionally.
    ENABLE_POLLING: bool = os.getenv("ENABLE_POLLING", "false").lower() == "true"

    # How often the scheduler wakes up to look for companies that are due.
    SCHEDULER_TICK_SECONDS: int = int(os.getenv("SCHEDULER_TICK_SECONDS", "60"))
    # Default per-company polling interval (each company can override).
    DEFAULT_POLL_INTERVAL_SECONDS: int = int(os.getenv("DEFAULT_POLL_INTERVAL_SECONDS", "180"))

    # Concurrency + resilience for outbound ATS requests.
    MAX_CONCURRENT_FETCHES: int = int(os.getenv("MAX_CONCURRENT_FETCHES", "8"))
    HTTP_TIMEOUT_SECONDS: float = float(os.getenv("HTTP_TIMEOUT_SECONDS", "20"))
    FETCH_MAX_RETRIES: int = int(os.getenv("FETCH_MAX_RETRIES", "3"))
    FETCH_BACKOFF_BASE_SECONDS: float = float(os.getenv("FETCH_BACKOFF_BASE_SECONDS", "2"))

    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")

    # Notion sync (Phase 3) — leave blank until configured.
    NOTION_TOKEN: str = os.getenv("NOTION_TOKEN", "")
    NOTION_DATABASE_ID: str = os.getenv("NOTION_DATABASE_ID", "")

    # SMTP for email alerts (Phase 2) — leave blank until configured.
    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    ALERT_EMAIL_TO: str = os.getenv("ALERT_EMAIL_TO", "")


settings = Settings()
