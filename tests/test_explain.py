"""Unit tests for explainability and counterfactual analysis ml/explain.py."""

import pytest

from ml.explain import (
    compare_roles,
    explain_contributions,
    generate_reason,
    rank_gaps_by_impact,
    what_if,
)
from ml.match import gap_analysis
from ml.profiles import RoleProfileManager
from ml.taxonomy import taxonomy


@pytest.fixture(scope="module", autouse=True)
def load_taxonomy():
    taxonomy.load()


@pytest.fixture
def sample_profile():
    return {
        "role": "Backend Developer",
        "n_postings": 10,
        "skills": {
            "python": {"weight": 1.0, "tier": "core"},
            "postgresql": {"weight": 0.8, "tier": "core"},
            "fastapi": {"weight": 0.6, "tier": "common"},
            "docker": {"weight": 0.4, "tier": "common"},
            "redis": {"weight": 0.2, "tier": "bonus"},
        },
    }


def test_contributions_sum_exactly_to_coverage_score(sample_profile):
    """Point contributions from all skills must sum EXACTLY to the coverage score."""
    # Test case 1: Partial candidate (has python and docker)
    # Total weight: 1.0 + 0.8 + 0.6 + 0.4 + 0.2 = 3.0
    # Earned weight: 1.0 + 0.4 = 1.4 -> 1.4 / 3.0 * 100 = 46.6667%
    res = gap_analysis(resume_skills=["python", "docker"], profile=sample_profile)
    contributions = explain_contributions(res, sample_profile)

    # 1. Earned points must sum exactly to coverage_score
    earned_sum = sum(c.points for c in contributions)
    assert earned_sum == pytest.approx(res.coverage_score, abs=1e-2)

    # 2. Points lost must sum to (100.0 - coverage_score)
    lost_sum = sum(abs(c.points_lost) for c in contributions)
    assert lost_sum == pytest.approx(100.0 - res.coverage_score, abs=1e-2)

    # Test case 2: Full candidate (all skills) -> sum is 100.0
    res_full = gap_analysis(resume_skills=list(sample_profile["skills"].keys()), profile=sample_profile)
    contrib_full = explain_contributions(res_full, sample_profile)
    assert sum(c.points for c in contrib_full) == pytest.approx(100.0, abs=1e-2)

    # Test case 3: Empty candidate (no skills) -> sum is 0.0
    res_empty = gap_analysis(resume_skills=[], profile=sample_profile)
    contrib_empty = explain_contributions(res_empty, sample_profile)
    assert sum(c.points for c in contrib_empty) == pytest.approx(0.0, abs=1e-2)


def test_what_if_never_lowers_score(sample_profile):
    """Adding skills via what_if simulation must NEVER lower the score."""
    baseline_skills = ["python"]

    # Test adding each missing skill individually
    for add_skill in ["postgresql", "fastapi", "docker", "redis"]:
        sim = what_if(
            resume_skills=baseline_skills,
            profile=sample_profile,
            add=[add_skill],
        )
        assert sim["delta_coverage"] >= 0.0, f"Delta was negative ({sim['delta_coverage']}) for skill {add_skill}"
        assert sim["new_coverage"] >= sim["original_coverage"]

    # Test adding an already present skill -> delta should be 0.0
    sim_noop = what_if(
        resume_skills=baseline_skills,
        profile=sample_profile,
        add=["python"],
    )
    assert sim_noop["delta_coverage"] == 0.0
    assert sim_noop["new_coverage"] == sim_noop["original_coverage"]

    # Test adding multiple skills simultaneously
    sim_multi = what_if(
        resume_skills=baseline_skills,
        profile=sample_profile,
        add=["postgresql", "fastapi", "docker"],
    )
    assert sim_multi["delta_coverage"] > 0.0
    assert sim_multi["new_coverage"] > sim_multi["original_coverage"]


def test_rank_gaps_by_impact(sample_profile):
    """Missing skills must be prioritized by impact gain (highest score gain first)."""
    # Candidate only has 'redis' (weight 0.2)
    res = gap_analysis(resume_skills=["redis"], profile=sample_profile)
    impacts = rank_gaps_by_impact(res, sample_profile)

    assert len(impacts) == 4
    # The highest impact skill should be python (weight 1.0), then postgresql (0.8), fastapi (0.6), docker (0.4)
    assert impacts[0].skill_id == "python"
    assert impacts[1].skill_id == "postgresql"
    assert impacts[2].skill_id == "fastapi"
    assert impacts[3].skill_id == "docker"

    # Score gains must be non-increasing
    gains = [imp.score_gain for imp in impacts]
    assert gains == sorted(gains, reverse=True)


def test_generate_reason_templates():
    """Verify deterministic plain-English reasons for core missing and covered skills."""
    core_missing = generate_reason(
        skill_id="sql",
        role_name="Data Analyst",
        status="missing",
        weight=0.71,
        tier="core",
    )
    assert "SQL appears in 71% of Data Analyst postings" in core_missing
    assert "You don't list it" in core_missing

    core_covered = generate_reason(
        skill_id="python",
        role_name="Backend Developer",
        status="covered",
        weight=0.90,
        tier="core",
    )
    assert "core requirement" in core_covered
    assert "verified on your resume" in core_covered


def test_compare_roles():
    """Verify compare_roles evaluates candidate across roles and selects the best fit."""
    pm = RoleProfileManager()
    roles = pm.get_canonical_roles()
    if not roles:
        pytest.skip("No cached role profiles found.")

    # Candidate with strong frontend skills
    frontend_skills = ["react", "typescript", "javascript", "html5", "css3"]
    comparison = compare_roles(resume_skills=frontend_skills, roles=roles, profile_manager=pm)

    assert "best_fit_role" in comparison
    assert "ranked_roles" in comparison
    assert len(comparison["ranked_roles"]) > 0

    # Best fit should be Frontend Developer if present
    if "Frontend Developer" in roles:
        assert comparison["best_fit_role"] == "Frontend Developer"
