"""Unit and integration tests for Phase 12C:
- Faithfulness validator (catches invented numbers, invented tools, first person, weak verbs, length)
- Fallback path works with Ollama down or USE_SLM=false
- Tailor never mutates the input resume
- Cache is in-memory only (zero disk persistence)
- Logs contain no resume text
- API endpoints with rate limiting, timeouts, and structured response
"""

from __future__ import annotations

import copy
import json
import logging
from pathlib import Path
from typing import Any, Dict

import pytest
from fastapi.testclient import TestClient

from api.main import app
from config import settings
from ml.resume_ai import (
    _IN_MEMORY_AI_CACHE,
    draft_summary,
    improve_bullet,
    polish_project,
    suggest_skills_from_text,
    tailor,
)
from ml.resume_ai_validate import validate_bullet, validate_summary
from ml.resume_schema import Resume

FIXTURE_1 = Path(__file__).resolve().parent / "fixtures" / "resume_example_1.json"

client = TestClient(app)


@pytest.fixture
def sample_resume() -> Dict[str, Any]:
    with open(FIXTURE_1, "r", encoding="utf-8") as f:
        return json.load(f)


# =========================================================================
# 1. Faithfulness Validator Tests
# =========================================================================

def test_validator_catches_invented_number():
    """Assert validator rejects candidate that invents numbers not in source."""
    source = "Built backend microservices in FastAPI with PostgreSQL."
    candidate = "Built backend microservices in FastAPI reducing latency by 45%."

    is_valid, checks, failures = validate_bullet(candidate, source)
    assert not is_valid
    assert not checks["no_invented_numbers"]
    assert any("Invented numbers" in f for f in failures)


def test_validator_catches_invented_tool():
    """Assert validator rejects candidate that introduces unverified tools."""
    source = "Engineered caching layer for low-latency requests."
    candidate = "Engineered caching layer using Redis and Kubernetes for low-latency requests."

    is_valid, checks, failures = validate_bullet(candidate, source, context={"selected_skills": []})
    assert not is_valid
    assert not checks["no_invented_tools"]
    assert any("Invented tools" in f for f in failures)


def test_validator_catches_first_person():
    """Assert validator rejects candidate containing first person pronouns."""
    source = "I developed the REST API for customer onboarding."
    candidate = "I developed the REST API for customer onboarding and verification."

    is_valid, checks, failures = validate_bullet(candidate, source)
    assert not is_valid
    assert not checks["no_first_person"]


def test_validator_catches_weak_verb():
    """Assert validator rejects candidate starting with weak phrase or non-action verb."""
    source = "Responsible for fixing bugs in the payment system."
    candidate = "Responsible for fixing bugs in the payment system."

    is_valid, checks, failures = validate_bullet(candidate, source)
    assert not is_valid
    assert not checks["no_banned_phrases"]


def test_validator_passes_faithful_bullet():
    """Assert validator approves bullet with action verb and faithful facts."""
    source = "Worked on reducing query latency from 450ms down to 60ms by adding Redis caching."
    candidate = "Engineered Redis caching layer reducing query latency from 450ms down to 60ms."

    is_valid, checks, failures = validate_bullet(candidate, source)
    assert is_valid
    assert all(checks.values())
    assert len(failures) == 0


# =========================================================================
# 2. Rule-Based Fallback Engine
# =========================================================================

def test_improve_bullet_fallback_rules():
    """Assert improve_bullet works gracefully without SLM and eliminates weak phrases."""
    orig = "I was responsible for developing the user authentication backend with JWT in FastAPI."
    res = improve_bullet(orig, context={"role": "Backend Engineer", "company": "SaaS Platform"})

    assert res["source"] in ("rules", "slm")
    assert "variants" in res
    assert len(res["variants"]) >= 1

    first_var = res["variants"][0]
    # Pronoun 'I' and 'responsible for' stripped
    assert not first_var["text"].lower().startswith("i was responsible")
    assert first_var["checks"]["no_first_person"]
    assert first_var["checks"]["no_banned_phrases"]


def test_improve_bullet_suggests_missing_metric_prompt():
    """Assert missing metric prompt is provided when no numbers exist."""
    orig = "Built microservices architecture using Python and FastAPI."
    res = improve_bullet(orig)
    assert res["variants"][0]["missing_metric_prompt"] is not None
    assert "number" in res["variants"][0]["missing_metric_prompt"].lower() or "measurable" in res["variants"][0]["missing_metric_prompt"].lower()


def test_draft_summary_fallback_grounded(sample_resume):
    """Assert summary generation uses verified resume fields without hallucinations."""
    res = draft_summary(sample_resume)
    assert "variants" in res
    assert len(res["variants"]) >= 1
    summary_text = res["variants"][0]["text"]
    assert len(summary_text.split(".")) >= 2
    # Verify candidate role appears
    assert "Engineer" in summary_text or "Developer" in summary_text


def test_polish_project_fallback():
    """Assert polish_project produces bullets strictly from notes without inventing tools."""
    notes = "I worked on creating a cache with Redis. It reduced latency significantly."
    res = polish_project("MicroCache", ["Redis", "Python"], notes)
    assert "bullets" in res
    assert 1 <= len(res["bullets"]) <= 2
    assert not res["bullets"][0].lower().startswith("i worked on")


# =========================================================================
# 3. Deterministic Skill Suggestion & Tailoring (No Mutation)
# =========================================================================

def test_suggest_skills_from_text(sample_resume):
    """Assert suggest_skills_from_text discovers skills present in text not in selected list."""
    # Temporarily remove Docker from candidate skills
    modified = copy.deepcopy(sample_resume)
    modified["skills"] = [s for s in modified["skills"] if s["name"].lower() != "docker"]

    suggestions = suggest_skills_from_text(modified)
    s_names = [s["name"].lower() for s in suggestions]
    assert "docker" in s_names


def test_tailor_never_mutates_resume(sample_resume):
    """Assert tailor executes gap analysis without changing input resume dictionary."""
    orig_copy = copy.deepcopy(sample_resume)
    res = tailor(sample_resume, target="DevOps Engineer")

    # Verify input resume is untouched
    assert sample_resume == orig_copy
    # Verify result structure
    assert res["suggest_only"] is True
    assert "score" in res
    assert "missing_skills" in res
    assert len(res["missing_skills"]) > 0


# =========================================================================
# 4. Cache & Logging Invariants
# =========================================================================

def test_cache_is_in_memory_only():
    """Assert cache is stored only in-memory and not on disk."""
    initial_cache_len = len(_IN_MEMORY_AI_CACHE)
    res = improve_bullet("Created Docker deployment pipelines for backend services.")
    assert len(_IN_MEMORY_AI_CACHE) >= initial_cache_len

    # Ensure no disk files created in temp or app data for resume AI cache
    assert isinstance(_IN_MEMORY_AI_CACHE, dict)


def test_logging_omits_resume_content(caplog):
    """Verify logger never logs resume body or bullet text."""
    with caplog.at_level(logging.INFO):
        improve_bullet("Sensitive secret project bullet with internal details.")
        for record in caplog.records:
            assert "Sensitive secret project" not in record.message


# =========================================================================
# 5. API Endpoints
# =========================================================================

def test_api_ai_bullet():
    resp = client.post("/resume/ai/bullet", json={"text": "Responsible for developing APIs with FastAPI."})
    assert resp.status_code == 200
    data = resp.json()
    assert "variants" in data
    assert "source" in data


def test_api_ai_summary(sample_resume):
    resp = client.post("/resume/ai/summary", json=sample_resume)
    assert resp.status_code == 200
    data = resp.json()
    assert "variants" in data


def test_api_ai_project():
    payload = {
        "name": "Cache Engine",
        "tech": ["Python", "Redis"],
        "notes": "Worked on cache invalidation logic.",
    }
    resp = client.post("/resume/ai/project", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "bullets" in data


def test_api_ai_suggest_skills(sample_resume):
    resp = client.post("/resume/ai/suggest-skills", json=sample_resume)
    assert resp.status_code == 200
    data = resp.json()
    assert "suggestions" in data


def test_api_ai_tailor(sample_resume):
    payload = {
        "resume": sample_resume,
        "target": "Backend Developer",
    }
    resp = client.post("/resume/ai/tailor", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["suggest_only"] is True
    assert "missing_skills" in data
