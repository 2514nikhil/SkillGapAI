"""Integration tests for the SkillGap FastAPI backend.

Tests all endpoints (/health, /roles, /skills, /analyze, /whatif, /compare),
error validations (format, size, unknown role, empty file),
and enforces latency requirements (< 3s on analyze).
"""

from __future__ import annotations

import io
import time
from typing import Generator

import pytest
from fastapi.testclient import TestClient

from api.cache import analysis_cache
from api.main import app
from config import settings


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    """Provide a TestClient with lifespan context entered."""
    with TestClient(app) as test_client:
        yield test_client


SAMPLE_RESUME_TEXT = """
Jane Doe
Backend Software Engineer

PROFESSIONAL SUMMARY
Experienced backend engineer with 4 years building scalable microservices and APIs.

TECHNICAL SKILLS
Languages: Python, JavaScript, SQL, Bash
Frameworks: FastAPI, Flask, Django
Databases & Tools: PostgreSQL, Redis, Docker, Git, Linux
Cloud: AWS (EC2, S3)

WORK EXPERIENCE
Software Engineer | Acme Corp (2022 - Present)
- Developed RESTful microservices using Python and FastAPI.
- Containerized services with Docker and managed deployments on AWS EC2.
- Optimized PostgreSQL database queries and cached data with Redis.

EDUCATION
B.S. in Computer Science | Tech University
"""


def test_health_endpoint(client: TestClient):
    """Test /health returns healthy status and preloaded models."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "models_loaded" in data
    assert data["models_loaded"]["taxonomy"] is True
    assert data["models_loaded"]["profiles"] is True
    assert data["models_loaded"]["courses"] is True
    assert "use_slm" in data
    assert "ollama_reachable" in data


def test_roles_endpoint(client: TestClient):
    """Test /roles returns canonical roles with posting counts."""
    response = client.get("/roles")
    assert response.status_code == 200
    roles = response.json()
    assert isinstance(roles, list)
    assert len(roles) >= 5

    role_names = [r["role"] for r in roles]
    assert "Backend Developer" in role_names
    assert "Frontend Developer" in role_names

    # Check structure
    sample = roles[0]
    assert "role" in sample
    assert "postings_count" in sample
    assert "core_skills_count" in sample
    assert sample["postings_count"] >= 1


def test_skills_search_endpoint(client: TestClient):
    """Test /skills search works by substring and limit."""
    # Substring search
    resp = client.get("/skills?q=pyth")
    assert resp.status_code == 200
    results = resp.json()
    assert isinstance(results, list)
    assert any(s["skill_id"] == "python" for s in results)

    # Empty search with limit
    resp_all = client.get("/skills?limit=10")
    assert resp_all.status_code == 200
    assert len(resp_all.json()) == 10


def test_analyze_endpoint_with_role(client: TestClient):
    """Test /analyze with valid resume and target role."""
    file_bytes = SAMPLE_RESUME_TEXT.encode("utf-8")

    t0 = time.perf_counter()
    response = client.post(
        "/analyze",
        files={"file": ("resume.txt", file_bytes, "text/plain")},
        data={"role": "Backend Developer"},
    )
    elapsed = time.perf_counter() - t0

    assert response.status_code == 200
    data = response.json()

    # Latency check: must be strictly under 3.0 seconds
    assert elapsed < 3.0, f"Analyze endpoint took {elapsed:.2f}s, expected < 3.0s"
    assert "X-Process-Time" in response.headers

    # Validate schema fields
    assert "analysis_id" in data
    assert len(data["analysis_id"]) > 10

    # Skills check
    extracted = data["extracted_skills"]
    assert len(extracted) > 0
    extracted_ids = [s["skill_id"] for s in extracted]
    assert "python" in extracted_ids
    assert "docker" in extracted_ids

    # Scores
    score = data["score"]
    assert 0 <= score["final"] <= 100
    assert 0 <= score["coverage"] <= 100
    assert 0 <= score["semantic"] <= 100

    # Match components
    assert "covered" in data
    assert "partial" in data
    assert "missing" in data
    assert "category_coverage" in data
    assert "learning_path" in data
    assert "summary_text" in data
    assert len(data["summary_text"]) > 20

    # Verify cache holds ONLY skill IDs (no resume text)
    cached = analysis_cache.get(data["analysis_id"])
    assert cached is not None
    assert "python" in cached["skills"]
    assert "resume_text" not in cached
    assert "content" not in cached


def test_analyze_endpoint_with_custom_jd(client: TestClient):
    """Test /analyze with a custom pasted job description."""
    file_bytes = SAMPLE_RESUME_TEXT.encode("utf-8")
    custom_jd = """
    Job Title: Senior Backend Engineer
    Must have requirements:
    - 3+ years experience with Python and FastAPI
    - Strong database skills in PostgreSQL and Redis
    - Hands-on experience with Kubernetes and Docker
    """

    response = client.post(
        "/analyze",
        files={"file": ("resume.txt", file_bytes, "text/plain")},
        data={"jd": custom_jd},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["analysis_id"] is not None
    assert data["score"]["coverage"] > 0


def test_analyze_endpoint_with_manual_skills(client: TestClient):
    """Test /analyze with manual_skills_add and manual_skills_remove."""
    file_bytes = SAMPLE_RESUME_TEXT.encode("utf-8")

    response = client.post(
        "/analyze",
        files={"file": ("resume.txt", file_bytes, "text/plain")},
        data={
            "role": "Backend Developer",
            "manual_skills_add": "kubernetes,go",
            "manual_skills_remove": "docker",
        },
    )
    assert response.status_code == 200
    data = response.json()
    extracted_ids = [s["skill_id"] for s in data["extracted_skills"]]

    assert "kubernetes" in extracted_ids
    assert "docker" not in extracted_ids


def test_analyze_validation_errors(client: TestClient):
    """Test various validation failure scenarios on /analyze."""
    valid_text = "Experienced Python developer with SQL skills.".encode("utf-8")

    # 1. Neither role nor jd provided
    resp = client.post(
        "/analyze",
        files={"file": ("resume.txt", valid_text, "text/plain")},
        data={},
    )
    assert resp.status_code == 400
    assert "Either 'role' or 'jd' must be provided" in resp.json()["detail"]

    # 2. Unknown role
    resp = client.post(
        "/analyze",
        files={"file": ("resume.txt", valid_text, "text/plain")},
        data={"role": "Quantum Holographic Architect"},
    )
    assert resp.status_code == 400
    assert "Unknown role" in resp.json()["detail"]

    # 3. Unsupported file extension
    resp = client.post(
        "/analyze",
        files={"file": ("malicious.exe", valid_text, "application/octet-stream")},
        data={"role": "Backend Developer"},
    )
    assert resp.status_code == 400
    assert "Unsupported file format" in resp.json()["detail"]

    # 4. Empty file content
    resp = client.post(
        "/analyze",
        files={"file": ("empty.txt", b"", "text/plain")},
        data={"role": "Backend Developer"},
    )
    assert resp.status_code == 400
    assert "empty" in resp.json()["detail"].lower()

    # 5. Oversized file (> 5 MB)
    oversized = b"a" * (6 * 1024 * 1024)
    resp = client.post(
        "/analyze",
        files={"file": ("huge.txt", oversized, "text/plain")},
        data={"role": "Backend Developer"},
    )
    assert resp.status_code == 413
    assert "exceeds maximum allowed limit" in resp.json()["detail"].lower()


def test_whatif_endpoint_with_analysis_id(client: TestClient):
    """Test /whatif simulation using a previous analysis_id."""
    file_bytes = SAMPLE_RESUME_TEXT.encode("utf-8")
    init_resp = client.post(
        "/analyze",
        files={"file": ("resume.txt", file_bytes, "text/plain")},
        data={"role": "Backend Developer"},
    )
    analysis_id = init_resp.json()["analysis_id"]

    sim_resp = client.post(
        "/whatif",
        json={
            "analysis_id": analysis_id,
            "role": "Backend Developer",
            "add": ["kubernetes", "postgresql"],
        },
    )
    assert sim_resp.status_code == 200
    sim_data = sim_resp.json()
    assert "new_score" in sim_data
    assert "delta_coverage" in sim_data
    assert sim_data["delta_coverage"] >= 0.0
    assert sim_data["new_coverage"] >= sim_data["original_coverage"]


def test_whatif_endpoint_with_direct_skills(client: TestClient):
    """Test /whatif simulation with explicit skills list."""
    sim_resp = client.post(
        "/whatif",
        json={
            "skills": ["python"],
            "role": "Backend Developer",
            "add": ["docker"],
        },
    )
    assert sim_resp.status_code == 200
    sim_data = sim_resp.json()
    assert sim_data["delta_coverage"] > 0.0


def test_whatif_unknown_session_or_role(client: TestClient):
    """Test /whatif handles invalid session ID and invalid role."""
    resp = client.post(
        "/whatif",
        json={
            "analysis_id": "non-existent-uuid",
            "role": "Backend Developer",
            "add": ["docker"],
        },
    )
    assert resp.status_code == 404

    resp = client.post(
        "/whatif",
        json={
            "skills": ["python"],
            "role": "Astronaut Developer",
            "add": ["docker"],
        },
    )
    assert resp.status_code == 400


def test_compare_endpoint_json(client: TestClient):
    """Test /compare with JSON skills list."""
    resp = client.post(
        "/compare",
        json={
            "skills": ["python", "sql", "fastapi", "docker"],
            "roles": ["Backend Developer", "Frontend Developer", "Data Analyst"],
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "best_fit_role" in data
    assert "ranked_roles" in data
    assert len(data["ranked_roles"]) == 3
    # Backend Developer should rank higher than Frontend Developer with these skills
    role_order = [r["role"] for r in data["ranked_roles"]]
    assert role_order.index("Backend Developer") < role_order.index("Frontend Developer")


def test_compare_endpoint_multipart(client: TestClient):
    """Test /compare with multipart resume file upload."""
    file_bytes = SAMPLE_RESUME_TEXT.encode("utf-8")
    resp = client.post(
        "/compare",
        files={"file": ("resume.txt", file_bytes, "text/plain")},
        data={"roles": "Backend Developer, Frontend Developer"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["best_fit_role"] is not None
    assert len(data["ranked_roles"]) == 2
