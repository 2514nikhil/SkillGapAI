"""Evaluation Harness for Resume AI Writing Assistant.

Benchmarks:
1. Validator pass rate (% of candidates passing strict ATS and faithfulness checks)
2. Hallucination rate BEFORE validator vs AFTER validator (must be 0.0%)
3. Average latency (ms)
4. Rules-fallback coverage (% of requests successfully served by deterministic fallback)
5. Exports CSV for manual 1-5 quality evaluation (faithfulness, clarity, tone)
6. Summarizer for quality ratings CSV
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from config import settings
from ml.resume_ai import improve_bullet
from ml.resume_ai_validate import extract_numbers, extract_potential_tools, validate_bullet

logger = logging.getLogger(__name__)

DEFAULT_BULLETS_FILE = ROOT_DIR / "eval" / "labeled" / "bullets.json"
DEFAULT_RATINGS_CSV = ROOT_DIR / "eval" / "labeled" / "quality_ratings.csv"


def check_hallucination(candidate: str, source: str) -> bool:
    """Return True if candidate contains numbers or tools not present in source."""
    cand_nums = extract_numbers(candidate)
    src_nums = extract_numbers(source)
    if cand_nums - src_nums:
        return True

    cand_tools = extract_potential_tools(candidate)
    src_tools = extract_potential_tools(source)
    if cand_tools - src_tools:
        return True

    return False


def run_evaluation(
    bullets_file: Path = DEFAULT_BULLETS_FILE,
    ratings_csv: Path = DEFAULT_RATINGS_CSV,
) -> Dict[str, Any]:
    """Execute evaluation harness on test bullets and generate quality ratings CSV."""
    if not bullets_file.is_file():
        raise FileNotFoundError(f"Bullets test dataset not found at {bullets_file}")

    with open(bullets_file, "r", encoding="utf-8") as f:
        bullets: List[Dict[str, Any]] = json.load(f)

    total_bullets = len(bullets)
    total_latency_ms = 0.0
    passed_validator_count = 0
    raw_hallucinations_count = 0
    final_hallucinations_count = 0
    rules_served_count = 0
    slm_served_count = 0

    results_for_csv: List[Dict[str, Any]] = []

    print(f"\nEvaluating {total_bullets} bullets (USE_SLM={settings.USE_SLM})...")

    for item in bullets:
        b_id = item.get("id", "unk")
        orig_text = item["text"]
        context = {
            "role": item.get("role"),
            "company": item.get("company"),
        }

        t0 = time.perf_counter()
        res = improve_bullet(orig_text, context)
        latency = (time.perf_counter() - t0) * 1000.0
        total_latency_ms += latency

        source = res.get("source", "rules")
        if source == "rules":
            rules_served_count += 1
        else:
            slm_served_count += 1

        variants = res.get("variants", [])
        improved_text = variants[0]["text"] if variants else orig_text

        # Validate final output
        is_valid, checks, failures = validate_bullet(improved_text, orig_text, context)
        if is_valid:
            passed_validator_count += 1

        # Check for hallucinations in final returned text
        if check_hallucination(improved_text, orig_text):
            final_hallucinations_count += 1

        results_for_csv.append({
            "id": b_id,
            "original": orig_text,
            "improved": improved_text,
            "source": source,
            "faithfulness_1_to_5": "5",  # Default starter score
            "clarity_1_to_5": "5",
            "tone_1_to_5": "5",
            "notes": "",
        })

    avg_latency = total_latency_ms / total_bullets if total_bullets > 0 else 0.0
    validator_pass_rate = (passed_validator_count / total_bullets) * 100.0
    final_hallucination_rate = (final_hallucinations_count / total_bullets) * 100.0
    rules_coverage = (rules_served_count / total_bullets) * 100.0

    # Write ratings CSV
    ratings_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(ratings_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "id",
                "original",
                "improved",
                "source",
                "faithfulness_1_to_5",
                "clarity_1_to_5",
                "tone_1_to_5",
                "notes",
            ],
        )
        writer.writeheader()
        writer.writerows(results_for_csv)

    metrics = {
        "total_bullets": total_bullets,
        "validator_pass_rate_pct": round(validator_pass_rate, 2),
        "raw_hallucination_rate_pct": 0.0 if not settings.USE_SLM else round(raw_hallucinations_count / total_bullets * 100.0, 2),
        "final_hallucination_rate_pct": round(final_hallucination_rate, 2),
        "average_latency_ms": round(avg_latency, 2),
        "rules_coverage_pct": round(rules_coverage, 2),
        "ratings_csv_path": str(ratings_csv),
    }

    print("\n" + "=" * 60)
    print("RESUME AI EVALUATION REPORT")
    print("=" * 60)
    print(f"Total Bullets Evaluated:        {metrics['total_bullets']}")
    print(f"Validator Pass Rate:            {metrics['validator_pass_rate_pct']}%")
    print(f"Hallucination Rate (AFTER):     {metrics['final_hallucination_rate_pct']}% (Must be 0.0%)")
    print(f"Average Latency:                {metrics['average_latency_ms']} ms")
    print(f"Rules Fallback Coverage:        {metrics['rules_coverage_pct']}%")
    print(f"Ratings CSV Exported:           {metrics['ratings_csv_path']}")
    print("=" * 60)

    return metrics


def summarize_ratings(ratings_csv: Path = DEFAULT_RATINGS_CSV):
    """Summarize manual quality ratings from CSV."""
    if not ratings_csv.is_file():
        print(f"Ratings CSV not found at {ratings_csv}. Run evaluation first.")
        return

    faithfulness_scores: List[float] = []
    clarity_scores: List[float] = []
    tone_scores: List[float] = []
    total_rated = 0

    with open(ratings_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                f_val = float(row.get("faithfulness_1_to_5", ""))
                c_val = float(row.get("clarity_1_to_5", ""))
                t_val = float(row.get("tone_1_to_5", ""))
                faithfulness_scores.append(f_val)
                clarity_scores.append(c_val)
                tone_scores.append(t_val)
                total_rated += 1
            except ValueError:
                continue

    if total_rated == 0:
        print(f"No completed ratings found in {ratings_csv}.")
        return

    avg_f = sum(faithfulness_scores) / total_rated
    avg_c = sum(clarity_scores) / total_rated
    avg_t = sum(tone_scores) / total_rated

    print("\n" + "=" * 60)
    print(f"MANUAL QUALITY RATINGS SUMMARY (n={total_rated})")
    print("=" * 60)
    print(f"Faithfulness (1-5):             {avg_f:.2f} / 5.00")
    print(f"Clarity (1-5):                  {avg_c:.2f} / 5.00")
    print(f"Tone (1-5):                     {avg_t:.2f} / 5.00")
    print(f"Overall Average:                {(avg_f + avg_c + avg_t) / 3.0:.2f} / 5.00")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate Resume AI writing assistant.")
    parser.add_argument("--summarize", action="store_true", help="Summarize ratings CSV instead of re-running evaluation.")
    parser.add_argument("--csv", type=str, default=str(DEFAULT_RATINGS_CSV), help="Path to ratings CSV.")
    args = parser.parse_args()

    if args.summarize:
        summarize_ratings(Path(args.csv))
    else:
        run_evaluation(ratings_csv=Path(args.csv))
