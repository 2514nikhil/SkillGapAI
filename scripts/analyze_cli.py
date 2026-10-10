"""CLI tool for SkillGap deterministic resume-to-role matching and explanation.

Usage:
    python scripts/analyze_cli.py <resume_path> --role "Data Analyst"
    python scripts/analyze_cli.py <resume_path> --jd <jd_path>
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import numpy as np
from sentence_transformers import SentenceTransformer

from config import settings
from ml.explain import (
    explain_contributions,
    get_skill_evidence,
    rank_gaps_by_impact,
)
from ml.extract import extract_skills
from ml.match import gap_analysis
from ml.parse import parse_resume
from ml.profiles import RoleProfileManager, profile_from_jd
from ml.taxonomy import taxonomy

logging.basicConfig(level=logging.WARNING, format="%(message)s")


def run_analysis(
    resume_path: Path,
    role_name: str | None = None,
    jd_path: Path | None = None,
    mode: str = "hybrid",
) -> None:
    """Analyze a resume against a target role profile or job description."""
    if not resume_path.is_file():
        print(f"Error: Resume file not found at '{resume_path}'", file=sys.stderr)
        sys.exit(1)

    # 1. Parse resume
    with open(resume_path, "rb") as f:
        file_bytes = f.read()

    print(f"\n================================================================================")
    print(f"SKILLGAP DETERMINISTIC MATCH & GAP ANALYSIS")
    print(f"================================================================================")
    print(f"Resume: {resume_path.name}")

    resume_text = parse_resume(file_bytes, resume_path.name)

    # 2. Extract skills
    taxonomy.load()
    extract_res = extract_skills(resume_text, mode=mode)
    print(f"Extracted {len(extract_res.skills)} verified skills: {', '.join(extract_res.skills[:10])}" + ("..." if len(extract_res.skills) > 10 else ""))

    # 3. Load or generate target profile
    pm = RoleProfileManager()
    target_profile = None
    role_text_emb = None

    if jd_path and jd_path.is_file():
        with open(jd_path, "r", encoding="utf-8") as f:
            jd_text = f.read()
        target_role = role_name or "Custom Job Description"
        target_profile = profile_from_jd(jd_text, role_title=target_role)
        print(f"Target: Job Description ({jd_path.name})")
    elif role_name:
        target_role = role_name
        raw_profile = pm.get_role_profile(role_name)
        if not raw_profile:
            print(f"Error: Role '{role_name}' not found in role profiles.", file=sys.stderr)
            print(f"Available roles: {', '.join(pm.get_canonical_roles())}", file=sys.stderr)
            sys.exit(1)
        target_profile = dict(raw_profile)
        target_profile["role"] = role_name
        role_text_emb = pm.get_role_embedding(role_name)
        print(f"Target Role: {role_name} (derived from {target_profile.get('n_postings', 0)} real postings)")
    else:
        print("Error: You must provide either --role <Role Name> or --jd <jd_file>", file=sys.stderr)
        sys.exit(1)

    # 4. Compute resume embedding for semantic similarity score
    model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
    resume_emb = model.encode(resume_text, normalize_embeddings=True)

    # 5. Run deterministic gap analysis
    gap_res = gap_analysis(
        resume_skills=extract_res.skills,
        profile=target_profile,
        skill_emb=taxonomy,
        resume_text_emb=resume_emb,
        role_text_emb=role_text_emb,
    )

    # 6. Run explainability & impact analysis
    contributions = explain_contributions(gap_res, target_profile)
    evidence_map = get_skill_evidence(gap_res.all_covered, extract_res.best_sentences)
    top_impacts = rank_gaps_by_impact(gap_res, target_profile, skill_emb=taxonomy)

    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    # 7. Print formatted explainable report
    print(f"\n--------------------------------------------------------------------------------")
    print(f"MATCH SCORE BREAKDOWN")
    print(f"--------------------------------------------------------------------------------")
    print(f"  FINAL MATCH SCORE        : {gap_res.final_score:.1f} / 100")
    print(f"  |-- Skill Coverage Score : {gap_res.coverage_score:.1f}% (Weight: {int(settings.W_COVERAGE * 100)}%)")
    print(f"  \\-- Semantic Alignment   : {gap_res.semantic_score:.1f}% (Weight: {int(settings.W_SEMANTIC * 100)}%)")
    print(f"  Total Demand Weight      : {gap_res.total_weight:.2f}")
    print(f"  Earned Skill Credit      : {gap_res.earned_weight:.2f}")

    print(f"\n--------------------------------------------------------------------------------")
    print(f"COVERED SKILLS ({len(gap_res.exact_matches)} Exact, {len(gap_res.partial_matches)} Partial)")
    print(f"--------------------------------------------------------------------------------")
    if not gap_res.all_covered:
        print("  (None found)")
    else:
        for cs in gap_res.exact_matches:
            evidence = evidence_map.get(cs.skill_id, "")
            evidence_snip = next((l.strip(" \t-*") for l in evidence.splitlines() if l.strip()), "")
            print(f"  [+] {cs.name:<24} [{cs.tier.upper():<6}] weight: {cs.weight:.2f} (Full credit: +{cs.earned_weight:.2f})")
            if evidence_snip:
                print(f"      Evidence: \"{evidence_snip[:90]}\"")

        for ps in gap_res.partial_matches:
            evidence = evidence_map.get(ps.skill_id, "")
            evidence_snip = next((l.strip(" \t-*") for l in evidence.splitlines() if l.strip()), "")
            print(f"  [~] {ps.name:<24} [{ps.tier.upper():<6}] weight: {ps.weight:.2f} (Partial credit: +{ps.earned_weight:.2f} via '{ps.covered_by_name}' [{int(ps.similarity*100)}% sim])")
            if evidence_snip:
                print(f"      Evidence: \"{evidence_snip[:90]}\"")

    print(f"\n--------------------------------------------------------------------------------")
    print(f"MISSING SKILLS ({len(gap_res.missing_skills)} Total)")
    print(f"--------------------------------------------------------------------------------")
    if not gap_res.missing_skills:
        print("  (None! All demanded skills covered.)")
    else:
        for ms in gap_res.missing_skills[:10]:
            info = taxonomy.get_skill(ms.skill_id) or {}
            share_pct = int(round(ms.weight * 100))
            print(f"  [-] {ms.name:<24} [{ms.tier.upper():<6}] Demand: {share_pct}% | Points lost: -{ms.potential_gain:.1f} pts")
            print(f"      Reason: {ms.name} appears in {share_pct}% of {gap_res.role} postings. You don't list it.")

    print(f"\n--------------------------------------------------------------------------------")
    print(f"TOP 5 SKILL ACQUISITION IMPACT GAINS (Priority Learning Order)")
    print(f"--------------------------------------------------------------------------------")
    if not top_impacts:
        print("  (No skill gaps to close.)")
    else:
        for i, imp in enumerate(top_impacts[:5], start=1):
            print(f"  {i}. {imp.skill_name:<22} [{imp.tier.upper():<6}] Score Gain: +{imp.score_gain:.1f} pts (Demand: {imp.demand_share_pct}%)")

    print(f"\n--------------------------------------------------------------------------------")
    print(f"CATEGORY COVERAGE BREAKDOWN")
    print(f"--------------------------------------------------------------------------------")
    for cat_name, cat in sorted(gap_res.categories.items(), key=lambda c: c[1].coverage_score, reverse=True):
        bar_len = int(cat.coverage_score / 5)
        bar = "#" * bar_len + "-" * (20 - bar_len)
        print(f"  {cat_name:<16} : [{bar}] {cat.coverage_score:>5.1f}% ({cat.covered_count}/{cat.skills_count} skills, earned {cat.earned_weight:.1f}/{cat.total_weight:.1f})")

    from ml.recommend import build_learning_path

    # 8. Learning Plan
    if gap_res.missing_skills:
        print(f"\n--------------------------------------------------------------------------------")
        print(f"GROUNDED LEARNING PLAN ({len(gap_res.missing_skills)} gaps to close)")
        print(f"--------------------------------------------------------------------------------")
        path = build_learning_path(gap_result=gap_res, profile=target_profile, hours_per_week=10)
        print(f"  Schedule: {path.total_weeks} weeks @ {path.hours_per_week} hrs/week ({path.total_duration_hours:.1f} total learning hours)")
        print(f"  Coverage Projection: {path.baseline_score:.1f}% -> {path.projected_final_score:.1f}%\n")

        for step in path.steps:
            c = step.course
            sb = c.score_breakdown
            print(f"  * {step.phase_label} | Focus: {step.primary_skill_name} (+{step.score_gain:.1f} pts -> {step.cumulative_score:.1f}%)")
            print(f"    Course: \"{c.title}\"")
            print(f"    Platform: {c.platform} | Level: {c.level} | Duration: {c.duration_hours:.0f} hrs | Rating: {c.rating:.1f}/5.0")
            if c.url:
                print(f"    Link: {c.url}")
            print(f"    Score Parts: relevance={sb['skill_relevance']:.2f}, exact_bonus={sb['exact_skill_bonus']:.2f}, rating={sb['rating_score']:.2f}, level_fit={sb['level_fit_score']:.2f}, dur_penalty={sb['duration_penalty']:.2f} => total={c.total_score:.3f}")
            print(f"    Why Chosen: {step.why_chosen}")
            print()

    print(f"================================================================================\n")


def main():
    parser = argparse.ArgumentParser(description="SkillGap: Deterministic Resume-to-Role Gap Analyzer")
    parser.add_argument("resume", type=Path, help="Path to resume file (.pdf, .docx, .txt)")
    parser.add_argument("--role", type=str, default=None, help="Target canonical role name (e.g. 'Data Analyst')")
    parser.add_argument("--jd", type=Path, default=None, help="Path to target job description text file")
    parser.add_argument("--mode", type=str, default="hybrid", choices=["baseline", "hybrid"], help="Extraction mode")
    parser.add_argument("--hours", type=int, default=10, help="Study hours per week (default 10)")

    args = parser.parse_args()
    run_analysis(resume_path=args.resume, role_name=args.role, jd_path=args.jd, mode=args.mode)


if __name__ == "__main__":
    main()
