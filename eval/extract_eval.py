"""Evaluation benchmark for skill extraction engine.

Computes micro-averaged Precision, Recall, F1 score, and processing latency for:
- Stage A: Baseline dictionary matching (spaCy PhraseMatcher)
- Stage B / Hybrid: Semantic fallback combined with dictionary matching
- Stage C / Hybrid+SLM: Extraction recovery using local SLM

Also performs:
- Per-document-type breakdown (resume vs job description)
- Per-category recall breakdown
- In-depth error analysis (Top 20 false positives and false negatives with context,
  grouped by root cause: ambiguous alias, missing from taxonomy, phrasing).
"""

from __future__ import annotations

import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

# Add parent directory to path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config import settings
from ml.extract import extract_skills
from ml.taxonomy import taxonomy

BENCHMARK_FILE = BASE_DIR / "eval" / "labeled" / "benchmark.json"


def classify_error_cause(skill_id: str, sentence: str, error_type: str = "FP") -> str:
    """Classify the root cause of an extraction error into canonical error groups."""
    skill_info = taxonomy.get_skill(skill_id)
    if not skill_info:
        return "missing from taxonomy"

    # Ambiguous names or aliases
    if skill_id in settings.AMBIGUOUS_SKILL_NAMES or len(skill_id) <= 3:
        return "ambiguous alias"

    # Phrasing / contextual complexity
    aliases = skill_info.get("aliases", [])
    if error_type == "FN" and len(aliases) <= 1:
        return "missing from taxonomy"

    return "phrasing"


def evaluate_dataset(
    docs: List[Dict[str, Any]], mode: str
) -> Tuple[Dict[str, Any], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Run extraction benchmark across a collection of annotated documents."""
    total_tp = 0
    total_fp = 0
    total_fn = 0

    fps: List[Dict[str, Any]] = []
    fns: List[Dict[str, Any]] = []

    # Category counters
    cat_tp = defaultdict(int)
    cat_total = defaultdict(int)

    start_time = time.perf_counter()

    for doc in docs:
        doc_id = doc["doc_id"]
        doc_type = doc.get("doc_type", "unknown")
        text = doc["text"]
        gt_skills: Set[str] = set(doc["ground_truth_skills"])

        res = extract_skills(text, mode=mode)
        pred_skills: Set[str] = set(res.skills)

        tp_set = pred_skills & gt_skills
        fp_set = pred_skills - gt_skills
        fn_set = gt_skills - pred_skills

        total_tp += len(tp_set)
        total_fp += len(fp_set)
        total_fn += len(fn_set)

        # Track per-category GT and TP
        for s in gt_skills:
            info = taxonomy.get_skill(s) or {}
            cat = info.get("category", "other")
            cat_total[cat] += 1
            if s in tp_set:
                cat_tp[cat] += 1

        for s in fp_set:
            sent = res.best_sentences.get(s, "(No sentence excerpt available)")
            cause = classify_error_cause(s, sent, error_type="FP")
            fps.append({
                "doc_id": doc_id,
                "doc_type": doc_type,
                "skill_id": s,
                "sentence": sent,
                "cause": cause,
            })

        for s in fn_set:
            info = taxonomy.get_skill(s) or {}
            cause = classify_error_cause(s, "", error_type="FN")
            fns.append({
                "doc_id": doc_id,
                "doc_type": doc_type,
                "skill_id": s,
                "cause": cause,
                "category": info.get("category", "other"),
            })

    elapsed = time.perf_counter() - start_time
    avg_sec = elapsed / len(docs) if docs else 0.0

    precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
    recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    # Compute category recall
    category_recall = {}
    for cat in sorted(cat_total.keys()):
        tot = cat_total[cat]
        c_tp = cat_tp[cat]
        category_recall[cat] = {
            "gt_count": tot,
            "tp_count": c_tp,
            "recall": (c_tp / tot) if tot > 0 else 0.0,
        }

    metrics = {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "avg_sec": avg_sec,
        "tp": total_tp,
        "fp": total_fp,
        "fn": total_fn,
        "total_gt": total_tp + total_fn,
        "category_recall": category_recall,
    }
    return metrics, fps, fns


def run_benchmark() -> Dict[str, Any]:
    """Execute complete extraction evaluation and print formatted report tables."""
    if not BENCHMARK_FILE.is_file():
        raise FileNotFoundError(f"Benchmark file not found at {BENCHMARK_FILE}")

    with open(BENCHMARK_FILE, "r", encoding="utf-8") as f:
        docs = json.load(f)

    # 1. Overall comparison across modes
    base_metrics, _, _ = evaluate_dataset(docs, mode="baseline")
    hyb_metrics, hyb_fps, hyb_fns = evaluate_dataset(docs, mode="hybrid")
    slm_metrics, _, _ = evaluate_dataset(docs, mode="hybrid+slm")

    # 2. Per-document-type evaluation (Hybrid mode)
    resume_docs = [d for d in docs if d.get("doc_type") == "resume"]
    jd_docs = [d for d in docs if d.get("doc_type") == "job_description"]

    res_metrics, _, _ = evaluate_dataset(resume_docs, mode="hybrid")
    jd_metrics, _, _ = evaluate_dataset(jd_docs, mode="hybrid")

    print("\n" + "=" * 105)
    print(f"SKILL EXTRACTION EVALUATION BENCHMARK ({len(docs)} documents)")
    print("=" * 105)

    print(f"{'Mode':<14} | {'Precision':<10} | {'Recall':<10} | {'F1 Score':<10} | {'Sec/Doc':<9} | {'TP':<5} | {'FP':<5} | {'FN':<5} | {'Total GT'}")
    print("-" * 105)

    for mode_name, m in [("baseline", base_metrics), ("hybrid", hyb_metrics), ("hybrid+slm", slm_metrics)]:
        print(
            f"{mode_name:<14} | "
            f"{m['precision'] * 100:>9.2f}% | "
            f"{m['recall'] * 100:>9.2f}% | "
            f"{m['f1'] * 100:>9.2f}% | "
            f"{m['avg_sec']:>7.3f}s | "
            f"{m['tp']:>5} | "
            f"{m['fp']:>5} | "
            f"{m['fn']:>5} | "
            f"{m['total_gt']:>8}"
        )
    print("=" * 105)

    # 3. Document Type Breakdown Table
    print("\n" + "=" * 80)
    print("PER-DOCUMENT-TYPE EVALUATION (Hybrid Mode)")
    print("=" * 80)
    print(f"{'Document Type':<18} | {'Docs':<6} | {'Precision':<10} | {'Recall':<10} | {'F1 Score':<10} | {'TP':<5} | {'FP':<5} | {'FN':<5}")
    print("-" * 80)
    for dtype, m, count in [("Resume", res_metrics, len(resume_docs)), ("Job Description", jd_metrics, len(jd_docs))]:
        print(
            f"{dtype:<18} | "
            f"{count:<6} | "
            f"{m['precision'] * 100:>9.2f}% | "
            f"{m['recall'] * 100:>9.2f}% | "
            f"{m['f1'] * 100:>9.2f}% | "
            f"{m['tp']:>5} | "
            f"{m['fp']:>5} | "
            f"{m['fn']:>5}"
        )
    print("=" * 80)

    # 4. Per-Category Recall Table
    print("\n" + "=" * 65)
    print("PER-CATEGORY RECALL BREAKDOWN (Hybrid Mode)")
    print("=" * 65)
    print(f"{'Category':<18} | {'GT Count':<10} | {'Detected':<10} | {'Recall':<10}")
    print("-" * 65)
    for cat, c_info in hyb_metrics["category_recall"].items():
        print(
            f"{cat:<18} | "
            f"{c_info['gt_count']:<10} | "
            f"{c_info['tp_count']:<10} | "
            f"{c_info['recall'] * 100:>9.2f}%"
        )
    print("=" * 65)

    # 5. Error Analysis: Top False Positives
    print("\n" + "=" * 110)
    print("ERROR ANALYSIS: TOP FALSE POSITIVES (Hybrid Mode)")
    print("=" * 110)
    print(f"{'Skill ID':<20} | {'Cause':<22} | {'Doc ID':<22} | {'Context Snippet'}")
    print("-" * 110)
    for fp in hyb_fps[:20]:
        ctx = fp["sentence"].replace("\n", " ").strip()
        if len(ctx) > 48:
            ctx = ctx[:45] + "..."
        print(f"{fp['skill_id']:<20} | {fp['cause']:<22} | {fp['doc_id']:<22} | {ctx}")
    if not hyb_fps:
        print("(No False Positives detected)")
    print("=" * 110)

    # 6. Error Analysis: False Negatives
    print("\n" + "=" * 75)
    print("ERROR ANALYSIS: TOP FALSE NEGATIVES (Hybrid Mode)")
    print("=" * 75)
    print(f"{'Skill ID':<24} | {'Cause':<24} | {'Category':<15} | {'Doc ID'}")
    print("-" * 75)
    for fn in hyb_fns[:20]:
        print(f"{fn['skill_id']:<24} | {fn['cause']:<24} | {fn['category']:<15} | {fn['doc_id']}")
    if not hyb_fns:
        print("(No False Negatives detected)")
    print("=" * 75)

    return {
        "modes": {
            "baseline": base_metrics,
            "hybrid": hyb_metrics,
            "hybrid+slm": slm_metrics,
        },
        "doc_types": {
            "resume": res_metrics,
            "job_description": jd_metrics,
        },
        "category_recall": hyb_metrics["category_recall"],
        "false_positives": hyb_fps,
        "false_negatives": hyb_fns,
    }


if __name__ == "__main__":
    run_benchmark()
