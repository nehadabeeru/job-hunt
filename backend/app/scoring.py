"""Hybrid 0–100 match scoring with a human-readable explanation.

Components (weights configurable in preferences.score_weights):
  skill_overlap        — user skills found in the job text, priority skills count extra
  semantic_similarity  — V1: lexical (token-overlap) similarity between resume_text and
                         the job description. Phase 3 swaps this component for embedding
                         cosine similarity behind the same interface.
  title_relevance      — boost/block term matching against the title
  experience_fit       — parsed "N+ years" vs the user's 2–6y target range
  freshness            — decays with hours since first_seen_at
  location             — US / remote preference match
"""
import re
from datetime import datetime, timezone

STOPWORDS = set("a an and are as at be by for from has have in is it of on or that the to was we with you your will our".split())

SKILL_SYNONYMS = {
    "postgresql": ["postgres", "postgresql"],
    "rest": ["rest", "restful"],
    "event-driven": ["event-driven", "event driven"],
    "ci/cd": ["ci/cd", "cicd", "ci cd", "continuous integration"],
    "genai": ["genai", "generative ai", "gen ai"],
    "distributed systems": ["distributed systems", "distributed system"],
    "async": ["async", "asynchronous"],
    "embeddings": ["embeddings", "embedding", "vector search"],
}


def _skill_in_text(skill: str, low_text: str) -> bool:
    for variant in SKILL_SYNONYMS.get(skill, [skill]):
        pattern = r"(?<![a-z0-9+])" + re.escape(variant) + r"(?![a-z0-9+])"
        if re.search(pattern, low_text):
            return True
    return False


def _tokenize(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9+#/.-]{2,}", (text or "").lower()) if t not in STOPWORDS}


def score_job(job_fields: dict, prefs: dict, now: datetime | None = None) -> tuple[float, dict]:
    now = now or datetime.now(timezone.utc)
    weights = prefs.get("score_weights", {})
    total_w = sum(weights.values()) or 1.0

    text = " ".join([
        job_fields.get("title", ""), job_fields.get("description", ""),
        job_fields.get("requirements", ""), job_fields.get("preferred_qualifications", ""),
    ]).lower()
    title = job_fields.get("title", "").lower()

    # --- skill overlap ---
    skills = [s.lower() for s in prefs.get("skills", [])]
    priority = {s.lower() for s in prefs.get("priority_skills", [])}
    matching, missing = [], []
    weight_hit = weight_total = 0.0
    for s in skills:
        w = 2.0 if s in priority else 1.0
        weight_total += w
        if _skill_in_text(s, text):
            matching.append(s)
            weight_hit += w
        else:
            missing.append(s)
    skill_component = (weight_hit / weight_total) if weight_total else 0.0
    # A job mentioning ~half of a broad skill list is a strong match; rescale.
    skill_component = min(1.0, skill_component / 0.55)

    # --- semantic similarity (V1: lexical) ---
    resume = prefs.get("resume_text", "")
    if resume.strip():
        rt, jt = _tokenize(resume), _tokenize(text)
        inter = len(rt & jt)
        sim = inter / max(1, min(len(rt), len(jt)))
        semantic_component = min(1.0, sim / 0.35)
        semantic_note = "lexical similarity vs resume (embedding upgrade planned)"
    else:
        # No resume on file: fall back to skill signal so the component isn't dead weight.
        semantic_component = skill_component
        semantic_note = "no resume_text set — using skill overlap as proxy"

    # --- title relevance ---
    block_hits = [t for t in prefs.get("title_block_terms", []) if t.lower() in title]
    boost_hits = [t for t in prefs.get("title_boost_terms", []) if t.lower() in title]
    if block_hits:
        title_component = 0.0
    else:
        title_component = min(1.0, 0.35 + 0.35 * len(boost_hits)) if boost_hits else 0.15

    # --- experience fit ---
    req_years = job_fields.get("experience_min_years")
    lo = prefs.get("experience_min_years", 2)
    hi = prefs.get("experience_max_years", 6)
    if req_years is None:
        experience_component, exp_note = 0.7, "no explicit requirement found"
    elif lo <= req_years <= hi:
        experience_component, exp_note = 1.0, f"requires {int(req_years)}+ years — good match"
    elif req_years < lo:
        experience_component, exp_note = 0.8, f"requires {int(req_years)}+ years — junior of target range"
    else:
        over = req_years - hi
        experience_component = max(0.0, 1.0 - 0.35 * over)
        exp_note = f"requires {int(req_years)}+ years — above target range"

    # --- freshness ---
    first_seen = job_fields.get("first_seen_at") or now
    if first_seen.tzinfo is None:
        first_seen = first_seen.replace(tzinfo=timezone.utc)
    age_hours = max(0.0, (now - first_seen).total_seconds() / 3600)
    freshness_component = 1.0 if age_hours < 1 else 0.85 if age_hours < 6 else 0.6 if age_hours < 24 else 0.35 if age_hours < 24 * 7 else 0.15

    # --- location ---
    loc = (job_fields.get("location", "") + " " + job_fields.get("remote_status", "")).lower()
    prefs_loc = [p.lower() for p in prefs.get("preferred_locations", [])]
    us_markers = ("united states", "usa", "us", "remote", ", al", ", ak", ", az", ", ar", ", ca", ", co", ", ct", ", de", ", fl", ", ga", ", hi", ", id", ", il", ", in", ", ia", ", ks", ", ky", ", la", ", me", ", md", ", ma", ", mi", ", mn", ", ms", ", mo", ", mt", ", ne", ", nv", ", nh", ", nj", ", nm", ", ny", ", nc", ", nd", ", oh", ", ok", ", or", ", pa", ", ri", ", sc", ", sd", ", tn", ", tx", ", ut", ", vt", ", va", ", wa", ", wv", ", wi", ", wy", "new york", "san francisco", "seattle", "austin", "boston", "chicago", "charlotte", "raleigh", "atlanta", "denver")
    if any(p in loc for p in prefs_loc) or any(m in loc for m in us_markers):
        location_component = 1.0
    elif not loc.strip():
        location_component = 0.6
    else:
        location_component = 0.2

    components = {
        "skill_overlap": skill_component,
        "semantic_similarity": semantic_component,
        "title_relevance": title_component,
        "experience_fit": experience_component,
        "freshness": freshness_component,
        "location": location_component,
    }
    score = sum(components[k] * weights.get(k, 0) for k in components) / total_w * 100
    if block_hits:
        score = min(score, 25.0)  # hard down-rank for blocked titles

    explanation = {
        "matching_skills": matching,
        "missing_skills": [m for m in missing if m in priority][:10] or missing[:10],
        "title": {"boost_hits": boost_hits, "block_hits": block_hits},
        "experience": {"required_raw": job_fields.get("experience_raw", ""), "required_years": req_years, "note": exp_note},
        "semantic_note": semantic_note,
        "components": {k: round(v, 3) for k, v in components.items()},
        "weights": weights,
    }
    return round(score, 1), explanation
