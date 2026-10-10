"""Sensitivity analysis benchmark for SkillGap.

Evaluates how candidate scores and match behavior vary across:
1. PARTIAL_THRESHOLD (semantic similarity cutoff for awarding 50% partial credit)
2. MIN_SKILL_SHARE (frequency cutoff for retaining a skill in empirical role profiles)
3. W_COVERAGE (weight balance between deterministic skill coverage and semantic embedding alignment)
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config import Settings, settings
from ml.data_io import load_resumes
from ml.extract import extract_skills
from ml.match import gap_analysis
from ml.profiles import role_manager
from ml.taxonomy import taxonomy


def evaluate_partial_threshold_sensitivity(
    candidate_skills_list: List[List[str]],
    role_profile: Dict[str, Any],
    thresholds: List[float] = [0.70, 0.75, 0.80, 0.85, 0.90],
) -> List[Dict[str, Any]]:
    """Analyze impact of PARTIAL_THRESHOLD on coverage score and partial match count."""
    rows: List[Dict[str, Any]] = []

    for thresh in thresholds:
        cfg = Settings(PARTIAL_THRESHOLD=thresh)
        scores: List[float] = []
        partial_counts: List[int] = []

        for c_skills in candidate_skills_list:
            res = gap_analysis(
                resume_skills=c_skills,
                profile=role_profile,
                skill_emb=taxonomy,
                cfg=cfg,
            )
            scores.append(res.coverage_score)
            partial_counts.append(len(res.partial_matches))

        rows.append({
            "partial_threshold": thresh,
            "avg_coverage_score": round(float(np.mean(scores)), 2),
            "avg_partial_matches": round(float(np.mean(partial_counts)), 2),
        })

    return rows


def evaluate_min_skill_share_sensitivity(
    candidate_skills_list: List[List[str]],
    raw_role_profile: Dict[str, Any],
    cutoffs: List[float] = [0.05, 0.10, 0.15, 0.20, 0.25],
) -> List[Dict[str, Any]]:
    """Analyze impact of MIN_SKILL_SHARE on profile size and candidate coverage."""
    rows: List[Dict[str, Any]] = []
    base_skills = raw_role_profile.get("skills", {})

    for cutoff in cutoffs:
        # Filter skills below cutoff
        filtered_skills = {
            sid: data for sid, data in base_skills.items()
            if data.get("weight", 0.0) >= cutoff
        }
        test_profile = {
            "role": raw_role_profile.get("role", "Target Role"),
            "n_postings": raw_role_profile.get("n_postings", 1),
            "skills": filtered_skills,
        }

        scores: List[float] = []
        for c_skills in candidate_skills_list:
            res = gap_analysis(
                resume_skills=c_skills,
                profile=test_profile,
                skill_emb=taxonomy,
            )
            scores.append(res.coverage_score)

        rows.append({
            "min_skill_share": cutoff,
            "skills_in_profile": len(filtered_skills),
            "avg_coverage_score": round(float(np.mean(scores)), 2),
        })

    return rows


def evaluate_w_coverage_sensitivity(
    candidate_skills_list: List[List[str]],
    resume_texts: List[str],
    role_profile: Dict[str, Any],
    weights: List[float] = [0.50, 0.60, 0.70, 0.80, 0.90, 1.00],
) -> List[Dict[str, Any]]:
    """Analyze impact of W_COVERAGE balance on final match score."""
    rows: List[Dict[str, Any]] = []
    role_name = role_profile.get("role", "Backend Developer")
    role_emb = role_manager.get_role_embedding(role_name)

    for w_cov in weights:
        w_sem = round(1.0 - w_cov, 2)
        cfg = Settings(W_COVERAGE=w_cov, W_SEMANTIC=w_sem)
        final_scores: List[float] = []
        coverage_scores: List[float] = []
        semantic_scores: List[float] = []

        for c_skills, r_text in zip(candidate_skills_list, resume_texts):
            r_emb = taxonomy.model.encode([r_text], normalize_embeddings=True)[0]
            res = gap_analysis(
                resume_skills=c_skills,
                profile=role_profile,
                skill_emb=taxonomy,
                cfg=cfg,
                resume_text_emb=r_emb,
                role_text_emb=role_emb,
            )
            final_scores.append(res.final_score)
            coverage_scores.append(res.coverage_score)
            semantic_scores.append(res.semantic_score)

        rows.append({
            "w_coverage": w_cov,
            "w_semantic": w_sem,
            "avg_final_score": round(float(np.mean(final_scores)), 2),
            "avg_coverage": round(float(np.mean(coverage_scores)), 2),
            "avg_semantic": round(float(np.mean(semantic_scores)), 2),
        })

    return rows


def run_sensitivity_analysis() -> Dict[str, Any]:
    """Execute all sensitivity benchmarks across standard roles."""
    taxonomy.load()
    role_manager.load()

    target_role = "Backend Developer"
    prof = role_manager.get_role_profile(target_role)
    if not prof:
        raise ValueError(f"Profile for {target_role} not found.")

    # Load representative resumes for Backend Developer
    df = load_resumes()
    backend_resumes = df[df["category"].str.contains("Backend|Python", case=False, na=False)]
    if len(backend_resumes) == 0:
        backend_resumes = df.head(10)

    resume_texts = backend_resumes["resume_text"].tolist()
    skills_list = [extract_skills(t, mode="hybrid").skills for t in resume_texts]

    # 1. Partial Threshold Sensitivity
    partial_results = evaluate_partial_threshold_sensitivity(skills_list, prof)

    # 2. Min Skill Share Sensitivity
    share_results = evaluate_min_skill_share_sensitivity(skills_list, prof)

    # 3. W_COVERAGE Sensitivity
    weight_results = evaluate_w_coverage_sensitivity(skills_list, resume_texts, prof)

    print("\n" + "=" * 65)
    print("SENSITIVITY ANALYSIS: PARTIAL_THRESHOLD")
    print("=" * 65)
    print(f"{'PARTIAL_THRESHOLD':<20} | {'Avg Coverage Score':<20} | {'Avg Partial Matches'}")
    print("-" * 65)
    for r in partial_results:
        print(f"{r['partial_threshold']:<20.2f} | {r['avg_coverage_score']:<20.2f}% | {r['avg_partial_matches']:<15.2f}")
    print("=" * 65)

    print("\n" + "=" * 65)
    print("SENSITIVITY ANALYSIS: MIN_SKILL_SHARE")
    print("=" * 65)
    print(f"{'MIN_SKILL_SHARE':<20} | {'Skills in Profile':<20} | {'Avg Coverage Score'}")
    print("-" * 65)
    for r in share_results:
        print(f"{r['min_skill_share']:<20.2f} | {r['skills_in_profile']:<20} | {r['avg_coverage_score']:<18.2f}%")
    print("=" * 65)

    print("\n" + "=" * 70)
    print("SENSITIVITY ANALYSIS: W_COVERAGE vs W_SEMANTIC")
    print("=" * 70)
    print(f"{'W_COVERAGE':<12} | {'W_SEMANTIC':<12} | {'Final Score':<14} | {'Coverage':<12} | {'Semantic'}")
    print("-" * 70)
    for r in weight_results:
        print(f"{r['w_coverage']:<12.2f} | {r['w_semantic']:<12.2f} | {r['avg_final_score']:<14.2f}% | {r['avg_coverage']:<12.2f}% | {r['avg_semantic']:<10.2f}%")
    print("=" * 70)

    return {
        "partial_threshold": partial_results,
        "min_skill_share": share_results,
        "w_coverage": weight_results,
    }


if __name__ == "__main__":
    run_sensitivity_analysis()
