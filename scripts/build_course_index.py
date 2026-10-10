"""Build processed course catalog, skill tags, and precomputed MiniLM embeddings.

Reads data/raw/courses.csv (or tests/fixtures/sample_courses.csv with --sample),
extracts canonical skill tags taught by each course, computes normalized
sentence embeddings for title + description, and saves:
- data/processed/courses.json
- data/processed/course_embeddings.npy

Usage:
    python scripts/build_course_index.py [--sample]
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

from config import settings
from ml.data_io import load_courses
from ml.extract import extract_skills
from ml.taxonomy import taxonomy

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def parse_duration_hours(val: Any) -> float:
    """Parse course duration string or number into hours float."""
    if pd.isna(val) or val is None:
        return 20.0
    if isinstance(val, (int, float)):
        return float(val) if val > 0 else 20.0
    val_str = str(val).lower()
    # Match patterns like '15 hours', '15 hrs', '15', '2 weeks'
    m_hrs = re.search(r"(\d+(?:\.\d+)?)\s*(?:hours?|hrs?|h)\b", val_str)
    if m_hrs:
        return float(m_hrs.group(1))
    m_weeks = re.search(r"(\d+(?:\.\d+)?)\s*(?:weeks?|wks?)\b", val_str)
    if m_weeks:
        return float(m_weeks.group(1)) * 10.0  # assume 10 hrs/week
    # Plain number
    m_num = re.search(r"^(\d+(?:\.\d+)?)$", val_str.strip())
    if m_num:
        return float(m_num.group(1))
    return 20.0


def parse_rating(val: Any) -> float:
    """Parse rating float safely, defaulting to 4.5."""
    try:
        r = float(val)
        return float(np.clip(r, 1.0, 5.0))
    except (ValueError, TypeError):
        return 4.5


def build_course_index(source_path: Path | None = None) -> None:
    """Process course dataset, extract skill tags, embed text, and persist index."""
    settings.ensure_directories()
    taxonomy.load()

    # Determine data source
    input_path = source_path or settings.RAW_COURSES_FILE
    if not input_path.is_file():
        raise FileNotFoundError(
            f"Required course dataset not found at '{input_path}'.\n"
            f"Please download a course catalog (e.g. Coursera or Udemy courses from Kaggle) "
            f"and place it at '{settings.RAW_COURSES_FILE}' with columns: title, description, rating, level, duration, url, platform.\n"
            f"Or run with '--sample' to test with the bundled fixtures dataset."
        )

    logger.info("Loading courses from %s...", input_path)
    df = load_courses(input_path)

    courses_list = []
    texts_to_embed = []

    logger.info("Extracting taught skills for %d courses...", len(df))
    for idx, row in df.iterrows():
        title = str(row.get("title", "")).strip()
        desc = str(row.get("description", "")).strip()
        rating = parse_rating(row.get("rating", 4.5))
        level = str(row.get("level", "All Levels")).strip().capitalize()
        duration = parse_duration_hours(row.get("duration", 20.0))
        url = str(row.get("url", "")).strip()
        platform = str(row.get("platform", "Online")).strip()

        combined_text = f"{title}. {desc}"
        texts_to_embed.append(combined_text)

        # Extract skills taught by course text
        ext = extract_skills(combined_text, mode="baseline")

        course_item = {
            "course_id": f"course_{idx}",
            "title": title,
            "description": desc,
            "rating": rating,
            "level": level,
            "duration": duration,
            "url": url,
            "platform": platform,
            "skills": ext.skills,
        }
        courses_list.append(course_item)

    # Compute sentence embeddings
    logger.info("Encoding course texts with SentenceTransformer (%s)...", settings.EMBEDDING_MODEL_NAME)
    model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
    embeddings = model.encode(texts_to_embed, normalize_embeddings=True, show_progress_bar=True)
    embeddings = np.array(embeddings, dtype=np.float32)

    # Save processed outputs
    logger.info("Saving processed courses to %s...", settings.COURSES_FILE)
    with open(settings.COURSES_FILE, "w", encoding="utf-8") as f:
        json.dump(courses_list, f, indent=2)

    logger.info("Saving course embeddings to %s (shape: %s)...", settings.COURSE_EMBEDDINGS_FILE, embeddings.shape)
    np.save(settings.COURSE_EMBEDDINGS_FILE, embeddings)

    logger.info("Successfully built course index with %d courses!", len(courses_list))


def main():
    parser = argparse.ArgumentParser(description="Build SkillGap course index and embeddings")
    parser.add_argument(
        "--sample",
        action="store_true",
        help="Build index using tests/fixtures/sample_courses.csv",
    )
    args = parser.parse_args()

    source = settings.FIXTURES_DIR / "sample_courses.csv" if args.sample else settings.RAW_COURSES_FILE
    build_course_index(source)


if __name__ == "__main__":
    main()
