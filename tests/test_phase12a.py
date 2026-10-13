"""Unit and integration tests for Phase 12A:
- Tech catalog integrity (no duplicate ids, unique aliases, taxonomy_id resolution)
- Social platforms definitions and URL build/extract roundtrips
- Resume schema validation (mandatory fields, date formats, bullet limits, HTML stripping, forbidden PII rejection)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pytest
from pydantic import ValidationError

from config import settings
from ml.resume_schema import Resume, export_json_schema
from ml.socials import build_url, extract_value, get_platform, load_platforms, validate_value

BASE_DIR = Path(__file__).resolve().parent.parent
CATALOG_FILE = settings.DATA_DIR / "processed" / "tech_catalog.json"
PLATFORMS_FILE = settings.DATA_DIR / "processed" / "social_platforms.json"
SKILLS_FILE = settings.SKILLS_FILE
EMBEDDINGS_FILE = settings.SKILL_EMBEDDINGS_FILE
SKILL_IDS_FILE = settings.SKILL_IDS_FILE

REQUIRED_CATEGORIES = [
    "languages",
    "hosting_cloud",
    "frameworks_libraries",
    "servers_runtime",
    "databases_orm",
    "design_tools",
    "ml_dl_data",
    "cicd_vcs",
    "testing",
    "data_bi_analytics",
    "mobile",
    "security_networking",
    "os_systems",
    "other_tools",
    "soft_skills",
]


# =========================================================================
# 1. Tech Catalog Tests
# =========================================================================

def test_catalog_file_exists_and_categories_order():
    """Assert tech catalog exists and categories follow exact required sequence."""
    assert CATALOG_FILE.is_file(), f"Catalog file missing at {CATALOG_FILE}"
    with open(CATALOG_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "categories" in data
    cats = data["categories"]
    assert len(cats) == 15

    cat_ids = [c["id"] for c in cats]
    assert cat_ids == REQUIRED_CATEGORIES, f"Category order mismatch: {cat_ids}"


def test_catalog_minimum_700_entries():
    """Assert catalog contains at least 700 total entries."""
    with open(CATALOG_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    total_skills = sum(len(c.get("skills", [])) for c in data["categories"])
    assert total_skills >= 700, f"Expected at least 700 catalog entries, found {total_skills}"


def test_catalog_no_duplicate_ids():
    """Assert no duplicate skill IDs exist across the entire catalog."""
    with open(CATALOG_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    all_ids: List[str] = []
    for cat in data["categories"]:
        for skill in cat["skills"]:
            all_ids.append(skill["id"])

    duplicates = [sid for sid in set(all_ids) if all_ids.count(sid) > 1]
    assert not duplicates, f"Found duplicate IDs in catalog: {duplicates}"


def test_catalog_globally_unique_aliases():
    """Assert every alias is unique across the entire catalog and does not clash with any skill ID."""
    with open(CATALOG_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    all_ids = set()
    for cat in data["categories"]:
        for skill in cat["skills"]:
            all_ids.add(skill["id"])

    claimed_aliases: Dict[str, str] = {}
    clashes_with_id = []
    duplicate_aliases = []

    for cat in data["categories"]:
        for skill in cat["skills"]:
            sid = skill["id"]
            for a in skill.get("aliases", []):
                if a in all_ids:
                    clashes_with_id.append((a, sid))
                if a in claimed_aliases:
                    duplicate_aliases.append((a, sid, claimed_aliases[a]))
                claimed_aliases[a] = sid

    assert not clashes_with_id, f"Aliases clashing with skill IDs: {clashes_with_id}"
    assert not duplicate_aliases, f"Duplicate aliases across catalog: {duplicate_aliases}"


def test_catalog_taxonomy_id_resolves():
    """Assert every skill has a taxonomy_id that points to an existing key in skills.json."""
    with open(CATALOG_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    with open(SKILLS_FILE, "r", encoding="utf-8") as f:
        taxonomy = json.load(f)

    unresolved = []
    for cat in data["categories"]:
        for skill in cat["skills"]:
            tid = skill.get("taxonomy_id")
            if not tid or tid not in taxonomy:
                unresolved.append((skill["id"], tid))

    assert not unresolved, f"Unresolved taxonomy IDs: {unresolved[:10]}"


def test_taxonomy_and_embeddings_alignment():
    """Assert skills.json and skill_embeddings.npy have matching dimensions."""
    with open(SKILLS_FILE, "r", encoding="utf-8") as f:
        taxonomy = json.load(f)
    with open(SKILL_IDS_FILE, "r", encoding="utf-8") as f:
        skill_ids = json.load(f)
    embeddings = np.load(EMBEDDINGS_FILE)

    assert len(taxonomy) == len(skill_ids) == len(embeddings), (
        f"Alignment mismatch: taxonomy={len(taxonomy)}, ids={len(skill_ids)}, embeddings={len(embeddings)}"
    )


# =========================================================================
# 2. Social Platforms Tests
# =========================================================================

EXPECTED_PLATFORMS = [
    "email", "phone", "linkedin", "github", "portfolio",
    "leetcode", "kaggle", "huggingface", "google_scholar", "medium",
    "stackoverflow", "behance", "codepen", "x", "bluesky",
    "mastodon", "youtube", "discord", "reddit", "quora",
    "instagram", "facebook", "tiktok", "twitch", "pinterest"
]

NON_RESUME_FRIENDLY = {
    "facebook", "instagram", "tiktok", "twitch", "pinterest", "discord", "reddit", "quora"
}

DEFAULT_VISIBLE = {"email", "phone", "linkedin", "github", "portfolio"}


def test_social_platforms_definition_completeness():
    """Verify all 25 platforms are defined with required attributes."""
    platforms = load_platforms()
    assert len(platforms) == 25
    for pid in EXPECTED_PLATFORMS:
        assert pid in platforms, f"Missing platform '{pid}'"
        p = platforms[pid]
        assert p["id"] == pid
        assert p["label"]
        assert p["input_label"]
        assert p["placeholder"]
        assert p["url_template"]
        assert p["accepts_full_url"] is True

        if pid in DEFAULT_VISIBLE:
            assert p["default_visible"] is True, f"{pid} should be default_visible"
        else:
            assert p["default_visible"] is False, f"{pid} should not be default_visible"

        if pid in NON_RESUME_FRIENDLY:
            assert p["resume_friendly"] is False, f"{pid} should have resume_friendly=False"
            assert p["hint"] is not None and len(p["hint"]) > 10
        else:
            assert p["resume_friendly"] is True, f"{pid} should have resume_friendly=True"
            assert p["hint"] is None


@pytest.mark.parametrize(
    "pid,raw_username,full_url,expected_val,expected_url",
    [
        ("email", "dev@example.com", "mailto:dev@example.com?subject=Hi", "dev@example.com", "mailto:dev@example.com"),
        ("phone", "+15550199", "tel:+15550199", "+15550199", "tel:+15550199"),
        ("linkedin", "nikhil-m", "https://www.linkedin.com/in/nikhil-m?trk=profile", "nikhil-m", "https://linkedin.com/in/nikhil-m"),
        ("github", "@2514nikhil", "https://github.com/2514nikhil/", "2514nikhil", "https://github.com/2514nikhil"),
        ("portfolio", "nikhil.dev", "https://nikhil.dev/?ref=resume", "https://nikhil.dev", "https://nikhil.dev"),
        ("leetcode", "top_coder", "https://leetcode.com/u/top_coder/", "top_coder", "https://leetcode.com/u/top_coder"),
        ("kaggle", "ml_expert", "https://www.kaggle.com/ml_expert", "ml_expert", "https://kaggle.com/ml_expert"),
        ("huggingface", "deepmind_fan", "https://huggingface.co/deepmind_fan", "deepmind_fan", "https://huggingface.co/deepmind_fan"),
        ("google_scholar", "qc6CJjYAAAAJ", "https://scholar.google.com/citations?user=qc6CJjYAAAAJ&hl=en", "qc6CJjYAAAAJ", "https://scholar.google.com/citations?user=qc6CJjYAAAAJ"),
        ("medium", "@johndoe", "https://medium.com/@johndoe?source=rss", "johndoe", "https://medium.com/@johndoe"),
        ("stackoverflow", "123456", "https://stackoverflow.com/users/123456/john-skeet", "123456", "https://stackoverflow.com/users/123456"),
        ("behance", "art_design", "https://www.behance.net/art_design/", "art_design", "https://behance.net/art_design"),
        ("codepen", "css_master", "https://codepen.io/css_master", "css_master", "https://codepen.io/css_master"),
        ("x", "@elonmusk", "https://x.com/elonmusk?s=20", "elonmusk", "https://x.com/elonmusk"),
        ("bluesky", "alice.bsky.social", "https://bsky.app/profile/alice.bsky.social", "alice.bsky.social", "https://bsky.app/profile/alice.bsky.social"),
        ("mastodon", "user@mastodon.social", "https://mastodon.social/@user", "user@mastodon.social", "https://mastodon.social/@user"),
        ("youtube", "@Veritasium", "https://youtube.com/@Veritasium", "@Veritasium", "https://youtube.com/@Veritasium"),
        ("discord", "pythondiscord", "https://discord.gg/pythondiscord", "pythondiscord", "https://discord.gg/pythondiscord"),
        ("reddit", "spez", "https://www.reddit.com/user/spez/", "spez", "https://reddit.com/user/spez"),
        ("quora", "Adam-DAngelo", "https://www.quora.com/profile/Adam-DAngelo", "Adam-DAngelo", "https://quora.com/profile/Adam-DAngelo"),
        ("instagram", "@natgeo", "https://instagram.com/natgeo/", "natgeo", "https://instagram.com/natgeo"),
        ("facebook", "markzuck", "https://facebook.com/markzuck", "markzuck", "https://facebook.com/markzuck"),
        ("tiktok", "@creative", "https://www.tiktok.com/@creative?lang=en", "creative", "https://tiktok.com/@creative"),
        ("twitch", "ninja", "https://twitch.tv/ninja", "ninja", "https://twitch.tv/ninja"),
        ("pinterest", "designideas", "https://pinterest.com/designideas/", "designideas", "https://pinterest.com/designideas"),
    ],
)
def test_social_round_trips(pid, raw_username, full_url, expected_val, expected_url):
    """Test extract_value and build_url roundtrips for all 25 platforms."""
    # Test from username/handle
    val_from_handle = extract_value(pid, raw_username)
    assert val_from_handle == expected_val, f"Handle extraction failed for {pid}: got {val_from_handle}"
    url_from_handle = build_url(pid, raw_username)
    assert url_from_handle == expected_url, f"Build URL from handle failed for {pid}: got {url_from_handle}"

    # Test from full URL
    val_from_url = extract_value(pid, full_url)
    assert val_from_url == expected_val, f"URL extraction failed for {pid}: got {val_from_url}"
    url_from_url = build_url(pid, full_url)
    assert url_from_url == expected_url, f"Build URL from url failed for {pid}: got {url_from_url}"


# =========================================================================
# 3. Resume Schema Tests
# =========================================================================

def test_resume_fixtures_validation():
    """Verify both example fixtures validate against Resume schema."""
    with open(BASE_DIR / "tests" / "fixtures" / "resume_example_1.json", "r", encoding="utf-8") as f:
        r1_data = json.load(f)
    r1 = Resume.model_validate(r1_data)
    assert r1.basics.name == "Nikhil Maghodiya"
    assert len(r1.skills) == 12

    with open(BASE_DIR / "tests" / "fixtures" / "resume_example_2.json", "r", encoding="utf-8") as f:
        r2_data = json.load(f)
    r2 = Resume.model_validate(r2_data)
    assert r2.basics.name == "Jane Doe"
    assert len(r2.projects) == 1


def test_resume_minimal_valid():
    """Verify that only name and email are strictly mandatory."""
    minimal = {
        "basics": {
            "name": "Alex Smith",
            "email": "alex@example.com"
        }
    }
    r = Resume.model_validate(minimal)
    assert r.basics.name == "Alex Smith"
    assert r.basics.email == "alex@example.com"
    assert r.skills == []
    assert r.experience == []
    assert r.projects == []


def test_resume_missing_name_or_email_fails():
    """Verify that missing name or missing email raises ValidationError."""
    with pytest.raises(ValidationError):
        Resume.model_validate({"basics": {"email": "alex@example.com"}})

    with pytest.raises(ValidationError):
        Resume.model_validate({"basics": {"name": "Alex"}})

    with pytest.raises(ValidationError):
        Resume.model_validate({"basics": {"name": "Alex", "email": "invalid-email"}})


def test_resume_html_and_control_chars_stripped():
    """Verify HTML tags and control characters are stripped automatically."""
    data = {
        "basics": {
            "name": "<b>John</b> <i>Doe</i>\x00\x1f",
            "email": "john@example.com",
            "headline": "<script>alert('xss')</script>Senior Engineer"
        },
        "summary": "<p>Experienced in <strong>FastAPI</strong> &amp; Python.</p>",
        "experience": [
            {
                "company": "<span>Acme Corp</span>",
                "title": "Engineer",
                "bullets": ["Managed <b>Kubernetes</b> & microservices.\x07"]
            }
        ]
    }
    r = Resume.model_validate(data)
    assert r.basics.name == "John Doe"
    assert r.basics.headline == "alert('xss')Senior Engineer"
    assert r.summary == "Experienced in FastAPI & Python."
    assert r.experience[0].company == "Acme Corp"
    assert r.experience[0].bullets[0] == "Managed Kubernetes & microservices."


def test_resume_date_validation():
    """Verify valid date formats (YYYY-MM, YYYY, Present) and rejection of invalid formats."""
    valid_data = {
        "basics": {"name": "Sam", "email": "sam@example.com"},
        "experience": [
            {
                "company": "Google",
                "title": "SWE",
                "start": "2021-04",
                "end": "Present",
                "current": True,
            },
            {
                "company": "Amazon",
                "title": "Intern",
                "start": "2020",
                "end": "2021",
                "current": False,
            }
        ]
    }
    r = Resume.model_validate(valid_data)
    assert r.experience[0].start == "2021-04"
    assert r.experience[0].end == "Present"

    # Invalid dates
    invalid_dates = ["04/2021", "2021/04", "April 2021", "yesterday", "2021-4"]
    for bad_date in invalid_dates:
        bad_data = {
            "basics": {"name": "Sam", "email": "sam@example.com"},
            "experience": [
                {"company": "Google", "title": "SWE", "start": bad_date}
            ]
        }
        with pytest.raises(ValidationError):
            Resume.model_validate(bad_data)


def test_resume_bullet_length_limit():
    """Verify bullet length limit <= 300 chars."""
    long_bullet = "A" * 301
    bad_data = {
        "basics": {"name": "Sam", "email": "sam@example.com"},
        "experience": [
            {"company": "Google", "title": "SWE", "bullets": [long_bullet]}
        ]
    }
    with pytest.raises(ValidationError):
        Resume.model_validate(bad_data)


def test_resume_bullet_count_limit():
    """Verify maximum 8 bullets per item."""
    bullets = [f"Bullet {i}" for i in range(9)]
    bad_data = {
        "basics": {"name": "Sam", "email": "sam@example.com"},
        "experience": [
            {"company": "Google", "title": "SWE", "bullets": bullets}
        ]
    }
    with pytest.raises(ValidationError):
        Resume.model_validate(bad_data)


def test_resume_max_skills_limit():
    """Verify maximum 150 skills."""
    skills = [
        {"category_id": "languages", "name": f"Skill {i}"}
        for i in range(151)
    ]
    bad_data = {
        "basics": {"name": "Sam", "email": "sam@example.com"},
        "skills": skills
    }
    with pytest.raises(ValidationError):
        Resume.model_validate(bad_data)


def test_resume_forbidden_pii_fields_rejected():
    """Verify that forbidden demographic or personal PII fields are strictly rejected."""
    forbidden_keys = [
        "photo", "avatar", "dob", "date_of_birth", "gender",
        "marital_status", "religion", "nationality", "home_address",
        "ssn", "aadhaar"
    ]
    for key in forbidden_keys:
        bad_data = {
            "basics": {
                "name": "Sam",
                "email": "sam@example.com",
                key: "sensitive_value"
            }
        }
        with pytest.raises(ValidationError):
            Resume.model_validate(bad_data)

    # Extra top-level fields also rejected by extra="forbid"
    with pytest.raises(ValidationError):
        Resume.model_validate({
            "basics": {"name": "Sam", "email": "sam@example.com"},
            "random_extra_field": "not_allowed"
        })
