"""Default user profile. Fully editable at runtime via PUT /api/preferences."""

DEFAULT_PREFERENCES = {
    "target_titles": [
        "software engineer", "software engineer ii", "backend software engineer",
        "python backend engineer", "software development engineer", "sde ii",
        "platform engineer", "distributed systems engineer", "cloud software engineer",
        "data platform software engineer", "ai platform engineer", "genai software engineer",
    ],
    "title_boost_terms": [
        "software engineer", "backend", "platform", "python", "distributed systems",
        "cloud", "infrastructure", "data platform", "ai platform", "genai",
        "api", "microservices",
    ],
    # Titles matching these are auto-rejected/heavily down-ranked (configurable).
    "title_block_terms": [
        "staff", "principal", "distinguished", "engineering manager", "director",
        "vp ", "vice president", "intern", "internship", "new grad", "university grad",
        "hardware", "embedded", "frontend engineer", "front-end engineer", "front end engineer",
        "qa engineer", "quality assurance", "sdet", "test engineer", "support engineer",
        "technical support",
    ],
    "skills": [
        "python", "java", "rest", "graphql", "fastapi", "aws", "lambda", "appsync",
        "postgresql", "dynamodb", "opensearch", "redis", "microservices",
        "distributed systems", "event-driven", "async", "kafka", "sqs",
        "docker", "terraform", "ci/cd", "genai", "rag", "embeddings", "llm",
    ],
    # Extra positive weight inside the skill-overlap component.
    "priority_skills": [
        "python", "java", "aws", "backend", "rest", "graphql", "postgresql",
        "dynamodb", "redis", "microservices", "distributed systems",
        "event-driven", "docker", "terraform", "opensearch", "genai", "rag",
    ],
    "experience_min_years": 2,
    "experience_max_years": 6,
    "preferred_locations": ["united states", "remote"],
    "work_authorization_note": "US",
    # Hybrid score weights — must sum to 1.0 (validated in scoring).
    "score_weights": {
        "skill_overlap": 0.35,
        "semantic_similarity": 0.25,
        "title_relevance": 0.15,
        "experience_fit": 0.10,
        "freshness": 0.10,
        "location": 0.05,
    },
    # Paste resume text here (or via the API) to power the similarity component.
    # Phase 3 upgrades this from lexical similarity to embedding similarity.
    "resume_text": "",
    "daily_application_goal": 30,
}
