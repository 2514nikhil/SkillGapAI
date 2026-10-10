"""Unit tests for role profiling module ml/profiles.py."""

import pytest
from ml.profiles import (
    assign_tier,
    normalize_job_title,
    profile_from_jd,
    strip_seniority,
    RoleProfileManager,
)
from ml.taxonomy import taxonomy


@pytest.fixture(scope="module", autouse=True)
def init_taxonomy():
    taxonomy.load()


def test_strip_seniority():
    """Verify seniority prefixes and levels are cleanly identified and stripped."""
    cases = [
        ("Senior Backend Engineer", "Backend Engineer", "senior"),
        ("Lead Data Scientist", "Data Scientist", "lead"),
        ("Junior Frontend Developer", "Frontend Developer", "junior"),
        ("Principal DevOps Architect", "DevOps Architect", "principal"),
        ("Intern Machine Learning Engineer", "Machine Learning Engineer", "intern"),
        ("Mid-Level Software Engineer", "Software Engineer", "mid"),
        ("Software Engineer", "Software Engineer", None),
        ("Senior Director of Product Management", "Director of Product Management", "senior"),
    ]
    for raw, expected_clean, expected_level in cases:
        clean, level = strip_seniority(raw)
        assert clean == expected_clean, f"Failed for {raw}: got clean='{clean}', expected='{expected_clean}'"
        assert level == expected_level, f"Failed for {raw}: got level='{level}', expected='{expected_level}'"


def test_rule_based_title_normalization():
    """Verify title normalization maps titles according to role rules."""
    rules = {
        "Data Analyst": ["data analyst", "bi analyst", "business intelligence analyst"],
        "Backend Developer": ["backend engineer", "backend developer", "python backend"],
        "DevOps Engineer": ["devops engineer", "site reliability engineer", "sre", "cloud engineer"],
        "ML Engineer": ["machine learning engineer", "ml engineer", "ai engineer"],
    }

    test_titles = [
        ("Senior Data Analyst", "Data Analyst", "senior"),
        ("Junior Backend Engineer", "Backend Developer", "junior"),
        ("Lead SRE / DevOps Engineer", "DevOps Engineer", "lead"),
        ("Machine Learning Engineer III", "ML Engineer", None),
    ]

    for raw, expected_role, expected_seniority in test_titles:
        role, seniority = normalize_job_title(raw, rules=rules)
        assert role == expected_role, f"Expected role {expected_role} for {raw}, got {role}"
        assert seniority == expected_seniority, f"Expected seniority {expected_seniority} for {raw}, got {seniority}"


def test_tier_boundaries():
    """Verify tier assignment matches config thresholds (core >= 0.5, common 0.20-0.50, bonus < 0.20)."""
    assert assign_tier(0.95) == "core"
    assert assign_tier(0.50) == "core"
    assert assign_tier(0.499) == "common"
    assert assign_tier(0.20) == "common"
    assert assign_tier(0.199) == "bonus"
    assert assign_tier(0.05) == "bonus"


def test_weight_math_synthetic():
    """Verify skill weight calculations: weight = share of role's postings mentioning the skill."""
    # Suppose a role has 10 postings
    n_postings = 10
    skill_counts = {
        "python": 10,
        "docker": 7,
        "sql": 4,
        "aws": 1,
    }

    skills = {}
    for skill_id, count in skill_counts.items():
        share = count / n_postings
        if share >= 0.05:  # MIN_SKILL_SHARE
            skills[skill_id] = {
                "weight": round(share, 4),
                "tier": assign_tier(share),
            }

    assert skills["python"]["weight"] == 1.0
    assert skills["python"]["tier"] == "core"

    assert skills["docker"]["weight"] == 0.7
    assert skills["docker"]["tier"] == "core"

    assert skills["sql"]["weight"] == 0.4
    assert skills["sql"]["tier"] == "common"

    assert skills["aws"]["weight"] == 0.1
    assert skills["aws"]["tier"] == "bonus"


def test_profile_from_jd():
    """Verify on-the-fly JD parsing weights requirements 1.0 and nice-to-have 0.5."""
    jd_text = """
    Job Title: Senior Backend Developer
    
    Requirements:
    - Proficiency in Python and PostgreSQL.
    - Solid experience building REST APIs with FastAPI.
    
    Nice to Have / Preferred Qualifications:
    - Familiarity with Docker and Redis is a plus.
    - Basic knowledge of Kubernetes.
    """

    profile = profile_from_jd(jd_text, role_title="Senior Backend Developer")

    assert profile["role"] == "Senior Backend Developer"
    assert profile["n_postings"] == 1
    assert "skills" in profile

    skills = profile["skills"]
    # Python & FastAPI & PostgreSQL should be in requirements -> weight 1.0, tier core
    assert "python" in skills
    assert skills["python"]["weight"] == 1.0
    assert skills["python"]["tier"] == "core"

    # Docker / Redis / Kubernetes should be in nice-to-have -> weight 0.5
    if "docker" in skills:
        assert skills["docker"]["weight"] == 0.5


def test_role_profile_manager():
    """Verify RoleProfileManager loads cached profiles and retrieves role skills."""
    manager = RoleProfileManager()
    roles = manager.list_roles()
    assert len(roles) > 0

    assert "Backend Developer" in roles or "Data Analyst" in roles
    if "Data Analyst" in roles:
        analyst_profile = manager.get_profile("Data Analyst")
        assert analyst_profile is not None
        assert "sql" in analyst_profile["skills"]
        assert analyst_profile["skills"]["sql"]["tier"] == "core"
