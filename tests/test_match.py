"""Unit tests for deterministic matching engine ml/match.py."""

import numpy as np
import pytest

from config import settings
from ml.match import calibrate_semantic_score, gap_analysis
from ml.taxonomy import taxonomy


@pytest.fixture(scope="module", autouse=True)
def load_taxonomy():
    taxonomy.load()


@pytest.fixture
def synthetic_profile():
    """Synthetic role profile for deterministic math verification."""
    return {
        "role": "Data Engineer",
        "n_postings": 10,
        "skills": {
            "python": {"weight": 1.0, "tier": "core", "category": "programming"},
            "sql": {"weight": 0.8, "tier": "core", "category": "data"},
            "docker": {"weight": 0.6, "tier": "common", "category": "devops"},
            "spark": {"weight": 0.4, "tier": "common", "category": "data"},
            "snowflake": {"weight": 0.2, "tier": "bonus", "category": "data"},
        },
    }


def test_score_is_100_when_covering_all(synthetic_profile):
    """Score must be exactly 100.0 when all demanded skills are present."""
    all_skills = list(synthetic_profile["skills"].keys())
    res = gap_analysis(resume_skills=all_skills, profile=synthetic_profile)

    assert res.coverage_score == 100.0
    assert res.final_score == 100.0
    assert len(res.exact_matches) == 5
    assert len(res.partial_matches) == 0
    assert len(res.missing_skills) == 0
    assert res.earned_weight == res.total_weight


def test_score_is_0_when_no_skills(synthetic_profile):
    """Coverage score must be exactly 0.0 when candidate has no matching skills."""
    res = gap_analysis(resume_skills=[], profile=synthetic_profile)

    assert res.coverage_score == 0.0
    assert len(res.exact_matches) == 0
    assert len(res.partial_matches) == 0
    assert len(res.missing_skills) == 5
    assert res.earned_weight == 0.0


def test_partial_credit_logic():
    """Verify that a candidate skill with cosine >= 0.80 earns 0.5 * weight partial credit."""
    # Create two synthetic 2D unit vectors with known cosine similarity
    # Cosine = cos(theta). For cos(theta) = 0.85, theta ~ 0.55 rad
    # Let v1 = (1, 0), v2 = (0.85, sqrt(1 - 0.85^2))
    v_demanded = np.array([1.0, 0.0])
    v_related = np.array([0.85, np.sqrt(1 - 0.85**2)])  # dot product = 0.85 >= 0.80 threshold
    v_unrelated = np.array([0.2, np.sqrt(1 - 0.2**2)])  # dot product = 0.20 < 0.80 threshold

    mock_embeddings = {
        "demanded_skill": v_demanded,
        "related_skill": v_related,
        "unrelated_skill": v_unrelated,
    }

    profile = {
        "role": "Specialist",
        "skills": {
            "demanded_skill": {"weight": 1.0, "tier": "core"},
        },
    }

    # Case 1: Candidate has related skill -> partial credit awarded (0.5 * 1.0 = 0.5 earned weight -> 50%)
    res_partial = gap_analysis(
        resume_skills=["related_skill"],
        profile=profile,
        skill_emb=mock_embeddings,
    )
    assert len(res_partial.partial_matches) == 1
    assert res_partial.partial_matches[0].skill_id == "demanded_skill"
    assert res_partial.partial_matches[0].covered_by == "related_skill"
    assert res_partial.partial_matches[0].earned_weight == 0.5
    assert res_partial.coverage_score == 50.0

    # Case 2: Candidate has unrelated skill -> no credit awarded (0.0 earned weight -> 0%)
    res_none = gap_analysis(
        resume_skills=["unrelated_skill"],
        profile=profile,
        skill_emb=mock_embeddings,
    )
    assert len(res_none.partial_matches) == 0
    assert len(res_none.missing_skills) == 1
    assert res_none.coverage_score == 0.0


def test_ordering_of_gaps(synthetic_profile):
    """Missing skills must be strictly sorted by weight descending."""
    res = gap_analysis(resume_skills=["python"], profile=synthetic_profile)

    assert len(res.missing_skills) == 4
    weights = [ms.weight for ms in res.missing_skills]
    # Expected order: sql (0.8), docker (0.6), spark (0.4), snowflake (0.2)
    assert weights == sorted(weights, reverse=True)
    assert res.missing_skills[0].skill_id == "sql"
    assert res.missing_skills[-1].skill_id == "snowflake"


def test_category_coverage(synthetic_profile):
    """Category breakdown must accurately aggregate weights and compute percentages."""
    # Candidate has python (programming, w=1.0) and sql (data, w=0.8)
    # Total data weight: sql(0.8) + spark(0.4) + snowflake(0.2) = 1.4
    # Earned data weight: sql(0.8) -> 0.8 / 1.4 = 57.14%
    res = gap_analysis(resume_skills=["python", "sql"], profile=synthetic_profile)

    assert "programming" in res.categories
    assert "data" in res.categories
    assert "devops" in res.categories

    prog_cat = res.categories["programming"]
    assert prog_cat.coverage_score == 100.0
    assert prog_cat.earned_weight == 1.0

    data_cat = res.categories["data"]
    expected_data_cov = round((0.8 / 1.4) * 100.0, 2)
    assert data_cat.coverage_score == expected_data_cov

    devops_cat = res.categories["devops"]
    assert devops_cat.coverage_score == 0.0


def test_semantic_score_calibration():
    """Verify semantic calibration clamps between 0.0 and 100.0."""
    min_c = settings.SEMANTIC_MIN_COSINE
    max_c = settings.SEMANTIC_MAX_COSINE

    assert calibrate_semantic_score(min_c, min_c, max_c) == 0.0
    assert calibrate_semantic_score(max_c, min_c, max_c) == 100.0
    assert calibrate_semantic_score(-0.5, min_c, max_c) == 0.0
    assert calibrate_semantic_score(1.0, min_c, max_c) == 100.0
    mid = (min_c + max_c) / 2.0
    assert calibrate_semantic_score(mid, min_c, max_c) == pytest.approx(50.0)
