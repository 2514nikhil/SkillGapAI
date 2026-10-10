"""Matching evaluation benchmark for role ranking and scoring ablation.

Evaluates resume-to-role matching on held-out resumes against empirical role profiles.
Compares four scoring approaches:
  (a) TF-IDF cosine between resume and role text
  (b) Dense sentence embedding cosine only
  (c) Deterministic skill coverage only
  (d) Final blended score (skill coverage + calibrated semantic similarity)

Metrics reported:
  - Top-1 Accuracy
  - Recall@3
  - Mean Reciprocal Rank (MRR)
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.model_selection import train_test_split

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config import settings
from ml.data_io import load_resumes
from ml.extract import extract_skills
from ml.match import gap_analysis
from ml.profiles import role_manager
from ml.taxonomy import taxonomy

logger = logging.getLogger(__name__)

CATEGORY_MAP_FILE = BASE_DIR / "data" / "processed" / "category_role_map.json"


def load_category_role_map() -> Dict[str, str]:
    """Load category to role mapping from data/processed/category_role_map.json."""
    if not CATEGORY_MAP_FILE.is_file():
        raise FileNotFoundError(f"Category role map not found at {CATEGORY_MAP_FILE}")
    with open(CATEGORY_MAP_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def build_role_text_corpora(role_profiles: Dict[str, Any]) -> Dict[str, str]:
    """Construct reference text corpus per role from demanded skills and titles."""
    corpora: Dict[str, str] = {}
    for role_name, p_data in role_profiles.items():
        skills_text = " ".join([
            f"{s_meta.get('name', sid)} " * int(max(1, s_meta.get('weight', 1.0) * 10))
            for sid, s_meta in p_data.get("skills", {}).items()
        ])
        corpora[role_name] = f"{role_name} {role_name} {skills_text}"
    return corpora


def evaluate_ranking(
    ranks: List[int], total_items: int
) -> Dict[str, float]:
    """Compute Top-1 Accuracy, Recall@3, and MRR from rank positions (1-indexed)."""
    if not ranks:
        return {"top1_accuracy": 0.0, "recall_at_3": 0.0, "mrr": 0.0}

    top1 = sum(1 for r in ranks if r == 1) / total_items
    rec3 = sum(1 for r in ranks if r <= 3) / total_items
    mrr = sum(1.0 / r for r in ranks) / total_items

    return {
        "top1_accuracy": round(top1, 4),
        "recall_at_3": round(rec3, 4),
        "mrr": round(mrr, 4),
    }


def run_matching_evaluation(
    random_state: int = 42,
    test_size: float = 0.40,
) -> Dict[str, Any]:
    """Run matching ablation benchmark and return metric results."""
    # Ensure dependencies and profiles are loaded
    taxonomy.load()
    role_manager.load()
    category_map = load_category_role_map()

    # Load resumes dataset
    df_resumes = load_resumes()
    # Filter to resumes that have valid mapped canonical roles
    df_resumes["target_role"] = df_resumes["category"].map(category_map)
    df_valid = df_resumes[df_resumes["target_role"].notna()].copy()
    available_roles = role_manager.get_canonical_roles()
    df_valid = df_valid[df_valid["target_role"].isin(available_roles)].reset_index(drop=True)

    if len(df_valid) == 0:
        raise ValueError("No resumes with valid mapped canonical roles found.")

    # Train / Test split
    train_df, test_df = train_test_split(
        df_valid,
        test_size=test_size,
        random_state=random_state,
        stratify=df_valid["target_role"],
    )

    role_profiles = role_manager.profiles
    role_names = sorted(list(role_profiles.keys()))

    # Build role corpora for TF-IDF
    role_corpora = build_role_text_corpora(role_profiles)
    role_text_list = [role_corpora[r] for r in role_names]

    # Fit TF-IDF on role texts + train resume texts
    tfidf = TfidfVectorizer(stop_words="english", max_features=1500)
    all_train_texts = role_text_list + train_df["resume_text"].tolist()
    tfidf.fit(all_train_texts)
    role_tfidf = tfidf.transform(role_text_list)

    # Precompute role embeddings
    role_embeddings = [role_manager.get_role_embedding(r) for r in role_names]
    # Fallback encode if any role embedding missing
    for idx, r in enumerate(role_names):
        if role_embeddings[idx] is None:
            emb = taxonomy.model.encode([role_corpora[r]], normalize_embeddings=True)[0]
            role_embeddings[idx] = emb
    role_emb_matrix = np.array(role_embeddings)

    # Tune / verify W_COVERAGE & W_SEMANTIC on train split
    best_w_cov = 0.8
    best_train_mrr = 0.0
    for cand_w in [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]:
        train_ranks = []
        for _, row in train_df.iterrows():
            true_role = row["target_role"]
            text = row["resume_text"]
            cand_skills = extract_skills(text, mode="hybrid").skills
            text_emb = taxonomy.model.encode([text], normalize_embeddings=True)[0]

            scores = []
            for r_idx, r_name in enumerate(role_names):
                res = gap_analysis(
                    resume_skills=cand_skills,
                    profile=role_profiles[r_name],
                    skill_emb=taxonomy,
                    resume_text_emb=text_emb,
                    role_text_emb=role_emb_matrix[r_idx],
                )
                b_score = cand_w * res.coverage_score + (1.0 - cand_w) * res.semantic_score
                scores.append((r_name, b_score))
            scores.sort(key=lambda x: x[1], reverse=True)
            rank = [s[0] for s in scores].index(true_role) + 1
            train_ranks.append(rank)
        mrr = np.mean([1.0 / r for r in train_ranks])
        if mrr > best_train_mrr:
            best_train_mrr = mrr
            best_w_cov = cand_w

    # Evaluate on held-out test split
    ranks_tfidf: List[int] = []
    ranks_emb: List[int] = []
    ranks_cov: List[int] = []
    ranks_blended: List[int] = []

    test_total = len(test_df)

    for _, row in test_df.iterrows():
        true_role = row["target_role"]
        text = row["resume_text"]

        # 1. TF-IDF
        res_tfidf = tfidf.transform([text])
        sim_tfidf = cosine_similarity(res_tfidf, role_tfidf)[0]
        order_tfidf = [role_names[i] for i in np.argsort(-sim_tfidf)]
        ranks_tfidf.append(order_tfidf.index(true_role) + 1)

        # 2. Embedding Cosine
        text_emb = taxonomy.model.encode([text], normalize_embeddings=True)[0]
        sim_emb = np.dot(role_emb_matrix, text_emb)
        order_emb = [role_names[i] for i in np.argsort(-sim_emb)]
        ranks_emb.append(order_emb.index(true_role) + 1)

        # 3. Deterministic Skill Coverage only
        cand_skills = extract_skills(text, mode="hybrid").skills
        cov_scores = []
        for r_name in role_names:
            res = gap_analysis(
                resume_skills=cand_skills,
                profile=role_profiles[r_name],
                skill_emb=taxonomy,
            )
            cov_scores.append((r_name, res.coverage_score))
        cov_scores.sort(key=lambda x: x[1], reverse=True)
        order_cov = [s[0] for s in cov_scores]
        ranks_cov.append(order_cov.index(true_role) + 1)

        # 4. Final Blended Score (best_w_cov tuned on train)
        blended_scores = []
        for r_idx, r_name in enumerate(role_names):
            res = gap_analysis(
                resume_skills=cand_skills,
                profile=role_profiles[r_name],
                skill_emb=taxonomy,
                resume_text_emb=text_emb,
                role_text_emb=role_emb_matrix[r_idx],
            )
            b_score = (best_w_cov * res.coverage_score) + ((1.0 - best_w_cov) * res.semantic_score)
            blended_scores.append((r_name, b_score))
        blended_scores.sort(key=lambda x: x[1], reverse=True)
        order_blended = [s[0] for s in blended_scores]
        ranks_blended.append(order_blended.index(true_role) + 1)

    metrics_tfidf = evaluate_ranking(ranks_tfidf, test_total)
    metrics_emb = evaluate_ranking(ranks_emb, test_total)
    metrics_cov = evaluate_ranking(ranks_cov, test_total)
    metrics_blended = evaluate_ranking(ranks_blended, test_total)

    ablation_results = {
        "(a) TF-IDF Cosine": metrics_tfidf,
        "(b) Dense Embedding Cosine": metrics_emb,
        "(c) Skill Coverage Only": metrics_cov,
        "(d) Final Blended Score": metrics_blended,
    }

    # Print Ablation Table
    print("\n" + "=" * 80)
    print(f"ROLE MATCHING & RANKING ABLATION BENCHMARK (Test Set: {test_total} resumes)")
    print(f"Tuned Train Weight: W_COVERAGE = {best_w_cov:.2f}, W_SEMANTIC = {1.0 - best_w_cov:.2f}")
    print("=" * 80)
    print(f"{'Method':<32} | {'Top-1 Accuracy':<15} | {'Recall@3':<12} | {'MRR':<10}")
    print("-" * 80)
    for method_name, m in ablation_results.items():
        print(
            f"{method_name:<32} | "
            f"{m['top1_accuracy'] * 100:>13.2f}% | "
            f"{m['recall_at_3'] * 100:>10.2f}% | "
            f"{m['mrr']:>10.4f}"
        )
    print("=" * 80)

    return {
        "test_count": test_total,
        "train_count": len(train_df),
        "best_w_coverage": best_w_cov,
        "ablation_results": ablation_results,
    }


if __name__ == "__main__":
    run_matching_evaluation()
