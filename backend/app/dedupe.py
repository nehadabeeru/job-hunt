import hashlib


def fingerprint(company_id: int, title: str, location: str, apply_url: str) -> str:
    """Fallback dedupe key when an ATS job ID is unavailable."""
    raw = f"{company_id}|{(title or '').strip().lower()}|{(location or '').strip().lower()}|{(apply_url or '').strip().lower()}"
    return hashlib.sha1(raw.encode()).hexdigest()


def content_hash(title: str, location: str, description: str, salary_raw: str) -> str:
    """Hash of meaningful fields — used to decide if a reappearing job actually changed."""
    raw = f"{title}|{location}|{description}|{salary_raw}"
    return hashlib.sha1(raw.encode()).hexdigest()
