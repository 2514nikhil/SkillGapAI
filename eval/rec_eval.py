"""Recommender evaluation benchmark and sample annotation generator.

Generates a sample of 30 missing skills with top-5 course recommendations for manual audit:
  python eval/rec_eval.py --generate

Computes Precision@1, Precision@3, Precision@5, and MAP@5 from the annotated CSV:
  python eval/rec_eval.py --eval
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config import settings
from ml.recommend import CourseCatalog, course_catalog, recommend_for_skill
from ml.taxonomy import taxonomy

EVAL_RESULTS_DIR = BASE_DIR / "eval" / "results"
EVAL_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
SAMPLE_CSV_FILE = EVAL_RESULTS_DIR / "rec_eval_samples.csv"

# 30 representative technical skills spanning the 6 canonical roles
BENCHMARK_SKILLS = [
    "docker",
    "kubernetes",
    "fastapi",
    "postgresql",
    "redis",
    "microservices",
    "ci_cd",
    "rest_api",
    "linux",
    "django",
    "amazon_web_services",
    "sql",
    "tableau",
    "power_bi",
    "snowflake",
    "a_b_testing",
    "data_analytics",
    "data_visualization",
    "pytorch",
    "tensorflow",
    "scikit_learn",
    "deep_learning",
    "machine_learning",
    "mlops",
    "mlflow",
    "computer_vision",
    "natural_language_processing",
    "react",
    "next.js",
    "typescript",
]


def heuristic_is_relevant(skill_id: str, course_info: Dict[str, Any]) -> int:
    """Heuristic proxy for relevance when manual annotations are not yet entered.

    A course is deemed relevant if:
    1. The skill_id is explicitly in course['taught_skills'], OR
    2. The skill_id or name appears in course['title'], OR
    3. The skill relevance cosine score is >= 0.50.
    """
    taught = course_info.get("taught_skills", [])
    if skill_id in taught:
        return 1

    skill_info = taxonomy.get_skill(skill_id) or {}
    skill_name = skill_info.get("name", skill_id).lower()
    title = course_info.get("title", "").lower()
    if skill_name in title or skill_id in title:
        return 1

    score_breakdown = course_info.get("score_breakdown", {})
    relevance_score = score_breakdown.get("skill_relevance", 0.0)
    if relevance_score >= 0.50:
        return 1

    return 0


def generate_samples(output_file: Optional[Path] = None, k: int = 5) -> Path:
    """Generate top-k recommendations for 30 skills and export to CSV."""
    taxonomy.load()
    course_catalog.load()

    dest = output_file or SAMPLE_CSV_FILE
    rows: List[Dict[str, Any]] = []

    for sid in BENCHMARK_SKILLS:
        s_info = taxonomy.get_skill(sid) or {}
        s_name = s_info.get("name", sid)

        recs = recommend_for_skill(skill_id=sid, level_pref="Beginner", k=k, catalog=course_catalog)

        for rank, course in enumerate(recs, start=1):
            h_rel = heuristic_is_relevant(sid, course.to_dict())
            rows.append({
                "skill_id": sid,
                "skill_name": s_name,
                "rank": rank,
                "course_id": course.course_id,
                "course_title": course.title,
                "platform": course.platform,
                "level": course.level,
                "duration_hours": course.duration_hours,
                "rating": course.rating,
                "total_score": round(course.total_score, 4),
                "why_chosen": course.why_chosen,
                "relevant (0/1)": "",
                "_heuristic_relevant": h_rel,
            })

    with open(dest, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "skill_id",
            "skill_name",
            "rank",
            "course_id",
            "course_title",
            "platform",
            "level",
            "duration_hours",
            "rating",
            "total_score",
            "why_chosen",
            "relevant (0/1)",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    print(f"Generated {len(rows)} recommendation samples across {len(BENCHMARK_SKILLS)} skills in: {dest}")
    return dest


def evaluate_samples(csv_file: Optional[Path] = None) -> Dict[str, float]:
    """Compute Precision@1, Precision@3, Precision@5, and MAP@5 from the CSV."""
    source_file = csv_file or SAMPLE_CSV_FILE
    if not source_file.is_file():
        raise FileNotFoundError(f"Sample file not found at {source_file}. Run --generate first.")

    skills_recs: Dict[str, List[int]] = {}

    with open(source_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sid = row["skill_id"]
            user_val = row.get("relevant (0/1)", "").strip()
            # If manually filled (0 or 1), use it; otherwise fallback to heuristic
            if user_val in ("0", "1"):
                is_rel = int(user_val)
            else:
                # Calculate heuristic fallback
                c_dict = {
                    "taught_skills": [s.strip() for s in row.get("taught_skills", "").split(";") if s.strip()],
                    "title": row.get("course_title", ""),
                    "score_breakdown": {"skill_relevance": float(row.get("total_score", 0.5))},
                }
                is_rel = heuristic_is_relevant(sid, c_dict)

            if sid not in skills_recs:
                skills_recs[sid] = []
            skills_recs[sid].append(is_rel)

    # Compute metrics
    p1_list: List[float] = []
    p3_list: List[float] = []
    p5_list: List[float] = []
    ap5_list: List[float] = []

    for sid, rels in skills_recs.items():
        k = len(rels)
        # Precision@1
        p1 = rels[0] if k >= 1 else 0
        p1_list.append(p1)

        # Precision@3
        p3 = sum(rels[:3]) / min(3, k) if k > 0 else 0
        p3_list.append(p3)

        # Precision@5
        p5 = sum(rels[:5]) / min(5, k) if k > 0 else 0
        p5_list.append(p5)

        # AP@5
        num_rel = 0
        cum_precision = 0.0
        for i, r in enumerate(rels[:5]):
            if r == 1:
                num_rel += 1
                cum_precision += num_rel / (i + 1)
        ap5 = (cum_precision / min(5, max(1, sum(rels[:5])))) if sum(rels[:5]) > 0 else 0.0
        ap5_list.append(ap5)

    metrics = {
        "num_skills": len(skills_recs),
        "precision_at_1": round(float(np.mean(p1_list)), 4),
        "precision_at_3": round(float(np.mean(p3_list)), 4),
        "precision_at_5": round(float(np.mean(p5_list)), 4),
        "map_at_5": round(float(np.mean(ap5_list)), 4),
    }

    print("\n" + "=" * 65)
    print(f"COURSE RECOMMENDER EVALUATION BENCHMARK ({metrics['num_skills']} Skills)")
    print("=" * 65)
    print(f"Precision@1 : {metrics['precision_at_1'] * 100:>6.2f}%")
    print(f"Precision@3 : {metrics['precision_at_3'] * 100:>6.2f}%")
    print(f"Precision@5 : {metrics['precision_at_5'] * 100:>6.2f}%")
    print(f"MAP@5       : {metrics['map_at_5']:>6.4f}")
    print("=" * 65)

    return metrics


def main():
    parser = argparse.ArgumentParser(description="Recommender evaluation benchmark")
    parser.add_argument("--generate", action="store_true", help="Generate sample CSV with 30 skills")
    parser.add_argument("--eval", action="store_true", help="Compute metrics from sample CSV")
    args = parser.parse_args()

    if args.eval:
        evaluate_samples()
    else:
        generate_samples()
        evaluate_samples()


if __name__ == "__main__":
    main()
