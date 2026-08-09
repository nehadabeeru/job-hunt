"""Connector interface. Each ATS implements get_jobs and stays independent —
one broken connector or company never affects the others (the scheduler
isolates every company fetch in its own try/except)."""
import asyncio
import logging
from abc import ABC, abstractmethod

import httpx

from ..config import settings
from ..normalize import RawJob

log = logging.getLogger("jobradar.connectors")


class FetchError(Exception):
    pass


class ATSConnector(ABC):
    name: str = "base"

    @abstractmethod
    async def get_jobs(self, company, client: httpx.AsyncClient) -> list[RawJob]:
        """Return the company's current openings as RawJob objects."""

    async def _get_json(self, client: httpx.AsyncClient, url: str, *, method: str = "GET", json_body: dict | None = None):
        """GET/POST JSON with retries + exponential backoff. 429s respect Retry-After."""
        last_exc = None
        for attempt in range(settings.FETCH_MAX_RETRIES):
            try:
                resp = await client.request(method, url, json=json_body, timeout=settings.HTTP_TIMEOUT_SECONDS)
                if resp.status_code == 429:
                    wait = float(resp.headers.get("Retry-After", settings.FETCH_BACKOFF_BASE_SECONDS * (2 ** attempt)))
                    log.warning("rate limited url=%s wait=%.1fs", url, wait)
                    await asyncio.sleep(wait)
                    continue
                if resp.status_code == 404:
                    raise FetchError(f"404 — board token likely wrong for {url}")
                resp.raise_for_status()
                return resp.json()
            except FetchError:
                raise
            except Exception as exc:  # timeouts, 5xx, network
                last_exc = exc
                await asyncio.sleep(settings.FETCH_BACKOFF_BASE_SECONDS * (2 ** attempt))
        raise FetchError(f"failed after {settings.FETCH_MAX_RETRIES} attempts: {last_exc}")
