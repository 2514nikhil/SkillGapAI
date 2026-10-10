"""Robustness and fairness sanity benchmark for SkillGap.

Tests three critical system invariants:
1. Format Invariance: Same resume in different formats (PDF vs DOCX) yields the same skills.
2. Section Order Invariance: Permuting resume sections (Experience before Skills, etc.) produces identical match scores.
3. Monotonicity / Non-Degradation: Adding an irrelevant or additional skill never lowers candidate scores.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Set

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from ml.explain import what_if
from ml.extract import extract_skills
from ml.match import gap_analysis
from ml.parse import parse_resume
from ml.profiles import role_manager
from ml.taxonomy import taxonomy

FIXTURES_DIR = BASE_DIR / "tests" / "fixtures"


def test_format_invariance() -> Dict[str, Any]:
    """Test whether extracting from PDF vs DOCX yields identical skills."""
    pdf_path = FIXTURES_DIR / "sample_resume.pdf"
    docx_path = FIXTURES_DIR / "alice_resume.docx"
    if not docx_path.exists():
        docx_path = FIXTURES_DIR / "sample_resume.docx"

    pdf_text = parse_resume(pdf_path.read_bytes(), pdf_path.name)
    docx_text = parse_resume(docx_path.read_bytes(), docx_path.name)

    pdf_skills = set(extract_skills(pdf_text, mode="hybrid").skills)
    docx_skills = set(extract_skills(docx_text, mode="hybrid").skills)

    intersection = pdf_skills & docx_skills
    union = pdf_skills | docx_skills
    jaccard = len(intersection) / len(union) if union else 1.0

    return {
        "test": "Format Invariance (PDF vs DOCX)",
        "pdf_skills_count": len(pdf_skills),
        "docx_skills_count": len(docx_skills),
        "overlap_count": len(intersection),
        "jaccard_similarity": round(jaccard, 4),
        "status": "PASS" if jaccard >= 0.85 else "WARN",
    }


def test_section_order_invariance() -> Dict[str, Any]:
    """Test whether reordering resume sections affects the deterministic score."""
    role_manager.load()
    prof = role_manager.get_role_profile("Backend Developer")
    if not prof:
        raise ValueError("Profile for Backend Developer not found.")

    section_skills = "TECHNICAL SKILLS\nLanguages: Python, SQL, Bash\nFrameworks: FastAPI, Flask\nDatabases: PostgreSQL, Redis\nTools: Docker, Git"
    section_summary = "PROFESSIONAL SUMMARY\nSenior Backend Software Engineer with 5 years building scalable web services."
    section_exp = "WORK EXPERIENCE\nSenior Software Engineer at CloudApp (2020-Present)\nDeveloped RESTful microservices with Python, FastAPI, and Docker."
    section_edu = "EDUCATION\nB.S. in Computer Science, State Tech University"

    # Variant A: Standard (Summary -> Skills -> Experience -> Education)
    order_a = f"{section_summary}\n\n{section_skills}\n\n{section_exp}\n\n{section_edu}"
    # Variant B: Inverted (Experience -> Skills -> Education -> Summary)
    order_b = f"{section_exp}\n\n{section_skills}\n\n{section_edu}\n\n{section_summary}"
    # Variant C: Skills at the bottom (Summary -> Experience -> Education -> Skills)
    order_c = f"{section_summary}\n\n{section_exp}\n\n{section_edu}\n\n{section_skills}"

    skills_a = extract_skills(order_a, mode="hybrid").skills
    skills_b = extract_skills(order_b, mode="hybrid").skills
    skills_c = extract_skills(order_c, mode="hybrid").skills

    res_a = gap_analysis(skills_a, prof, skill_emb=taxonomy)
    res_b = gap_analysis(skills_b, prof, skill_emb=taxonomy)
    res_c = gap_analysis(skills_c, prof, skill_emb=taxonomy)

    score_diff_ab = abs(res_a.coverage_score - res_b.coverage_score)
    score_diff_ac = abs(res_a.coverage_score - res_c.coverage_score)
    is_identical = (score_diff_ab < 1e-4) and (score_diff_ac < 1e-4)

    return {
        "test": "Section Order Invariance",
        "score_variant_a": res_a.coverage_score,
        "score_variant_b": res_b.coverage_score,
        "score_variant_c": res_c.coverage_score,
        "max_score_difference": max(score_diff_ab, score_diff_ac),
        "status": "PASS" if is_identical else "FAIL",
    }


def test_monotonicity() -> Dict[str, Any]:
    """Verify that adding any skill (relevant or irrelevant) never reduces coverage score."""
    role_manager.load()
    prof = role_manager.get_role_profile("Backend Developer")
    if not prof:
        raise ValueError("Profile for Backend Developer not found.")

    base_skills = ["python", "sql", "git"]
    base_res = gap_analysis(base_skills, prof, skill_emb=taxonomy)
    base_score = base_res.coverage_score

    test_additions = [
        ("docker", "Core Demanded Skill"),
        ("fastapi", "Core Demanded Skill"),
        ("figma", "Irrelevant Design Skill"),
        ("scrum", "Adjacent Non-Core Skill"),
        ("gardening", "Completely Unrelated Term"),
    ]

    violations: List[str] = []
    checks: List[Dict[str, Any]] = []

    for sid, desc in test_additions:
        sim = what_if(
            resume_skills=base_skills,
            profile=prof,
            add=[sid],
            skill_emb=taxonomy,
        )
        delta = sim["delta_coverage"]
        new_score = sim["new_coverage"]

        if new_score < base_score:
            violations.append(sid)

        checks.append({
            "added_skill": sid,
            "type": desc,
            "base_score": base_score,
            "new_score": new_score,
            "delta": delta,
        })

    return {
        "test": "Monotonicity (Non-Degradation)",
        "base_score": base_score,
        "checks": checks,
        "violations_count": len(violations),
        "status": "PASS" if len(violations) == 0 else "FAIL",
    }


def run_robustness_sanity_checks() -> Dict[str, Any]:
    """Execute all fairness and robustness checks and print formatted report."""
    taxonomy.load()

    res_format = test_format_invariance()
    res_order = test_section_order_invariance()
    res_mono = test_monotonicity()

    print("\n" + "=" * 80)
    print("FAIRNESS & ROBUSTNESS SANITY BENCHMARK")
    print("=" * 80)

    # 1. Format invariance
    print(f"1. {res_format['test']}: [{res_format['status']}]")
    print(f"   PDF Skills Detected : {res_format['pdf_skills_count']}")
    print(f"   DOCX Skills Detected: {res_format['docx_skills_count']}")
    print(f"   Overlap             : {res_format['overlap_count']} (Jaccard: {res_format['jaccard_similarity']})")

    # 2. Section order invariance
    print(f"\n2. {res_order['test']}: [{res_order['status']}]")
    print(f"   Variant A (Summary -> Skills -> Exp -> Edu): {res_order['score_variant_a']:.2f}%")
    print(f"   Variant B (Exp -> Skills -> Edu -> Summary): {res_order['score_variant_b']:.2f}%")
    print(f"   Variant C (Summary -> Exp -> Edu -> Skills): {res_order['score_variant_c']:.2f}%")
    print(f"   Max Score Delta                             : {res_order['max_score_difference']:.4f}")

    # 3. Monotonicity
    print(f"\n3. {res_mono['test']}: [{res_mono['status']}]")
    print(f"   Baseline Score: {res_mono['base_score']:.2f}%")
    for chk in res_mono["checks"]:
        print(f"   + '{chk['added_skill']}' ({chk['type']}): New Score {chk['new_score']:.2f}% (Delta: +{chk['delta']:.2f})")

    print("=" * 80)

    return {
        "format_invariance": res_format,
        "section_order_invariance": res_order,
        "monotonicity": res_mono,
    }


if __name__ == "__main__":
    run_robustness_sanity_checks()
