"""Build the clean canonical skills taxonomy and precompute embeddings.

Consolidates:
1. Hand-curated seed skills (data/raw/seed_skills.csv)
2. ESCO skills (data/raw/esco_skills.csv, filtered if present)
3. O*NET skills (data/raw/onet_skills.csv, if present)
4. Manual allowlist (data/raw/skill_allowlist.txt)

Applies strict normalization, alias deduplication, category assignment,
and marks ambiguous short/polysemous terms.
Precomputes and caches normalized embeddings using all-MiniLM-L6-v2.
"""

import csv
import json
import logging
import random
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np
from sentence_transformers import SentenceTransformer

# Add parent directory to path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config import settings
from ml.taxonomy import is_ambiguous_skill, is_valid_skill_term, normalize_skill_name

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Keywords to identify relevant ESCO skills if esco_skills.csv is provided
ESCO_RELEVANT_KEYWORDS = {
    "software",
    "programming",
    "develop",
    "code",
    "algorithm",
    "database",
    "sql",
    "data",
    "analytics",
    "machine learning",
    "artificial intelligence",
    "cloud",
    "network",
    "security",
    "web",
    "devops",
    "design",
    "user experience",
    "user interface",
    "agile",
    "scrum",
    "project management",
    "testing",
    "quality assurance",
    "troubleshoot",
    "sysadmin",
    "infrastructure",
    "business analysis",
    "communication",
    "leadership",
    "collaboration",
}

CATEGORY_HEURISTICS = [
    (
        "programming",
        [
            "programming",
            "language",
            "compiler",
            "syntax",
            "c++",
            "python",
            "java",
            "javascript",
            "typescript",
            "ruby",
            "php",
            "swift",
            "kotlin",
            "golang",
            "rust",
        ],
    ),
    (
        "ml",
        [
            "machine learning",
            "deep learning",
            "neural",
            "nlp",
            "computer vision",
            "pytorch",
            "tensorflow",
            "model",
            "hugging face",
            "ai",
            "reinforcement",
            "llm",
        ],
    ),
    (
        "data",
        [
            "database",
            "sql",
            "data warehouse",
            "etl",
            "pipeline",
            "spark",
            "hadoop",
            "analytics",
            "bi",
            "postgres",
            "mysql",
            "snowflake",
            "bigquery",
            "pandas",
            "databricks",
        ],
    ),
    (
        "web",
        [
            "react",
            "angular",
            "vue",
            "frontend",
            "backend",
            "api",
            "rest",
            "graphql",
            "html",
            "css",
            "web",
            "django",
            "flask",
            "fastapi",
            "node",
            "express",
        ],
    ),
    (
        "cloud",
        [
            "aws",
            "azure",
            "gcp",
            "cloud",
            "serverless",
            "s3",
            "ec2",
            "lambda",
            "gke",
            "eks",
        ],
    ),
    (
        "devops",
        [
            "docker",
            "kubernetes",
            "ci/cd",
            "jenkins",
            "terraform",
            "ansible",
            "linux",
            "monitoring",
            "prometheus",
            "grafana",
            "nginx",
            "git",
            "sre",
        ],
    ),
    (
        "design",
        [
            "design",
            "ui",
            "ux",
            "figma",
            "sketch",
            "photoshop",
            "wireframe",
            "prototype",
            "usability",
            "illustrator",
            "visual",
        ],
    ),
    (
        "business",
        [
            "agile",
            "scrum",
            "product management",
            "project management",
            "stakeholder",
            "strategy",
            "budget",
            "kpi",
            "crm",
            "business",
        ],
    ),
    (
        "soft skills",
        [
            "communication",
            "leadership",
            "teamwork",
            "problem solving",
            "adaptability",
            "collaboration",
            "critical thinking",
            "listening",
        ],
    ),
]


def infer_category(name: str) -> str:
    """Infer one of the 10 standard categories based on keywords."""
    norm = normalize_skill_name(name)
    for cat, kws in CATEGORY_HEURISTICS:
        for kw in kws:
            if kw in norm:
                return cat
    return "tools"


def load_allowlist() -> Set[str]:
    """Load manual allowlist terms."""
    if not settings.SKILL_ALLOWLIST_FILE.is_file():
        return set()
    terms = set()
    for line in settings.SKILL_ALLOWLIST_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            terms.add(normalize_skill_name(line))
    return terms


def build_taxonomy() -> Tuple[Dict[str, Dict[str, Any]], np.ndarray, List[str]]:
    """Generate, normalize, deduplicate taxonomy and compute embeddings."""
    logger.info("Starting taxonomy build process...")
    skills_by_id: Dict[str, Dict[str, Any]] = {}
    registered_names: Dict[str, str] = {}  # norm_name -> skill_id
    registered_aliases: Dict[str, str] = {}  # norm_alias -> skill_id
    allowlist = load_allowlist()

    def add_skill(name: str, aliases: List[str], category: str, source: str) -> None:
        if not is_valid_skill_term(name):
            return

        norm_name = normalize_skill_name(name)
        if not norm_name:
            return

        # Ensure valid category
        if category not in settings.SKILL_CATEGORIES:
            category = infer_category(name)

        # Generate slug skill_id
        skill_id = re.sub(r"[^a-z0-9+#.]+", "_", norm_name).strip("_")
        if not skill_id:
            return

        # Clean aliases
        valid_aliases: List[str] = []
        for a in aliases:
            if not a:
                continue
            norm_a = normalize_skill_name(a)
            if (
                norm_a
                and is_valid_skill_term(norm_a)
                and norm_a != norm_name
                and norm_a not in valid_aliases
            ):
                valid_aliases.append(norm_a)

        if norm_name in registered_names:
            # Merge with existing skill
            existing_id = registered_names[norm_name]
            existing_skill = skills_by_id[existing_id]
            for a in valid_aliases:
                if a not in existing_skill["aliases"]:
                    existing_skill["aliases"].append(a)
            return

        # Check if name is already an alias of another skill -> keep the primary
        if norm_name in registered_aliases:
            # Promote or retain
            pass

        ambiguous = is_ambiguous_skill(norm_name, valid_aliases)

        skills_by_id[skill_id] = {
            "name": name.strip(),
            "aliases": valid_aliases,
            "category": category,
            "ambiguous": ambiguous,
        }
        registered_names[norm_name] = skill_id

    # 1. Load Seed Skills (Highest Priority)
    if settings.SEED_SKILLS_FILE.is_file():
        logger.info("Loading seed skills from %s", settings.SEED_SKILLS_FILE)
        with open(settings.SEED_SKILLS_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = row.get("preferred_label", "").strip()
                raw_aliases = row.get("alt_labels", "")
                aliases = [a.strip() for a in raw_aliases.split(";") if a.strip()]
                cat = row.get("category", "tools").strip()
                add_skill(name, aliases, cat, "seed")
        logger.info("Loaded seed skills. Current total: %d", len(skills_by_id))
    else:
        logger.warning("Seed skills file not found at %s!", settings.SEED_SKILLS_FILE)

    # 2. Load ESCO Skills (if present)
    if settings.RAW_ESCO_SKILLS_FILE.is_file():
        logger.info("Found ESCO skills file at %s. Filtering and importing...", settings.RAW_ESCO_SKILLS_FILE)
        try:
            import pandas as pd
            df_esco = pd.read_csv(settings.RAW_ESCO_SKILLS_FILE, on_bad_lines="skip")
            # Map column names if needed
            pref_col = "preferredLabel" if "preferredLabel" in df_esco.columns else "preferred_label"
            alt_col = "altLabels" if "altLabels" in df_esco.columns else "alt_labels"

            imported_esco = 0
            if pref_col in df_esco.columns:
                for _, row in df_esco.iterrows():
                    name = str(row[pref_col]).strip() if pd.notna(row[pref_col]) else ""
                    if not name:
                        continue
                    norm = normalize_skill_name(name)

                    # Check if matches allowlist or relevant keywords
                    is_relevant = (
                        norm in allowlist
                        or any(kw in norm for kw in ESCO_RELEVANT_KEYWORDS)
                    )
                    if not is_relevant:
                        continue

                    raw_alt = str(row[alt_col]) if alt_col in row and pd.notna(row[alt_col]) else ""
                    aliases = [a.strip() for a in re.split(r"[;\n,]+", raw_alt) if a.strip()]
                    cat = infer_category(name)
                    add_skill(name, aliases, cat, "esco")
                    imported_esco += 1
            logger.info("Imported %d relevant ESCO skills. Total skills now: %d", imported_esco, len(skills_by_id))
        except Exception as exc:
            logger.warning("Could not parse ESCO skills: %s", exc)

    # 3. Deduplicate aliases across all skills
    logger.info("Resolving and deduplicating aliases across taxonomy...")
    claimed_aliases: Dict[str, str] = {}  # alias -> skill_id
    canonical_names_set = set(registered_names.keys())

    for skill_id, data in skills_by_id.items():
        clean_aliases: List[str] = []
        for alias in data["aliases"]:
            # If alias is identical to another skill's canonical name, drop as alias to avoid conflicts
            if alias in canonical_names_set:
                continue
            # If alias was already claimed by another skill, do not duplicate
            if alias in claimed_aliases:
                continue
            claimed_aliases[alias] = skill_id
            clean_aliases.append(alias)
        data["aliases"] = clean_aliases

    # 4. Save skills.json
    settings.SKILLS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(settings.SKILLS_FILE, "w", encoding="utf-8") as f:
        json.dump(skills_by_id, f, indent=2, ensure_ascii=False)
    logger.info("Saved %d canonical skills to %s", len(skills_by_id), settings.SKILLS_FILE)

    # 5. Precompute and cache embeddings
    logger.info("Loading embedding model '%s'...", settings.EMBEDDING_MODEL_NAME)
    model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)

    skill_ids_list = list(skills_by_id.keys())
    # Format descriptive text for richer embedding representation
    texts_to_embed = [
        f"{skills_by_id[sid]['name']} ({skills_by_id[sid]['category']})"
        for sid in skill_ids_list
    ]

    logger.info("Computing embeddings for %d skills...", len(texts_to_embed))
    embeddings = model.encode(texts_to_embed, normalize_embeddings=True, show_progress_bar=True)
    embeddings = np.asarray(embeddings, dtype=np.float32)

    # Save embeddings.npy and skill_ids.json
    np.save(settings.SKILL_EMBEDDINGS_FILE, embeddings)
    with open(settings.SKILL_IDS_FILE, "w", encoding="utf-8") as f:
        json.dump(skill_ids_list, f, indent=2)

    logger.info(
        "Embeddings saved to %s (shape: %s). IDs saved to %s.",
        settings.SKILL_EMBEDDINGS_FILE,
        embeddings.shape,
        settings.SKILL_IDS_FILE,
    )

    return skills_by_id, embeddings, skill_ids_list


def run_checks(skills: Dict[str, Dict[str, Any]], embeddings: np.ndarray, skill_ids: List[str]) -> None:
    """Print requested verification checks."""
    print("\n" + "=" * 80)
    print("PHASE 2 TAXONOMY VERIFICATION CHECKS")
    print("=" * 80)

    # Check 1: Counts per category
    print("\n1. Skill Counts by Category:")
    cat_counts: Dict[str, int] = {}
    for data in skills.values():
        c = data.get("category", "unknown")
        cat_counts[c] = cat_counts.get(c, 0) + 1

    for cat in sorted(cat_counts.keys()):
        print(f"   - {cat:<15}: {cat_counts[cat]:>4} skills")
    print(f"   TOTAL SKILLS   : {len(skills):>4}")

    # Check 2: 30 random entries
    print("\n2. Sample of 30 Random Skills (Inspection):")
    sample_ids = random.sample(list(skills.keys()), min(30, len(skills)))
    for sid in sample_ids:
        s = skills[sid]
        amb_tag = " [AMBIGUOUS]" if s.get("ambiguous") else ""
        alias_str = f" (aliases: {', '.join(s['aliases'])})" if s["aliases"] else ""
        print(f"   [{s['category']:<11}] {s['name']:<25}{alias_str}{amb_tag}")

    # Check 3: 20 nearest neighbors of "pytorch" and "sql"
    id_to_idx = {sid: idx for idx, sid in enumerate(skill_ids)}

    def show_neighbors(query_id: str, query_label: str) -> None:
        print(f"\n3. Top 20 Nearest Neighbors for '{query_label}':")
        if query_id not in id_to_idx:
            print(f"   [!] Skill ID '{query_id}' not found in taxonomy.")
            return

        query_vec = embeddings[id_to_idx[query_id]]
        scores = np.dot(embeddings, query_vec)
        top_indices = np.argsort(scores)[::-1][:21]  # top 21 (first is self)

        count = 0
        for idx in top_indices:
            sid = skill_ids[idx]
            if sid == query_id:
                continue
            count += 1
            s = skills[sid]
            print(f"   {count:>2}. {s['name']:<28} [{s['category']:<11}] similarity: {scores[idx]:.4f}")
            if count >= 20:
                break

    show_neighbors("pytorch", "PyTorch")
    show_neighbors("sql", "SQL")
    print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    skills, embeddings, skill_ids = build_taxonomy()
    run_checks(skills, embeddings, skill_ids)
