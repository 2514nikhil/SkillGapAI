"""Build empirical skill-demand profiles per canonical role from job postings.

Extracts skills across postings, computes empirical frequencies and tiers
(core, common, bonus), computes role description embeddings, and saves
data/processed/role_profiles.json and data/processed/role_embeddings.npy.
"""

import argparse
import json
import logging
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

# Add parent directory to path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config import settings
from ml.data_io import DatasetNotFoundError, load_job_postings
from ml.extract import extract_skills
from ml.profiles import assign_tier, load_role_rules, normalize_job_title
from ml.taxonomy import taxonomy

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def compute_role_centroids(
    model: SentenceTransformer, rules: Dict[str, List[str]]
) -> Dict[str, np.ndarray]:
    """Compute title embedding centroids for each canonical role from rule keywords."""
    centroids: Dict[str, np.ndarray] = {}
    for role_name, patterns in rules.items():
        if not patterns:
            continue
        embs = model.encode(patterns, normalize_embeddings=True)
        centroid = np.mean(embs, axis=0)
        centroid = centroid / np.linalg.norm(centroid)
        centroids[role_name] = centroid
    return centroids


def build_profiles(input_csv: Optional[Path] = None) -> Tuple[Dict[str, Any], Dict[str, np.ndarray]]:
    target_csv = input_csv or settings.RAW_JOB_POSTINGS_FILE
    if not target_csv.is_file():
        raise DatasetNotFoundError(
            f"Job postings dataset not found at {target_csv}.\n"
            f"Please place your job postings CSV at data/raw/job_postings.csv (at least: 'title', 'description' columns).\n"
            f"Or run with '--sample' to verify against tests/fixtures/sample_postings.csv."
        )

    logger.info("Loading job postings from %s...", target_csv)
    df = load_job_postings(target_csv)
    logger.info("Loaded %d postings.", len(df))

    # Load rules and model
    rules = load_role_rules()
    taxonomy.load()
    logger.info("Loading SentenceTransformer model '%s'...", settings.EMBEDDING_MODEL_NAME)
    model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
    role_centroids = compute_role_centroids(model, rules)

    # 1. Normalize Titles
    logger.info("Normalizing job titles...")
    assigned_roles: List[Optional[str]] = []
    seniorities: List[Optional[str]] = []

    for title in df["title"]:
        role, sen = normalize_job_title(str(title), rules=rules, model=model, role_centroids=role_centroids)
        assigned_roles.append(role)
        seniorities.append(sen)

    df["assigned_role"] = assigned_roles
    df["seniority"] = seniorities

    matched_df = df[df["assigned_role"].notna()].copy()
    unassigned_count = len(df) - len(matched_df)
    logger.info(
        "Assigned %d postings to canonical roles (%d unassigned).",
        len(matched_df),
        unassigned_count,
    )

    # 2. Extract Skills per Posting
    logger.info("Extracting skills for postings (mode=baseline for speed)...")
    posting_skills: List[List[str]] = []
    for desc in matched_df["description"]:
        res = extract_skills(str(desc), mode="baseline")
        posting_skills.append(res.skills)

    matched_df["skills"] = posting_skills

    # Cache posting skills to parquet
    cache_cols = [c for c in ["title", "assigned_role", "seniority", "company"] if c in matched_df.columns]
    cache_df = matched_df[cache_cols].copy()
    cache_df["skills"] = ["; ".join(s) for s in posting_skills]
    settings.POSTING_SKILLS_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    cache_df.to_parquet(settings.POSTING_SKILLS_CACHE_FILE, index=False)
    logger.info("Cached posting skills to %s", settings.POSTING_SKILLS_CACHE_FILE)

    # 3. Compute empirical skill shares and tiers per role
    role_profiles: Dict[str, Any] = {}
    role_embeddings: Dict[str, np.ndarray] = {}

    grouped = matched_df.groupby("assigned_role")

    for role_name, group in grouped:
        n_postings = len(group)
        if n_postings < settings.MIN_POSTINGS_PER_ROLE:
            logger.warning(
                "Dropping role '%s': only %d postings (< MIN_POSTINGS_PER_ROLE=%d)",
                role_name,
                n_postings,
                settings.MIN_POSTINGS_PER_ROLE,
            )
            continue

        skill_counter: Counter = Counter()
        for s_list in group["skills"]:
            skill_counter.update(s_list)

        role_skills: Dict[str, Dict[str, Any]] = {}
        for sid, count in skill_counter.items():
            weight = count / n_postings
            if weight < settings.MIN_SKILL_SHARE:
                continue
            tier = assign_tier(weight)
            role_skills[sid] = {
                "weight": round(weight, 3),
                "count": count,
                "tier": tier,
            }

        # Sort skills by weight descending
        sorted_skills = dict(sorted(role_skills.items(), key=lambda item: item[1]["weight"], reverse=True))

        # Compute role description mean embedding
        desc_list = group["description"].tolist()
        # Sample up to 50 descriptions for memory/speed efficiency
        sampled_descs = desc_list[:50]
        desc_embs = model.encode(sampled_descs, normalize_embeddings=True)
        mean_emb = np.mean(desc_embs, axis=0)
        mean_emb = mean_emb / np.linalg.norm(mean_emb)
        role_embeddings[role_name] = mean_emb

        role_profiles[role_name] = {
            "n_postings": n_postings,
            "skills": sorted_skills,
            "embedding_path": str(settings.ROLE_EMBEDDINGS_FILE),
        }

    # 4. Save role_profiles.json & role_embeddings.npy
    settings.ROLE_PROFILES_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(settings.ROLE_PROFILES_FILE, "w", encoding="utf-8") as f:
        json.dump(role_profiles, f, indent=2, ensure_ascii=False)
    logger.info("Saved %d role profiles to %s", len(role_profiles), settings.ROLE_PROFILES_FILE)

    np.save(settings.ROLE_EMBEDDINGS_FILE, role_embeddings, allow_pickle=True)
    logger.info("Saved role text embeddings to %s", settings.ROLE_EMBEDDINGS_FILE)

    return role_profiles, role_embeddings


def print_checks(profiles: Dict[str, Any]) -> None:
    print("\n" + "=" * 80)
    print("PHASE 4 ROLE PROFILES VERIFICATION CHECKS")
    print("=" * 80)

    print("\n1. Postings per Role:")
    for role, data in sorted(profiles.items()):
        print(f"   - {role:<24}: {data['n_postings']:>4} postings")

    # Pick 5 roles to show top 10 skills
    sample_roles = [
        "Data Analyst",
        "ML Engineer",
        "Backend Developer",
        "Frontend Developer",
        "DevOps Engineer",
    ]
    available_roles = [r for r in sample_roles if r in profiles]
    if not available_roles:
        available_roles = list(profiles.keys())[:5]

    print("\n2. Top 10 Skills (Weights & Tiers) for Key Roles:")
    for role in available_roles:
        data = profiles[role]
        print(f"\n   [*] {role} ({data['n_postings']} postings):")
        skills = data["skills"]
        top_10 = list(skills.items())[:10]
        for sid, sdata in top_10:
            info = taxonomy.get_skill(sid)
            name = info["name"] if info else sid
            print(
                f"       - {name:<22} (id: {sid:<18}) share: {sdata['weight'] * 100:>5.1f}% [{sdata['tier'].upper()}]"
            )

    print("\n" + "=" * 80 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Build role profiles from job postings.")
    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="Path to job postings CSV file.",
    )
    parser.add_argument(
        "--sample",
        action="store_true",
        help="Use tests/fixtures/sample_postings.csv for demonstration/testing.",
    )
    args = parser.parse_args()

    input_path = None
    if args.sample:
        input_path = settings.FIXTURES_DIR / "sample_postings.csv"
    elif args.input:
        input_path = Path(args.input)
    elif settings.RAW_JOB_POSTINGS_FILE.is_file():
        input_path = settings.RAW_JOB_POSTINGS_FILE
    else:
        # Fallback to sample fixture with notice
        sample_path = settings.FIXTURES_DIR / "sample_postings.csv"
        if sample_path.is_file():
            print(f"Notice: '{settings.RAW_JOB_POSTINGS_FILE}' not found. Defaulting to sample fixture at '{sample_path}'.")
            input_path = sample_path
        else:
            print(f"Error: {settings.RAW_JOB_POSTINGS_FILE} not found. Place your CSV at data/raw/job_postings.csv.")
            sys.exit(1)

    profiles, embeddings = build_profiles(input_path)
    print_checks(profiles)


if __name__ == "__main__":
    main()
