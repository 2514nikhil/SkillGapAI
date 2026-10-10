"""Data availability and validation checker for SkillGap.

Checks data/raw/ for required datasets, inspects columns against expected schema,
and prints a clear formatted summary with actionable download and configuration instructions.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd

# Add parent directory to path so config can be imported directly
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config import settings


DATASET_METADATA = {
    "esco_skills": {
        "filename": "esco_skills.csv",
        "optional": False,
        "dataset_name": "ESCO (European Skills, Competences, Qualifications and Occupations) Skills classification v1.2",
        "description": "European Commission skill taxonomy with preferred and alternative labels.",
        "canonical_required": ["preferred_label"],
        "canonical_optional": ["alt_labels", "skill_id", "skill_type"],
    },
    "onet_skills": {
        "filename": "onet_skills.csv",
        "optional": True,
        "dataset_name": "O*NET Skills Dataset",
        "description": "Occupational Information Network (O*NET) skills and work activities.",
        "canonical_required": ["preferred_label"],
        "canonical_optional": ["element_name", "description"],
    },
    "job_postings": {
        "filename": "job_postings.csv",
        "optional": False,
        "dataset_name": "LinkedIn / Indeed Job Postings (e.g., Kaggle: LinkedIn Job Postings Dataset)",
        "description": "Real-world job descriptions used to profile skill demand per role.",
        "canonical_required": ["title", "description"],
        "canonical_optional": ["company", "location"],
    },
    "resumes": {
        "filename": "resumes.csv",
        "optional": False,
        "dataset_name": "Resume Dataset (e.g., Kaggle: Updated Resume Dataset / Resume Dataset by Sneha Bilgi)",
        "description": "Candidate resumes labeled by job domain/category for benchmarking and testing.",
        "canonical_required": ["resume_text", "category"],
        "canonical_optional": [],
    },
    "courses": {
        "filename": "courses.csv",
        "optional": False,
        "dataset_name": "Coursera / Udemy Course Dataset (e.g., Kaggle: Coursera Courses Dataset)",
        "description": "Course catalog used to recommend targeted learning materials for missing skills.",
        "canonical_required": ["title", "description"],
        "canonical_optional": ["rating", "level", "duration", "url", "platform"],
    },
}


def check_dataset(key: str, meta: dict) -> dict:
    """Inspect status of a single dataset file in data/raw/."""
    file_path = settings.RAW_DATA_DIR / meta["filename"]
    exists = file_path.is_file()

    result = {
        "key": key,
        "filename": meta["filename"],
        "optional": meta["optional"],
        "exists": exists,
        "path": str(file_path),
        "found_columns": [],
        "mapped_columns": [],
        "missing_required": [],
        "status": "MISSING",
        "row_count": None,
    }

    if not exists:
        result["status"] = "OPTIONAL MISSING" if meta["optional"] else "MISSING"
        return result

    try:
        df_header = pd.read_csv(file_path, nrows=5)
        raw_cols = df_header.columns.tolist()
        result["found_columns"] = raw_cols

        # Map columns using settings.COLUMN_MAPPINGS
        mapping = settings.COLUMN_MAPPINGS.get(key, {})
        mapped = [mapping.get(c, c) for c in raw_cols]
        result["mapped_columns"] = mapped

        # Check required columns
        req = meta["canonical_required"]
        missing_req = [c for c in req if c not in mapped]
        result["missing_required"] = missing_req

        if missing_req:
            result["status"] = f"INVALID COLS (Missing: {', '.join(missing_req)})"
        else:
            result["status"] = "READY"

        # Count total rows safely
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            result["row_count"] = max(0, sum(1 for _ in f) - 1)

    except Exception as exc:
        result["status"] = f"ERROR ({exc})"

    return result


def print_report() -> bool:
    """Print ASCII report of raw datasets and return True if all required are present and valid."""
    results = [check_dataset(k, v) for k, v in DATASET_METADATA.items()]

    print("=" * 90)
    print("SKILLGAP DATA AVAILABILITY & VALIDATION REPORT")
    print(f"Target Directory: {settings.RAW_DATA_DIR}")
    print("=" * 90)

    # Header
    print(f"{'Dataset File':<20} | {'Type':<10} | {'Status':<24} | {'Rows':<8} | {'Found Columns'}")
    print("-" * 90)

    all_required_ready = True
    missing_items = []

    for r in results:
        file_type = "Optional" if r["optional"] else "Required"
        rows_str = str(r["row_count"]) if r["row_count"] is not None else "-"
        cols_summary = ", ".join(r["found_columns"][:4])
        if len(r["found_columns"]) > 4:
            cols_summary += f", ... (+{len(r['found_columns']) - 4} more)"
        if not cols_summary:
            cols_summary = "-"

        print(f"{r['filename']:<20} | {file_type:<10} | {r['status']:<24} | {rows_str:<8} | {cols_summary}")

        if not r["optional"] and r["status"] != "READY":
            all_required_ready = False
            missing_items.append(r)

    print("=" * 90)

    if missing_items:
        print("\nACTION REQUIRED: The following required datasets are missing or need column mapping:\n")
        for item in missing_items:
            meta = DATASET_METADATA[item["key"]]
            print(f"[*] {item['filename']} ({meta['dataset_name']})")
            print(f"    - Purpose: {meta['description']}")
            print(f"    - Place file at: {item['path']}")
            print(f"    - Required columns: {', '.join(meta['canonical_required'])}")
            print(f"    - Optional columns: {', '.join(meta['canonical_optional'])}")
            if item["found_columns"]:
                print(f"    - Currently detected columns: {', '.join(item['found_columns'])}")
                print(f"    - Missing required: {', '.join(item['missing_required'])}")
            print(
                f"    - Note: If your CSV has different column names, adjust 'COLUMN_MAPPINGS[\"{item['key']}\"]' in config.py."
            )
            print()
    else:
        print("\nAll required datasets are present and validated! Ready for processing.\n")

    return all_required_ready


if __name__ == "__main__":
    is_ready = print_report()
    sys.exit(0 if is_ready else 1)
